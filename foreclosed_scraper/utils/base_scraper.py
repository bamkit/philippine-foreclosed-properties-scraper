import os
import json
import asyncio
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Any, Optional

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy, JsonCssExtractionStrategy
from crawl4ai.types import create_llm_config

from .config import OPENAI_API_KEY, MAX_RESULTS_PER_BANK, OUTPUT_PATH, USER_AGENT


class BaseBankScraper(ABC):
    """Base class for bank scrapers.
    
    This class provides common functionality for scraping foreclosed properties
    from bank websites. Subclasses should implement the specific extraction
    logic for each bank.
    """
    
    def __init__(self, bank_name: str, bank_url: str, max_results: int = MAX_RESULTS_PER_BANK):
        """Initialize the scraper.
        
        Args:
            bank_name: The name of the bank
            bank_url: The URL of the bank's foreclosed properties page
            max_results: Maximum number of results to extract
        """
        self.bank_name = bank_name
        self.bank_url = bank_url
        self.max_results = max_results
        self.output_path = OUTPUT_PATH / f"{bank_name.lower().replace(' ', '_')}.json"
        
        # Configure browser settings
        self.browser_config = BrowserConfig(
            headless=True,
            viewport_width=1366,
            viewport_height=768,
            user_agent=USER_AGENT,
            verbose=True
        )
        
        # Configure LLM for extraction if needed
        try:
            self.llm_config = create_llm_config(
                provider="openai",
                api_token=OPENAI_API_KEY
            )
        except Exception as e:
            print(f"Warning: Could not create LLM config: {e}")
            self.llm_config = None
    
    async def scrape(self) -> List[Dict[str, Any]]:
        """Scrape foreclosed properties from the bank website.
        
        Returns:
            A list of dictionaries containing property information
        """
        async with AsyncWebCrawler(config=self.browser_config) as crawler:
            # First we need to get the list of properties
            properties = await self._extract_property_list(crawler)
            
            # Limit the number of properties
            properties = properties[:self.max_results]
            
            # Extract detailed information for each property
            detailed_properties = []
            for property_data in properties:
                # If the property has a detail URL, fetch additional information
                if "detail_url" in property_data:
                    detailed_info = await self._extract_property_details(
                        crawler, property_data["detail_url"]
                    )
                    property_data.update(detailed_info)
                
                # Normalize the data to ensure consistent format
                normalized_data = self._normalize_data(property_data)
                detailed_properties.append(normalized_data)
            
            # Save the results to a JSON file
            self._save_results(detailed_properties)
            
            return detailed_properties
    
    @abstractmethod
    async def _extract_property_list(self, crawler: AsyncWebCrawler) -> List[Dict[str, Any]]:
        """Extract the list of properties from the main page.
        
        This method should be implemented by subclasses to extract the list of
        properties from the bank's foreclosed properties page.
        
        Args:
            crawler: The web crawler instance
            
        Returns:
            A list of dictionaries containing basic property information
        """
        pass
    
    async def _extract_property_details(self, crawler: AsyncWebCrawler, detail_url: str) -> Dict[str, Any]:
        """Extract detailed information for a specific property.
        
        Args:
            crawler: The web crawler instance
            detail_url: The URL of the property detail page
            
        Returns:
            A dictionary containing detailed property information
        """
        # Default implementation using LLM extraction
        # Subclasses may override this method with a more specific implementation
        
        run_config = CrawlerRunConfig(
            extraction_strategy=LLMExtractionStrategy(
                llm_config=self.llm_config,
                instruction="""
                Extract the following information about the property:
                - Title or property name
                - Classification (Agricultural, Commercial, Residential, etc.)
                - Area in square meters (if available)
                - Floor area for condominiums (if available)
                - Location details including address
                - Province
                - Price or selling price
                - Any comments, notes, or additional information
                - URL for property photos (if available)
                
                Format the response as a JSON object with these fields:
                {
                    "title": string,
                    "classification": string,
                    "area": string or number,
                    "floor_area": string or number,
                    "location": string,
                    "province": string,
                    "price": string or number,
                    "comments": string,
                    "photo_url": string
                }
                
                If any field is not available, use "NA" as the value.
                """
            )
        )
        
        result = await crawler.arun(url=detail_url, config=run_config)
        
        # Extract the JSON data from the response
        if result.extracted_content and len(result.extracted_content) > 0:
            return result.extracted_content[0]
        
        return {}
    
    def _normalize_data(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize the property data to ensure consistent format.
        
        Args:
            property_data: The property data to normalize
            
        Returns:
            Normalized property data
        """
        # Define the expected fields
        expected_fields = [
            "title", "classification", "area", "floor_area", 
            "location", "province", "price", "comments", "photo_url"
        ]
        
        # Create a normalized dictionary with default "NA" values
        normalized = {field: "NA" for field in expected_fields}
        
        # Update with available data
        for key, value in property_data.items():
            normalized_key = key.lower().replace(" ", "_")
            if normalized_key in normalized and value:
                normalized[normalized_key] = value
        
        return normalized
    
    def _save_results(self, properties: List[Dict[str, Any]]) -> None:
        """Save the results to a JSON file.
        
        Args:
            properties: List of property dictionaries to save
        """
        with open(self.output_path, "w", encoding="utf-8") as f:
            json.dump(properties, f, ensure_ascii=False, indent=2)
        
        print(f"Saved {len(properties)} properties to {self.output_path}")


class CssSelectorScraper(BaseBankScraper):
    """A scraper that uses CSS selectors for extraction."""
    
    def __init__(self, bank_name: str, bank_url: str, 
                 list_schema: Dict[str, Any], 
                 detail_schema: Optional[Dict[str, Any]] = None,
                 max_results: int = MAX_RESULTS_PER_BANK):
        """Initialize the CSS selector scraper.
        
        Args:
            bank_name: The name of the bank
            bank_url: The URL of the bank's foreclosed properties page
            list_schema: CSS schema for extracting the property list
            detail_schema: CSS schema for extracting property details
            max_results: Maximum number of results to extract
        """
        super().__init__(bank_name, bank_url, max_results)
        self.list_schema = list_schema
        self.detail_schema = detail_schema
    
    async def _extract_property_list(self, crawler: AsyncWebCrawler) -> List[Dict[str, Any]]:
        """Extract the list of properties using CSS selectors.
        
        Args:
            crawler: The web crawler instance
            
        Returns:
            A list of dictionaries containing basic property information
        """
        run_config = CrawlerRunConfig(
            extraction_strategy=JsonCssExtractionStrategy(self.list_schema)
        )
        
        result = await crawler.arun(url=self.bank_url, config=run_config)
        
        if result.extracted_content:
            return result.extracted_content
        
        return []
    
    async def _extract_property_details(self, crawler: AsyncWebCrawler, detail_url: str) -> Dict[str, Any]:
        """Extract property details using CSS selectors if schema is available.
        
        Args:
            crawler: The web crawler instance
            detail_url: The URL of the property detail page
            
        Returns:
            A dictionary containing detailed property information
        """
        if self.detail_schema:
            run_config = CrawlerRunConfig(
                extraction_strategy=JsonCssExtractionStrategy(self.detail_schema)
            )
            
            result = await crawler.arun(url=detail_url, config=run_config)
            
            if result.extracted_content and len(result.extracted_content) > 0:
                return result.extracted_content[0]
            
            return {}
        
        # Fall back to LLM extraction if no schema is provided
        return await super()._extract_property_details(crawler, detail_url) 