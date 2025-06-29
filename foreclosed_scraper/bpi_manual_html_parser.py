#!/usr/bin/env python3
"""
BPI Manual HTML Parser
Extracts property data from manually downloaded HTML files from BPI/Buena Mano website.
This bypasses Cloudflare protection by using HTML files saved manually by the user.
"""

import os
import json
import re
from pathlib import Path
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional

class BPIManualHTMLParser:
    """Parser for manually downloaded BPI/Buena Mano HTML files."""
    
    def __init__(self, html_directory: str = "foreclosed_scraper/bpi_manual_html"):
        """
        Initialize the parser.
        
        Args:
            html_directory: Directory containing manually downloaded HTML files
        """
        self.html_directory = Path(html_directory)
        self.html_directory.mkdir(parents=True, exist_ok=True)
        self.output_file = Path("data/bpi_manual_parsed.json")
        
    def extract_properties_from_html(self, html_content: str, source_file: str = "unknown") -> List[Dict[str, Any]]:
        """
        Extract property data from a single HTML file.
        
        Args:
            html_content: HTML content as string
            source_file: Name of the source file for logging
            
        Returns:
            List of property dictionaries
        """
        properties = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find all property result containers
        property_containers = soup.find_all('div', class_='result-each')
        
        print(f"Found {len(property_containers)} properties in {source_file}")
        
        for container in property_containers:
            try:
                property_data = self._extract_single_property(container)
                if property_data:
                    property_data['source_file'] = source_file
                    properties.append(property_data)
            except Exception as e:
                print(f"Error extracting property from {source_file}: {e}")
                continue
        
        return properties
    
    def _extract_single_property(self, container) -> Optional[Dict[str, Any]]:
        """
        Extract data from a single property container.
        
        Args:
            container: BeautifulSoup element containing property data
            
        Returns:
            Property data dictionary or None if extraction fails
        """
        try:
            # Initialize property data
            property_data = {
                'property_id': 'NA',
                'property_type': 'NA',
                'title': 'NA',
                'location': 'NA',
                'address': 'NA',
                'price': 'NA',
                'image_url': 'NA',
                'detail_url': 'NA',
                'lot_area': 'NA',
                'floor_area': 'NA',
                'bedrooms': 'NA',
                'bathrooms': 'NA',
                'property_classification': 'NA',
                'special_concerns': 'NA',
                'sales_advisor': 'NA',
                'contact_no': 'NA',
                'alternate_contact': 'NA',
                'alternate_contact_no': 'NA'
            }
            
            # Extract property link and ID
            h4_element = container.find('h4')
            if h4_element:
                link_element = h4_element.find('a')
                if link_element:
                    detail_url = link_element.get('href', '')
                    if detail_url:
                        property_data['detail_url'] = detail_url
                        # Extract property ID from URL
                        property_id_match = re.search(r'/property/([^/]+)', detail_url)
                        if property_id_match:
                            property_data['property_id'] = property_id_match.group(1)
                    
                    # Extract title
                    title_text = link_element.get_text(strip=True)
                    property_data['title'] = title_text
                    
                    # Extract property type from title (e.g., "House & Lot (03997-O-247)")
                    type_match = re.match(r'^([^(]+)', title_text)
                    if type_match:
                        property_data['property_type'] = type_match.group(1).strip()
            
            # Extract image URL
            img_element = container.find('img')
            if img_element:
                img_src = img_element.get('src', '')
                if img_src:
                    # Convert relative URLs to absolute
                    if img_src.startswith('./'):
                        img_src = img_src[2:]  # Remove './'
                    elif not img_src.startswith('http'):
                        img_src = f"https://www.buenamano.ph/{img_src}"
                    property_data['image_url'] = img_src
            
            # Extract location, address, and price from paragraphs
            p_elements = container.find_all('p')
            for p in p_elements:
                text = p.get_text(strip=True)
                
                if text.startswith('Location:'):
                    location = text.replace('Location:', '').strip()
                    property_data['location'] = location
                
                elif text.startswith('Price:'):
                    price = text.replace('Price:', '').strip()
                    property_data['price'] = price
                
                elif text and not text.startswith('Location:') and not text.startswith('Price:'):
                    # This is likely the address
                    if property_data['address'] == 'NA':
                        property_data['address'] = text
            
            return property_data
            
        except Exception as e:
            print(f"Error extracting single property: {e}")
            return None
    
    def extract_detailed_property_info(self, html_content: str, source_file: str = "unknown") -> Dict[str, Any]:
        """
        Extract detailed property information from a property detail page.
        
        Args:
            html_content: HTML content of property detail page
            source_file: Name of the source file for logging
            
        Returns:
            Detailed property information dictionary
        """
        detailed_info = {
            'full_address': 'NA',
            'detailed_description': 'NA',
            'property_features': 'NA',
            'contact_info': 'NA',
            'viewing_info': 'NA',
            'terms_conditions': 'NA',
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
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract from property-summary div
        property_summary = soup.find('div', class_='property-summary')
        if property_summary:
            # Extract title
            h3 = property_summary.find('h3')
            if h3:
                detailed_info['title'] = h3.get_text(strip=True)
            
            # Extract location and address
            p_elements = property_summary.find_all('p')
            for p in p_elements:
                text = p.get_text(strip=True)
                
                if 'Location :' in text:
                    location = text.replace('Location :', '').strip()
                    detailed_info['location'] = location
                
                elif 'Lot Area (sqm) :' in text:
                    lot_area = text.replace('Lot Area (sqm) :', '').strip()
                    detailed_info['lot_area_sqm'] = lot_area
                
                elif 'Floor Area (sqm) :' in text:
                    floor_area = text.replace('Floor Area (sqm) :', '').strip()
                    detailed_info['floor_area_sqm'] = floor_area
                
                elif 'Price (Php) :' in text:
                    price = text.replace('Price (Php) :', '').strip()
                    detailed_info['price_php'] = price
                
                elif 'Storeys :' in text:
                    storeys = text.replace('Storeys :', '').strip()
                    detailed_info['storeys'] = storeys
                
                elif 'Bedrooms :' in text:
                    bedrooms = text.replace('Bedrooms :', '').strip()
                    detailed_info['bedrooms'] = bedrooms
                
                elif 'Bathrooms :' in text:
                    bathrooms = text.replace('Bathrooms :', '').strip()
                    detailed_info['bathrooms'] = bathrooms
                
                elif 'Usage Classification :' in text:
                    usage = text.replace('Usage Classification :', '').strip()
                    detailed_info['usage_classification'] = usage
            
            # Extract address (it's usually in a separate p element)
            address_p = property_summary.find('p', string=lambda text: text and 'Lot' in text and 'Block' in text)
            if address_p:
                detailed_info['full_address'] = address_p.get_text(strip=True)
        
        # Extract from property-location-content div
        property_location = soup.find('div', class_='property-location-content')
        if property_location:
            p_elements = property_location.find_all('p')
            for p in p_elements:
                text = p.get_text(strip=True)
                
                if 'Property Classification:' in text:
                    classification = text.replace('Property Classification:', '').strip()
                    detailed_info['property_classification'] = classification
                
                elif 'Sales Advisor :' in text:
                    advisor = text.replace('Sales Advisor :', '').strip()
                    detailed_info['sales_advisor'] = advisor
                
                elif 'Contact No. :' in text:
                    contact = text.replace('Contact No. :', '').strip()
                    detailed_info['contact_no'] = contact
                
                elif 'Alternate :' in text:
                    alternate = text.replace('Alternate :', '').strip()
                    detailed_info['alternate'] = alternate
                
                elif "Alternate's No. :" in text:
                    alternate_no = text.replace("Alternate's No. :", '').strip()
                    detailed_info['alternate_no'] = alternate_no
            
            # Extract special concerns
            special_concerns = property_location.find('p', string=lambda text: text and 'Special Concerns:' in text)
            if special_concerns:
                next_elem = special_concerns.find_next_sibling()
                if next_elem:
                    concerns_text = next_elem.get_text(strip=True)
                    if concerns_text and concerns_text != '-':
                        detailed_info['special_concerns'] = concerns_text
        
        return detailed_info
    
    def parse_all_html_files(self) -> List[Dict[str, Any]]:
        """
        Parse all HTML files in the directory.
        
        Returns:
            List of all extracted properties
        """
        all_properties = []
        
        # Find all HTML files in the directory
        html_files = list(self.html_directory.glob("*.html"))
        
        print(f"Looking for HTML files in: {self.html_directory}")
        print(f"Found {len(html_files)} HTML files")
        
        if not html_files:
            print("No HTML files found. Please download BPI pages manually first.")
            return []
        
        print(f"Processing {len(html_files)} HTML files...")
        
        for i, html_file in enumerate(html_files, 1):
            print(f"Processing file {i}/{len(html_files)}: {html_file.name}")
            try:
                with open(html_file, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                # Check if this is a search results page or a detail page
                if 'search-results' in html_content or 'result-each' in html_content:
                    # This is a search results page
                    properties = self.extract_properties_from_html(html_content, html_file.name)
                    print(f"Found {len(properties)} properties in {html_file.name}")
                    all_properties.extend(properties)
                
                elif 'property-summary' in html_content:
                    # This is a property detail page
                    detailed_info = self.extract_detailed_property_info(html_content, html_file.name)
                    if detailed_info.get('title') != 'NA':
                        all_properties.append(detailed_info)
                        print(f"Found detailed info from {html_file.name}")
                
                else:
                    print(f"Unknown page type in {html_file.name}")
            
            except Exception as e:
                print(f"Error parsing {html_file.name}: {e}")
                continue
        
        print(f"Total properties found: {len(all_properties)}")
        
        # Save results
        if all_properties:
            self.save_properties(all_properties)
            print(f"Results saved to: {self.output_file}")
        
        return all_properties
    
    def save_properties(self, properties: List[Dict[str, Any]]) -> None:
        """
        Save extracted properties to JSON file.
        
        Args:
            properties: List of property dictionaries
        """
        # Remove duplicates based on property_id or detail_url
        unique_properties = []
        seen_ids = set()
        seen_urls = set()
        
        for prop in properties:
            prop_id = prop.get('property_id', '')
            detail_url = prop.get('detail_url', '')
            
            if prop_id and prop_id != 'NA':
                if prop_id not in seen_ids:
                    seen_ids.add(prop_id)
                    unique_properties.append(prop)
            elif detail_url and detail_url != 'NA':
                if detail_url not in seen_urls:
                    seen_urls.add(detail_url)
                    unique_properties.append(prop)
            else:
                # If no ID or URL, include it anyway
                unique_properties.append(prop)
        
        # Save to JSON
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(unique_properties, f, indent=2, ensure_ascii=False)
        
        print(f"\nSaved {len(unique_properties)} unique properties to {self.output_file}")
        print(f"Removed {len(properties) - len(unique_properties)} duplicates")
    
    def run(self) -> List[Dict[str, Any]]:
        """
        Run the complete parsing process.
        
        Returns:
            List of extracted properties
        """
        print("=== BPI Manual HTML Parser ===")
        print(f"Looking for HTML files in: {self.html_directory}")
        print("This parser extracts property data from manually downloaded HTML files")
        print("=" * 50)
        
        properties = self.parse_all_html_files()
        
        if properties:
            self.save_properties(properties)
            
            print(f"\nSummary:")
            print(f"   - Total properties extracted: {len(properties)}")
            print(f"   - Properties with IDs: {len([p for p in properties if p.get('property_id') != 'NA'])}")
            print(f"   - Properties with prices: {len([p for p in properties if p.get('price') != 'NA'])}")
            print(f"   - Properties with addresses: {len([p for p in properties if p.get('address') != 'NA'])}")
            
            # Show sample data
            if properties:
                print(f"\nSample extracted data:")
                print(json.dumps(properties[0], indent=2))
        else:
            print("No properties extracted. Please ensure HTML files are in the correct directory.")
        
        return properties

def main():
    """Main function to run the parser."""
    parser = BPIManualHTMLParser()
    parser.run()

if __name__ == "__main__":
    main() 