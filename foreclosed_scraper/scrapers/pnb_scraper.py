import sys
import os
# Add the parent directory to sys.path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from ..utils.base_scraper import BaseBankScraper
    from ..utils.logger import setup_logger
except ImportError:
    from utils.base_scraper import BaseBankScraper
    from utils.logger import setup_logger
import pdfplumber

class PNBScraper(BaseBankScraper):
    def __init__(self, *args, **kwargs):
        super().__init__(bank_name="pnb", bank_url="https://www.pnb.com.ph/index.php/search-properties?tpl=2", *args, **kwargs)
        self.bank_name = "pnb"
        self.pdf_path = self._find_pnb_pdf()
        self.logger = setup_logger("pnb_scraper")

    def _find_pnb_pdf(self):
        pdf_dir = os.path.join("foreclosed_scraper", "pdf_input")
        for fname in os.listdir(pdf_dir):
            if fname.lower().startswith("pnb") and fname.lower().endswith(".pdf"):
                return os.path.join(pdf_dir, fname)
        self.logger.error(f"No PDF file starting with 'PNB' found in {pdf_dir}")
        return None

    async def _extract_property_list(self, crawler=None):
        if not self.pdf_path:
            self.logger.error("No PNB PDF file found to scrape.")
            return []
        self.logger.info(f"Starting scraping for {self.bank_name} from PDF: {self.pdf_path}")
        properties = []

        if not os.path.exists(self.pdf_path):
            self.logger.error(f"PDF file not found at {self.pdf_path}")
            return []

        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                current_province = None
                current_city = None
                current_contact_person = None
                current_contact_details = None
                for page in pdf.pages:
                    tables = page.extract_tables()
                    for table in tables:
                        header = None
                        for i, row in enumerate(table):
                            # Detect header row
                            if row and any("Title_ID" in str(cell) for cell in row):
                                header = [str(cell).strip() if cell else "" for cell in row]
                                continue
                            # Detect metadata row (region/municipality/contact)
                            if header and row and len([cell for cell in row if cell and str(cell).strip() != ""]) == 1:
                                meta = row[0].split("|")
                                meta = [m.strip() for m in meta]
                                current_province = meta[0] if len(meta) > 0 else None
                                current_city = meta[1] if len(meta) > 1 else None
                                current_contact_person = meta[2] if len(meta) > 2 else None
                                current_contact_details = meta[3] if len(meta) > 3 else None
                                continue
                            # Skip empty or malformed rows
                            if not header or not row or all(cell is None or str(cell).strip() == '' for cell in row):
                                continue
                            # Skip rows that are not property data (e.g., repeated header rows)
                            if row == header:
                                continue
                            # Pad row if it's shorter than header
                            padded_row = list(row) + [None] * (len(header) - len(row))
                            prop = dict(zip(header, padded_row))
                            # Attach metadata
                            prop["Province"] = current_province
                            prop["City/Municipality"] = current_city
                            prop["Contact Person"] = current_contact_person
                            prop["Contact Details"] = current_contact_details
                            # Only add if at least one main property field is present
                            main_fields = [
                                "Title_ID", "Title/CR No.", "Location/Description", "Property use", "Area", "Floor Area", "Minimum Price", "# of Titles", "Status"
                            ]
                            if any(prop.get(f) not in [None, "", "-"] for f in main_fields):
                                properties.append(prop)
        except Exception as e:
            self.logger.error(f"An error occurred while reading or parsing the PDF: {e}")
            return []
        
        self.logger.info(f"Successfully scraped {len(properties)} properties for {self.bank_name}.")
        return properties

    def _save_results(self, properties):
        """
        Override to save the extracted properties directly with the correct PNB columns.
        """
        import json
        with open(self.output_path, "w", encoding="utf-8") as f:
            json.dump(properties, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(properties)} properties to {self.output_path}")

    async def scrape(self):
        properties = await self._extract_property_list()
        self._save_results(properties)
        return properties 