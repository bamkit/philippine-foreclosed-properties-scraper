import os
import re
import json
import asyncio
from typing import Dict, List, Any
from pathlib import Path
import io

try:
    import PyPDF2
    from PyPDF2 import PdfReader
    HAS_PDF_READER = True
except ImportError:
    HAS_PDF_READER = False
    print("PyPDF2 not installed. PDF extraction will not be available.")
    print("Install with: pip install PyPDF2")

class SecurityBankPDFScraper:
    def __init__(self):
        self.output_path = Path(__file__).parent.parent / "data" / "security_bank.json"
        self.pdf_folder = Path(__file__).parent.parent / "pdf_input"
        self.required_fields = [
            "Property_type", "Property_description", "Lot_area", "Floor_area",
            "suggested_price", "sale_price", "status_of_title", "remarks"
        ]

    async def _extract_property_list(self) -> List[Dict[str, Any]]:
        if not HAS_PDF_READER:
            print("PyPDF2 not installed. Cannot extract properties from PDF.")
            return []
        print("Searching for Security Bank PDF in pdf_input folder...")
        pdf_files = list(self.pdf_folder.glob("SEC*.pdf"))
        if not pdf_files:
            print("No Security Bank PDF file found in pdf_input folder.")
            return []
        pdf_path = pdf_files[0]
        print(f"Extracting properties from PDF: {pdf_path}")
        properties = []
        try:
            with open(pdf_path, "rb") as f:
                pdf_reader = PdfReader(f)
                full_text = ""
                for page in pdf_reader.pages:
                    text = page.extract_text()
                    if text:
                        full_text += text + "\n"
            print(f"Extracted text from {len(pdf_reader.pages)} pages.")
            
            # Find the table header - it's space-separated, not pipe-separated
            table_header_match = re.search(r'PROPERTY\s+TYPE\s+PROPERTY\s+DESCRIPTION\s+LOT\s+AREA\s+FLOOR\s+AREA\s+SUGGESTED\s+PRICE\s+SALE\s+PRICE\s+STATUS\s+OF\s+TITLE\s+REMARKS', full_text, re.IGNORECASE)
            if table_header_match:
                print("Found table header, extracting properties...")
                # Get content after the header
                table_content = full_text[table_header_match.end():]
                
                # Split into lines and process each property entry
                lines = table_content.split('\n')
                current_property = {}
                current_description_lines = []
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Check if this line starts a new property (contains property type keywords)
                    if re.search(r'^(Residential|Commercial|Agricultural|Industrial|Condominium)', line, re.IGNORECASE):
                        # Save previous property if it exists
                        if current_property and current_property.get('Property_type'):
                            # Clean up the description
                            if current_description_lines:
                                current_property["Property_description"] = " ".join(current_description_lines).strip()
                                # Remove duplicate text patterns
                                current_property["Property_description"] = re.sub(r'(Residential|Commercial|Agricultural|Industrial|Condominium)(?:\s+(?:Lot|Unit|Building|House|Condo|Property))?\s*', '', current_property["Property_description"])
                                current_property["Property_description"] = re.sub(r'\s+', ' ', current_property["Property_description"]).strip()
                            properties.append(current_property)
                        
                        # Start new property
                        current_property = {
                            "Property_type": "",
                            "Property_description": "",
                            "Lot_area": "",
                            "Floor_area": "",
                            "suggested_price": "",
                            "sale_price": "",
                            "status_of_title": "",
                            "remarks": "From Security Bank PDF listing"
                        }
                        current_description_lines = []
                        
                        # Extract property type from this line
                        property_type_match = re.search(r'^(Residential|Commercial|Agricultural|Industrial|Condominium)(?:\s+(?:Lot|Unit|Building|House|Condo|Property))?', line, re.IGNORECASE)
                        if property_type_match:
                            current_property["Property_type"] = property_type_match.group(0).strip()
                        
                        # Extract description (rest of the line after property type)
                        description_start = line.find(current_property["Property_type"]) + len(current_property["Property_type"])
                        if description_start < len(line):
                            description_part = line[description_start:].strip()
                            if description_part:
                                current_description_lines.append(description_part)
                    
                    # Look for area information (sqms.)
                    area_match = re.search(r'(\d+(?:,\d+)?(?:\.\d+)?)\s*sqms?\.', line)
                    if area_match:
                        if not current_property.get("Lot_area"):
                            current_property["Lot_area"] = area_match.group(1) + " sqms."
                        elif not current_property.get("Floor_area"):
                            current_property["Floor_area"] = area_match.group(1) + " sqms."
                    
                    # Look for price information (PHP format)
                    price_match = re.search(r'PHP\s+([\d,]+(?:\.\d+)?)', line)
                    if price_match:
                        if not current_property.get("suggested_price"):
                            current_property["suggested_price"] = "PHP " + price_match.group(1)
                        elif not current_property.get("sale_price"):
                            current_property["sale_price"] = "PHP " + price_match.group(1)
                    
                    # Look for status information
                    status_match = re.search(r'(CONSOLIDATED\s+UNDER\s+SBC|CONSOLIDATED)', line, re.IGNORECASE)
                    if status_match and not current_property.get("status_of_title"):
                        current_property["status_of_title"] = status_match.group(0).strip()
                    
                    # If this line doesn't start a new property and doesn't contain specific data, it might be continuation of description
                    elif current_property and not any(keyword in line for keyword in ['sqms.', 'PHP', 'CONSOLIDATED', 'PROPERTY TYPE', 'PROPERTY DESCRIPTION']):
                        # Only add to description if it's not empty and doesn't look like a header
                        if line and len(line) > 3 and not line.isupper():
                            current_description_lines.append(line)
                
                # Don't forget the last property
                if current_property and current_property.get('Property_type'):
                    # Clean up the description
                    if current_description_lines:
                        current_property["Property_description"] = " ".join(current_description_lines).strip()
                        # Remove duplicate text patterns
                        current_property["Property_description"] = re.sub(r'(Residential|Commercial|Agricultural|Industrial|Condominium)(?:\s+(?:Lot|Unit|Building|House|Condo|Property))?\s*', '', current_property["Property_description"])
                        current_property["Property_description"] = re.sub(r'\s+', ' ', current_property["Property_description"]).strip()
                    properties.append(current_property)
                
                # Filter out properties with empty descriptions or invalid data
                filtered_properties = []
                for prop in properties:
                    if (prop.get("Property_type") and 
                        prop.get("Property_description") and 
                        len(prop.get("Property_description", "")) > 10 and
                        not prop.get("Property_description", "").startswith("Residential")):
                        filtered_properties.append(prop)
                
                properties = filtered_properties
                
            else:
                print("No table header found in PDF text.")
                print("Looking for alternative patterns...")
                
                # Try to find properties using alternative patterns
                property_pattern = r'(Residential|Commercial|Agricultural|Industrial|Condominium)(?:\s+(?:Lot|Unit|Building|House|Condo|Property))?\s+([^0-9]+?)\s+(\d+(?:,\d+)?(?:\.\d+)?)\s*sqms\.\s+(?:\d+(?:,\d+)?(?:\.\d+)?\s*sqms\.\s+)?PHP\s+([\d,]+(?:\.\d+)?)'
                matches = re.finditer(property_pattern, full_text, re.IGNORECASE)
                
                for match in matches:
                    property_entry = {
                        "Property_type": match.group(1).strip(),
                        "Property_description": match.group(2).strip(),
                        "Lot_area": match.group(3) + " sqms.",
                        "Floor_area": "N/A",
                        "suggested_price": "PHP " + match.group(4),
                        "sale_price": "N/A",
                        "status_of_title": "N/A",
                        "remarks": "From Security Bank PDF listing"
                    }
                    properties.append(property_entry)
            
            print(f"Extracted {len(properties)} properties from PDF.")
            return properties
        except Exception as e:
            print(f"Error extracting properties from PDF: {e}")
            return []

    def _save_results(self, properties: List[Dict[str, Any]]):
        with open(self.output_path, "w", encoding="utf-8") as f:
            json.dump(properties, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(properties)} properties to {self.output_path}")

    async def scrape(self):
        properties = await self._extract_property_list()
        self._save_results(properties)
        return properties

if __name__ == "__main__":
    asyncio.run(SecurityBankPDFScraper().scrape()) 