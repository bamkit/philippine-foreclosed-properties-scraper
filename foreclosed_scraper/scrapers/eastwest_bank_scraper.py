import sys
import os
# Add the parent directory to sys.path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re
import json
import asyncio
import logging
from typing import Dict, List, Any
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig

try:
    from ..utils.base_scraper import BaseBankScraper
    from ..utils.config import BANKS, OUTPUT_PATH
except ImportError:
    from utils.base_scraper import BaseBankScraper
    from utils.config import BANKS, OUTPUT_PATH

class EastwestBankScraper(BaseBankScraper):
    """Scraper for Eastwest Bank foreclosed properties."""
    
    def __init__(self, *args, **kwargs):
        """Initialize the Eastwest Bank scraper.
        
        Args:
            max_results: Maximum number of results to extract
        """
        # Hardcode max_results to None for Eastwest Bank to always save all properties
        kwargs['max_results'] = None  # Ignore config/environment for this bank
        super().__init__(
            bank_name="Eastwest Bank",
            bank_url=BANKS['eastwest_bank']['url'],
            *args, **kwargs
        )
        self.bank_name = "Eastwest Bank"
        self.url = BANKS['eastwest_bank']['url']
        self.max_results = None  # Explicitly override any inherited value
    
    async def _extract_property_list(self, crawler: AsyncWebCrawler) -> List[Dict[str, Any]]:
        """
        Extracts the list of properties from the Eastwest Bank website, handling pagination.
        """
        logging.info(f"Starting property list extraction for {self.bank_name}")
        properties = []
        page = 1
        while True:
            page_url = self.url
            if page > 1:
                page_url = f"{self.url}?page={page}"
            run_config = CrawlerRunConfig(
                url=page_url,
                wait_for="css:.content_card"
            )
            result = await crawler.arun(url=page_url, config=run_config)
            if not result.html:
                break
            soup = BeautifulSoup(result.html, 'html.parser')
            property_cards = soup.select(".content_card")
            if not property_cards:
                break
            for card in property_cards:
                prop = {}
                prop['property_name'] = card.select_one(".content_card-title").text.strip() if card.select_one(".content_card-title") else "NA"
                details = card.select(".content_card-info-text")
                if len(details) >= 6:
                    prop['property_no'] = details[0].text.strip()
                    prop['type'] = details[1].text.strip()
                    prop['lot_area'] = details[2].text.strip()
                    prop['floor_area'] = details[3].text.strip()
                    prop['location'] = details[4].text.strip()
                    prop['city'] = details[5].text.strip()
                price_tag = card.select_one(".content_card-price")
                prop['price'] = price_tag.text.replace("PhP", "").replace(",", "").strip() if price_tag else "NA"
                link_tag = card.select_one("a")
                if link_tag and link_tag.has_attr('href'):
                    prop['url'] = urljoin(self.url, link_tag['href'])
                else:
                    prop['url'] = self.url
                properties.append(prop)
            page += 1
        return properties

    async def scrape(self) -> List[Dict[str, Any]]:
        """
        Main scraping method for Eastwest Bank.
        
        Returns:
            A list of dictionaries, where each dictionary represents a foreclosed property.
        """
        logging.info(f"Starting scrape for {self.bank_name}")
        try:
            # Use a vanilla crawler instance since we are handling the parsing
            async with AsyncWebCrawler() as crawler:
                properties = await self._extract_property_list(crawler)
                # Always save all properties, do not use base class logic
                logging.info(f"Successfully scraped {len(properties)} properties from {self.bank_name}.")
                output_path = OUTPUT_PATH / f"{self.bank_name.lower().replace(' ', '_')}.json"
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(properties, f, ensure_ascii=False, indent=2)
                print(f"Saved {len(properties)} properties to {output_path}")

                return properties
        except Exception as e:
            logging.error(f"An error occurred while scraping {self.bank_name}: {e}")
            return [] 