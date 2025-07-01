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
        Based on the actual page structure at https://pre-owned-properties.eastwestbanker.com/
        """
        logging.info(f"Starting property list extraction for {self.bank_name}")
        properties = []
        page = 1
        max_pages = 21  # Based on the page showing "1 / 21"
        
        while page <= max_pages:
            logging.info(f"Scraping page {page} of {max_pages}")
            
            # Construct page URL
            page_url = self.url
            if page > 1:
                page_url = f"{self.url}?b74fbe7d_page={page}"
            
            run_config = CrawlerRunConfig(
                url=page_url,
                wait_for="text:Property No."  # Wait for property information to load
            )
            
            try:
                result = await crawler.arun(url=page_url, config=run_config)
                if not result.html:
                    logging.warning(f"No HTML content received for page {page}")
                    break
                
                soup = BeautifulSoup(result.html, 'html.parser')
                
                # Based on the actual page structure, properties are listed in a specific format
                # Look for property blocks that contain "Property No." text
                property_blocks = self._find_property_blocks(soup)
                
                if not property_blocks:
                    logging.warning(f"No property blocks found on page {page}")
                    break
                
                logging.info(f"Found {len(property_blocks)} properties on page {page}")
                
                for block in property_blocks:
                    try:
                        prop = self._extract_property_from_block(block)
                        if prop:
                            # Initialize address field
                            prop['address'] = "NA"
                            properties.append(prop)
                    except Exception as e:
                        logging.error(f"Error extracting property from block: {e}")
                        continue
                    
            except Exception as e:
                logging.error(f"Error scraping page {page}: {e}")
                break
            
            page += 1
            
            # Add a small delay between requests
            await asyncio.sleep(1)
        
        logging.info(f"Total properties extracted: {len(properties)}")
        return properties
    
    def _find_property_blocks(self, soup: BeautifulSoup) -> List:
        """
        Find property blocks in the HTML based on the actual page structure.
        Based on the debug output, properties are structured with content_card-info-block divs.
        """
        # Based on the HTML structure provided, each property is in a container
        # that has a content_card-title div and a call-to-actions div
        
        property_blocks = []
        
        # Method 1: Look for containers that have both content_card-title and call-to-actions
        # This is the most reliable way to identify individual property blocks
        for container in soup.find_all(['div', 'section', 'article']):
            has_title = container.find('div', class_='content_card-title') is not None
            has_call_to_actions = container.find('div', class_='call-to-actions') is not None
            has_info_blocks = len(container.find_all('div', class_='content_card-info-block')) >= 3
            
            if has_title and has_call_to_actions and has_info_blocks:
                property_blocks.append(container)
        
        # Method 2: If no blocks found with Method 1, try to find by content_card-title
        if not property_blocks:
            title_elements = soup.find_all('div', class_='content_card-title')
            for title_elem in title_elements:
                # Find the parent container that contains this title
                parent = title_elem.parent
                while parent and parent.name != 'body':
                    # Check if this parent has the required elements
                    if (parent.find('div', class_='call-to-actions') and 
                        len(parent.find_all('div', class_='content_card-info-block')) >= 3):
                        property_blocks.append(parent)
                        break
                    parent = parent.parent
        
        # Method 3: If still no blocks found, try to find by call-to-actions
        if not property_blocks:
            call_to_actions_elements = soup.find_all('div', class_='call-to-actions')
            for call_elem in call_to_actions_elements:
                # Find the parent container that contains this call-to-actions
                parent = call_elem.parent
                while parent and parent.name != 'body':
                    # Check if this parent has the required elements
                    if (parent.find('div', class_='content_card-title') and 
                        len(parent.find_all('div', class_='content_card-info-block')) >= 3):
                        property_blocks.append(parent)
                        break
                    parent = parent.parent
        
        return property_blocks
    
    def _get_block_identifier(self, block) -> str:
        """
        Create a unique identifier for a property block to avoid duplicates.
        Uses the property title and URL as the unique identifier.
        """
        title_elem = block.find('div', class_='content_card-title')
        title = title_elem.get_text(strip=True) if title_elem else ""
        
        call_to_actions = block.find('div', class_='call-to-actions')
        url = ""
        if call_to_actions:
            link_elem = call_to_actions.find('a')
            if link_elem and link_elem.has_attr('href'):
                url = link_elem['href']
        
        return f"{title}|{url}"
    
    def _remove_duplicates(self, properties: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate properties based on property_no and URL.
        Keeps the first occurrence of each unique property.
        """
        seen = set()
        unique_properties = []
        
        for prop in properties:
            # Create a unique key based on property_no and URL
            prop_no = prop.get('property_no', '')
            url = prop.get('url', '')
            key = f"{prop_no}|{url}"
            
            if key not in seen:
                unique_properties.append(prop)
                seen.add(key)
        
        return unique_properties
    
    def _extract_property_from_block(self, block) -> Dict[str, Any]:
        """
        Extract property information from a single property block.
        Based on the actual page structure with content_card-info-block divs.
        """
        prop = {}
        
        try:
            # Find all info blocks within this container
            info_blocks = block.find_all('div', class_='content_card-info-block')
            
            if not info_blocks:
                return None
            
            # Extract property name from content_card-title div
            # Format: "D-356-00562 Residential Townhouse in Las Pinas"
            title_elem = block.find('div', class_='content_card-title')
            if title_elem:
                title_text = title_elem.get_text(strip=True)
                prop['property_name'] = title_text
            else:
                prop['property_name'] = "NA"
            
            # Extract information from each info block
            for info_block in info_blocks:
                label_elem = info_block.find('div', class_='content_card-info-label')
                text_elem = info_block.find('div', class_='content_card-info-text')
                
                if label_elem and text_elem:
                    label = label_elem.get_text(strip=True)
                    value = text_elem.get_text(strip=True)
                    
                    if label == "Property No.":
                        prop['property_no'] = value
                    elif label == "Type":
                        prop['type'] = value
                    elif label == "Lot Area":
                        prop['lot_area'] = value
                    elif label == "Floor Area":
                        prop['floor_area'] = value
                    elif label == "Location":
                        prop['location'] = value
                    elif label == "City":
                        prop['city'] = value
            
            # If property_no is not found in info blocks, extract from title
            if 'property_no' not in prop or not prop['property_no']:
                if title_text:
                    parts = title_text.split(' ', 1)
                    if len(parts) > 0:
                        prop['property_no'] = parts[0]
                else:
                    prop['property_no'] = "NA"
            
            # Extract price from the call-to-actions div
            # Look for content_card-price div within call-to-actions
            call_to_actions = block.find('div', class_='call-to-actions')
            if call_to_actions:
                price_elem = call_to_actions.find('div', class_='content_card-price')
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    # Clean price text - remove "PhP" and commas, keep only numbers and decimal points
                    price_clean = re.sub(r'[^\d,\.]', '', price_text)
                    if price_clean:
                        prop['price'] = price_clean
                    else:
                        prop['price'] = "NA"
                else:
                    prop['price'] = "NA"
            else:
                prop['price'] = "NA"
            
            # Extract URL from the link in call-to-actions
            if call_to_actions:
                link_elem = call_to_actions.find('a')
                if link_elem and link_elem.has_attr('href'):
                    prop['url'] = urljoin(self.url, link_elem['href'])
                else:
                    prop['url'] = self.url
            else:
                prop['url'] = self.url
            
            # Set default values for missing fields
            if 'property_no' not in prop:
                prop['property_no'] = "NA"
            if 'type' not in prop:
                prop['type'] = "NA"
            if 'lot_area' not in prop:
                prop['lot_area'] = "NA"
            if 'floor_area' not in prop:
                prop['floor_area'] = "NA"
            if 'location' not in prop:
                prop['location'] = "NA"
            if 'city' not in prop:
                prop['city'] = "NA"
            
            return prop
            
        except Exception as e:
            logging.error(f"Error extracting property data: {e}")
            return None

    async def _extract_addresses_in_batches(self, crawler: AsyncWebCrawler, properties: List[Dict[str, Any]], batch_size: int = 10) -> List[Dict[str, Any]]:
        """
        Extract addresses from individual property pages in batches to avoid timeouts.
        """
        logging.info(f"Starting batch address extraction for {len(properties)} properties")
        
        for i in range(0, len(properties), batch_size):
            batch = properties[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(properties) + batch_size - 1) // batch_size
            
            logging.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} properties)")
            
            for prop in batch:
                try:
                    if not prop.get('url') or prop['url'] == self.url:
                        continue
                    
                    logging.info(f"Extracting address from: {prop['url']}")
                    
                    run_config = CrawlerRunConfig(
                        url=prop['url'],
                        wait_for="css:div.content_card-info-label"  # Wait for property details to load
                    )
                    
                    result = await crawler.arun(url=prop['url'], config=run_config)
                    if result.html:
                        soup = BeautifulSoup(result.html, 'html.parser')
                        
                        # Look for address in the detailed property page
                        address_elem = soup.find('div', class_='content_card-info-label', string='Address')
                        if address_elem:
                            address_text_elem = address_elem.find_next_sibling('div', class_='content_card-info-text')
                            if address_text_elem:
                                prop['address'] = address_text_elem.get_text(strip=True)
                                logging.info(f"Found address: {prop['address']}")
                    
                    # Add a small delay between requests
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logging.error(f"Error extracting address for {prop.get('url', 'unknown')}: {e}")
                    continue
            
            # Add delay between batches
            if i + batch_size < len(properties):
                logging.info(f"Waiting between batches...")
                await asyncio.sleep(2)
        
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
                # Step 1: Extract all properties from listing pages
                logging.info("Step 1: Extracting properties from listing pages...")
                properties = await self._extract_property_list(crawler)
                
                if not properties:
                    logging.warning("No properties found")
                    return []
                
                # Step 2: Extract addresses in batches
                logging.info("Step 2: Extracting addresses in batches...")
                properties_with_addresses = await self._extract_addresses_in_batches(crawler, properties, batch_size=10)
                
                # Step 3: Remove duplicates based on property_no and URL
                logging.info("Step 3: Removing duplicates...")
                unique_properties = self._remove_duplicates(properties_with_addresses)
                
                logging.info(f"Successfully scraped {len(unique_properties)} unique properties from {self.bank_name} (removed {len(properties_with_addresses) - len(unique_properties)} duplicates).")
                
                # Save to file
                output_path = OUTPUT_PATH / f"{self.bank_name.lower().replace(' ', '_')}.json"
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(unique_properties, f, ensure_ascii=False, indent=2)
                
                print(f"Saved {len(unique_properties)} unique properties to {output_path}")
                return unique_properties
                
        except Exception as e:
            logging.error(f"An error occurred while scraping {self.bank_name}: {e}")
            return [] 