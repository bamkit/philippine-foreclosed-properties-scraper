import sys
import os
# Add the parent directory to sys.path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re
import json
import asyncio
from typing import Dict, List, Any
from pathlib import Path

import pdfplumber
from crawl4ai import AsyncWebCrawler

try:
    from ..utils.base_scraper import BaseBankScraper
    from ..utils.config import BANKS
except ImportError:
    from utils.base_scraper import BaseBankScraper
    from utils.config import BANKS


class MetrobankScraper(BaseBankScraper):
    """Scraper for Metrobank foreclosed properties from PDF."""
    
    def __init__(self, *args, **kwargs):
        """Initialize the Metrobank scraper."""
        bank_name = "Metrobank"
        bank_url = BANKS[bank_name.lower()]['url']
        super().__init__(bank_name=bank_name, bank_url=bank_url, *args, **kwargs)
        self.pdf_path = self._find_metrobank_pdf()
        
    def _find_metrobank_pdf(self) -> str:
        """Find the Metrobank PDF file in the pdf_input folder.
        
        Returns:
            Path to the PDF file or None if not found
        """
        pdf_dir = os.path.join("foreclosed_scraper", "pdf_input")
        for fname in os.listdir(pdf_dir):
            if fname.lower().startswith("metrobank") and fname.lower().endswith(".pdf"):
                return os.path.join(pdf_dir, fname)
        print(f"No PDF file starting with 'METROBANK' found in {pdf_dir}")
        return None
    
    async def _extract_property_list(self, crawler=None) -> List[Dict[str, Any]]:
        """Extract the list of properties from the Metrobank PDF.
        
        Args:
            crawler: Not used for PDF processing
            
        Returns:
            A list of dictionaries containing property information
        """
        if not self.pdf_path:
            print("No Metrobank PDF file found to scrape.")
            return []
        
        if not os.path.exists(self.pdf_path):
            print(f"PDF file not found at {self.pdf_path}")
            return []
        
        print(f"Starting scraping for {self.bank_name} from PDF: {self.pdf_path}")
        properties = []
        
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                print(f"Processing {len(pdf.pages)} pages from PDF")
                
                for page_num, page in enumerate(pdf.pages):
                    print(f"Processing page {page_num + 1}")
                    
                    # Extract tables from the page
                    tables = page.extract_tables()
                    
                    for table_num, table in enumerate(tables):
                        if not table or len(table) < 2:  # Skip empty tables or tables with only header
                            continue
                        
                        print(f"Processing table {table_num + 1} on page {page_num + 1} with {len(table)} rows")
                        
                        # Process the table
                        table_properties = self._process_table(table, page_num + 1, table_num + 1)
                        properties.extend(table_properties)
                
                print(f"Successfully extracted {len(properties)} properties from PDF")
                return properties
                
        except Exception as e:
            print(f"Error processing PDF: {e}")
            return []
    
    def _process_table(self, table: List[List], page_num: int, table_num: int) -> List[Dict[str, Any]]:
        """Process a single table and extract property data.
        
        Args:
            table: The table data as a list of rows
            page_num: Page number for debugging
            table_num: Table number for debugging
            
        Returns:
            List of property dictionaries
        """
        properties = []
        
        # Find the header row
        header_row = None
        header_row_index = -1
        
        for i, row in enumerate(table):
            if not row:
                continue
            
            # Convert all cells to strings and clean them
            row_str = [str(cell).strip() if cell else "" for cell in row]
            
            # Skip disclaimer rows
            if any("disclaimer" in cell.lower() for cell in row_str if cell):
                continue
            
            # Look for actual property table headers (not disclaimer)
            # Check if this row contains property-related headers
            row_text = " ".join(row_str).upper()
            
            # Look for common property table header patterns
            if (any(keyword in row_text for keyword in 
                   ["PROPERTY", "LOCATION", "PRICE", "AREA", "DESCRIPTION", "TYPE", "CLASSIFICATION"]) and
                not any(keyword in row_text for keyword in ["DISCLAIMER", "AS-IS", "WHERE-IS", "NO RECOURSE"])):
                
                # Additional check: make sure it's not just a single property ID
                if len([cell for cell in row_str if cell and len(cell) > 5]) >= 3:
                    header_row = row_str
                    header_row_index = i
                    print(f"Found property header row at index {i}: {[cell[:50] + '...' if len(cell) > 50 else cell for cell in header_row]}")
                    break
        
        if not header_row:
            print(f"No valid property header row found in table {table_num} on page {page_num}")
            return []
        
        # Process data rows (rows after the header)
        for i in range(header_row_index + 1, len(table)):
            row = table[i]
            if not row:
                continue
            
            # Convert row to strings and clean
            row_str = [str(cell).strip() if cell else "" for cell in row]
            
            # Skip empty rows or rows that look like headers
            if not any(cell for cell in row_str) or len([cell for cell in row_str if cell]) < 2:
                continue
            
            # Skip if this row looks like a repeated header or disclaimer
            if self._is_header_row(row_str) or self._is_disclaimer_row(row_str):
                continue
            
            # Create property dictionary
            property_data = {}
            
            # Map row data to header columns
            for j, header in enumerate(header_row):
                if j < len(row_str):
                    property_data[header] = row_str[j]
                else:
                    property_data[header] = ""
            
            # Only add if we have meaningful data
            if self._has_meaningful_data(property_data):
                # Return the data as-is, preserving original column names
                properties.append(property_data)
        
        print(f"Extracted {len(properties)} properties from table {table_num} on page {page_num}")
        return properties
    
    def _is_header_row(self, row: List[str]) -> bool:
        """Check if a row looks like a header row.
        
        Args:
            row: The row to check
            
        Returns:
            True if the row looks like a header
        """
        if not row:
            return False
        
        # Check if all non-empty cells contain header-like text
        header_keywords = ["PROPERTY", "LOCATION", "PRICE", "AREA", "DESCRIPTION", "TYPE", "CLASSIFICATION", "STATUS"]
        row_text = " ".join(row).upper()
        
        # If more than 50% of the row contains header keywords, it's likely a header
        keyword_count = sum(1 for keyword in header_keywords if keyword in row_text)
        return keyword_count >= len(header_keywords) * 0.3  # 30% threshold
    
    def _is_disclaimer_row(self, row: List[str]) -> bool:
        """Check if a row looks like a disclaimer row.
        
        Args:
            row: The row to check
            
        Returns:
            True if the row looks like a disclaimer
        """
        if not row:
            return False
        
        row_text = " ".join(row).lower()
        disclaimer_keywords = ["disclaimer", "as-is", "where-is", "no recourse", "warranties", "buybacks"]
        
        return any(keyword in row_text for keyword in disclaimer_keywords)
    
    def _has_meaningful_data(self, property_data: Dict[str, str]) -> bool:
        """Check if property data contains meaningful information.
        
        Args:
            property_data: The property data to check
            
        Returns:
            True if the data contains meaningful information
        """
        # Check if we have at least some basic information
        meaningful_fields = ["PROPERTY", "LOCATION", "PRICE", "AREA", "DESCRIPTION"]
        
        for field in meaningful_fields:
            for key, value in property_data.items():
                if field in key.upper() and value and value.strip():
                    return True
        
        return False
    
    def _normalize_property_data(self, property_data: Dict[str, str]) -> Dict[str, Any]:
        """Return property data as-is without normalization.
        
        Args:
            property_data: Raw property data from PDF
            
        Returns:
            Property data with original column names
        """
        # Return the data as-is, preserving original column names
        return property_data
    
    def _extract_province_from_location(self, location: str) -> str:
        """Extract province from location string.
        
        Args:
            location: Location string
            
        Returns:
            Extracted province or empty string
        """
        # Common Metro Manila cities
        metro_cities = ["makati", "manila", "quezon city", "taguig", "pasig", "mandaluyong", 
                       "pasay", "parañaque", "muntinlupa", "las piñas", "marikina", "san juan"]
        
        location_lower = location.lower()
        
        # Check if it's a Metro Manila city
        for city in metro_cities:
            if city in location_lower:
                return "Metro Manila"
        
        # Check for other provinces
        if "calamba" in location_lower:
            return "Laguna"
        elif "calatagan" in location_lower:
            return "Batangas"
        elif "cavite" in location_lower:
            return "Cavite"
        elif "rizal" in location_lower:
            return "Rizal"
        elif "bulacan" in location_lower:
            return "Bulacan"
        elif "pampanga" in location_lower:
            return "Pampanga"
        
        return ""
    
    def _extract_classification_from_title(self, title: str) -> str:
        """Extract property classification from title.
        
        Args:
            title: Property title
            
        Returns:
            Extracted classification or empty string
        """
        title_lower = title.lower()
        
        if "house" in title_lower or "residential" in title_lower:
            return "Residential"
        elif "commercial" in title_lower:
            return "Commercial"
        elif "industrial" in title_lower:
            return "Industrial"
        elif "agricultural" in title_lower or "farm" in title_lower:
            return "Agricultural"
        elif "condo" in title_lower or "condominium" in title_lower:
            return "Condominium"
        elif "beach" in title_lower:
            return "Beach Property"
        elif "lot" in title_lower and "house" not in title_lower:
            return "Lot Only"
        
        return ""
    
    def _extract_area_from_text(self, text: str) -> str:
        """Extract area from text.
        
        Args:
            text: Text to search for area
            
        Returns:
            Extracted area or empty string
        """
        # Look for area patterns like "100 sqm", "150 sq.m.", etc.
        area_patterns = [
            r'(\d+(?:,\d+)?(?:\.\d+)?)\s*sq\.?m\.?',
            r'(\d+(?:,\d+)?(?:\.\d+)?)\s*square\s*meters?',
            r'(\d+(?:,\d+)?(?:\.\d+)?)\s*hectares?',
            r'(\d+(?:,\d+)?(?:\.\d+)?)\s*ha'
        ]
        
        for pattern in area_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1) + " sqm"
        
        return ""
    
    def _extract_price_from_text(self, text: str) -> str:
        """Extract price from text.
        
        Args:
            text: Text to search for price
            
        Returns:
            Extracted price or empty string
        """
        # Look for price patterns
        price_patterns = [
            r'PHP\s*([\d,]+(?:\.\d+)?)',
            r'₱\s*([\d,]+(?:\.\d+)?)',
            r'([\d,]+(?:\.\d+)?)\s*pesos?',
            r'([\d,]+(?:\.\d+)?)\s*million',
            r'([\d,]+(?:\.\d+)?)\s*m'
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return "PHP " + match.group(1)
        
        return ""
    
    async def _extract_property_details(self, crawler: AsyncWebCrawler, detail_url: str) -> Dict[str, Any]:
        """Extract detailed information for a specific property.
        
        Since we're working with PDF data, this method returns empty details
        as all information is already extracted from the PDF.
        
        Args:
            crawler: The web crawler instance (not used for PDF)
            detail_url: The URL of the property detail page (not used for PDF)
            
        Returns:
            Empty dictionary as details are already extracted
        """
        return {}
    
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
        """Scrape foreclosed properties from Metrobank PDF.
        
        Returns:
            A list of dictionaries containing property information
        """
        print("Note: Extracting properties from Metrobank PDF file.")
        print("      This provides the most up-to-date listings from Metrobank.")
        
        try:
            properties = await super().scrape()
            
            # Return all properties without filtering
            print(f"Successfully extracted {len(properties)} properties from PDF")
            return properties
                
        except Exception as e:
            print(f"Error during Metrobank PDF processing: {e}")
            return [] 