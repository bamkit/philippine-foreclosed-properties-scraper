import sys
import os
# Add the parent directory to sys.path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re
import json
import asyncio
from typing import Dict, List, Any
from pathlib import Path
from bs4 import BeautifulSoup

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy, JsonCssExtractionStrategy

try:
    from ..utils.base_scraper import BaseBankScraper
    from ..utils.config import BANKS
except ImportError:
    from utils.base_scraper import BaseBankScraper
    from utils.config import BANKS


class BPIScraper(BaseBankScraper):
    """Scraper for BPI foreclosed properties through their Buena Mano system."""
    
    def __init__(self, *args, **kwargs):
        """Initialize the BPI scraper."""
        bank_name = "BPI"
        bank_url = "https://www.buenamano.ph/search/result"  # Updated URL
        super().__init__(bank_name=bank_name, bank_url=bank_url, *args, **kwargs)
        
        # Override browser config to be more stealthy
        self.browser_config = BrowserConfig(
            headless=True,
            viewport_width=1920,
            viewport_height=1080,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            verbose=True,
            # Add stealth settings
            extra_args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor"
            ]
        )
        
        # BPI's foreclosed properties are available through both online sealed bidding 
        # and negotiated sale basis (first come, first served)
        self.has_bidding = True
        self.is_negotiated_sale = True
    
    async def _extract_property_list(self, crawler: AsyncWebCrawler) -> List[Dict[str, Any]]:
        """Extract the list of properties from the BPI/Buena Mano search results page.
        
        Args:
            crawler: The web crawler instance
            
        Returns:
            A list of dictionaries containing property URLs
        """
        print(f"Extracting property links from: {self.bank_url}")
        
        # Try multiple times with delays to bypass Cloudflare protection
        for attempt in range(3):
            try:
                print(f"Attempt {attempt + 1}/3")
                
                # Add delay between attempts
                if attempt > 0:
                    await asyncio.sleep(5)
                
                # Get the search results page
                result = await crawler.arun(url=self.bank_url)
                
                if not result.html:
                    print("No HTML content received from the search results page")
                    continue
                
                # Check if we got a Cloudflare protection page
                if "Whoops, looks like something went wrong" in result.html or "Cloudflare" in result.html:
                    print("Detected Cloudflare protection page, retrying...")
                    continue
                
                # Parse the HTML to find all h4 elements with property links
                soup = BeautifulSoup(result.html, 'html.parser')
                property_links = []
                
                # Find all h4 elements that contain property links
                h4_elements = soup.find_all('h4')
                
                for h4 in h4_elements:
                    link = h4.find('a')
                    if link and 'href' in link.attrs:
                        href = link['href']
                        title = link.get_text(strip=True)
                        
                        # Only include property detail links
                        if '/property/' in href:
                            property_links.append({
                                'title': title,
                                'detail_url': href
                            })
                
                print(f"Found {len(property_links)} property links")
                
                if property_links:
                    return property_links
                else:
                    print("No property links found, retrying...")
                    
            except Exception as e:
                print(f"Error extracting property links (attempt {attempt + 1}): {e}")
                continue
        
        print("Failed to extract property links after 3 attempts")
        return []
    
    async def _extract_property_details(self, crawler: AsyncWebCrawler, detail_url: str) -> Dict[str, Any]:
        """Extract detailed information for a specific property.
        
        Args:
            crawler: The web crawler instance
            detail_url: The URL of the property detail page
            
        Returns:
            A dictionary containing detailed property information
        """
        print(f"Extracting details from: {detail_url}")
        
        try:
            # Get the property detail page
            result = await crawler.arun(url=detail_url)
            
            if not result.html:
                print(f"No HTML content received from: {detail_url}")
                return {}
            
            # Parse the HTML to extract property details
            soup = BeautifulSoup(result.html, 'html.parser')
            
            # Extract data from property-summary div
            property_summary = soup.find('div', class_='property-summary')
            property_data = {
                'url': detail_url,
                'location': 'NA',
                'address': 'NA',
                'lot_area_sqm': 'NA',
                'floor_area_sqm': 'NA',
                'price_php': 'NA',
                'storeys': 'NA',
                'bedrooms': 'NA',
                'bathrooms': 'NA',
                'usage_classification': 'NA',
                'property_classification': 'NA',
                'special_concerns': 'NA',
                'sales_advisor': 'NA',
                'contact_no': 'NA',
                'alternate': 'NA',
                'alternate_no': 'NA'
            }
            
            if property_summary:
                # Extract title
                h3 = property_summary.find('h3')
                if h3:
                    property_data['title'] = h3.get_text(strip=True)
                
                # Extract location and address
                p_elements = property_summary.find_all('p')
                for p in p_elements:
                    text = p.get_text(strip=True)
                    
                    if 'Location :' in text:
                        location = text.replace('Location :', '').strip()
                        property_data['location'] = location
                    
                    elif 'Address:' in text:
                        # Address might be in the next p element
                        continue
                    
                    elif 'Lot Area (sqm) :' in text:
                        lot_area = text.replace('Lot Area (sqm) :', '').strip()
                        property_data['lot_area_sqm'] = lot_area
                    
                    elif 'Floor Area (sqm) :' in text:
                        floor_area = text.replace('Floor Area (sqm) :', '').strip()
                        property_data['floor_area_sqm'] = floor_area
                    
                    elif 'Price (Php) :' in text:
                        price = text.replace('Price (Php) :', '').strip()
                        property_data['price_php'] = price
                    
                    elif 'Storeys :' in text:
                        storeys = text.replace('Storeys :', '').strip()
                        property_data['storeys'] = storeys
                    
                    elif 'Bedrooms :' in text:
                        bedrooms = text.replace('Bedrooms :', '').strip()
                        property_data['bedrooms'] = bedrooms
                    
                    elif 'Bathrooms :' in text:
                        bathrooms = text.replace('Bathrooms :', '').strip()
                        property_data['bathrooms'] = bathrooms
                    
                    elif 'Usage Classification :' in text:
                        usage = text.replace('Usage Classification :', '').strip()
                        property_data['usage_classification'] = usage
                
                # Extract address (it's usually in a separate p element)
                address_p = property_summary.find('p', string=lambda text: text and 'Lot' in text and 'Block' in text)
                if address_p:
                    property_data['address'] = address_p.get_text(strip=True)
            
            # Extract data from property-location-content div
            property_location = soup.find('div', class_='property-location-content')
            if property_location:
                p_elements = property_location.find_all('p')
                for p in p_elements:
                    text = p.get_text(strip=True)
                    
                    if 'Property Classification:' in text:
                        classification = text.replace('Property Classification:', '').strip()
                        property_data['property_classification'] = classification
                    
                    elif 'Special Concerns:' in text:
                        # Special concerns might be in the next elements
                        continue
                    
                    elif 'Sales Advisor :' in text:
                        advisor = text.replace('Sales Advisor :', '').strip()
                        property_data['sales_advisor'] = advisor
                    
                    elif 'Contact No. :' in text:
                        contact = text.replace('Contact No. :', '').strip()
                        property_data['contact_no'] = contact
                    
                    elif 'Alternate :' in text:
                        alternate = text.replace('Alternate :', '').strip()
                        property_data['alternate'] = alternate
                    
                    elif "Alternate's No. :" in text:
                        alternate_no = text.replace("Alternate's No. :", '').strip()
                        property_data['alternate_no'] = alternate_no
                
                # Extract special concerns (it might be in a list or separate text)
                special_concerns = property_location.find('p', string=lambda text: text and 'Special Concerns:' in text)
                if special_concerns:
                    # Get the next sibling elements for special concerns
                    next_elem = special_concerns.find_next_sibling()
                    if next_elem:
                        concerns_text = next_elem.get_text(strip=True)
                        if concerns_text and concerns_text != '-':
                            property_data['special_concerns'] = concerns_text
            
            return property_data
            
        except Exception as e:
            print(f"Error extracting property details from {detail_url}: {e}")
            return {
                'url': detail_url,
                'error': f"Failed to extract details: {str(e)}"
            }
    
    def _normalize_data(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """Return property data as-is without normalization.
        
        Args:
            property_data: The property data to normalize
            
        Returns:
            Property data with original structure
        """
        # Return the data as-is, preserving original structure
        return property_data
    
    async def scrape(self) -> List[Dict[str, Any]]:
        """Scrape foreclosed properties from BPI/Buena Mano.
        
        Returns:
            A list of dictionaries containing property information
        """
        print("BPI/Buena Mano foreclosed properties are available in two ways:")
        print("1. Online Sealed Bidding - Properties are sold through competitive bidding")
        print("2. Negotiated Sale - Properties are sold on a 'first come, first served' basis")
        print("")
        print("Property classifications:")
        print("- Green Tag: Properties with cleared titles and tax declarations under the bank's name")
        print("- Yellow Tag: Properties with special concerns (e.g., titles in transfer process, occupied)")
        print("- Red Tag: Properties with pending court cases or legal issues")
        
        try:
            properties = await super().scrape()
            
            # Verify that we have actual data in the properties
            valid_properties = []
            for prop in properties:
                if isinstance(prop, dict) and prop.get('url') and prop.get('url') != 'NA':
                    valid_properties.append(prop)
            
            if valid_properties:
                print(f"Successfully extracted {len(valid_properties)} properties from BPI/Buena Mano")
                return valid_properties
            
            # If we have no valid properties, return empty list
            print("Warning: No valid properties found.")
            return []
            
        except Exception as e:
            print(f"Error during BPI/Buena Mano scraping: {e}")
            return [] 