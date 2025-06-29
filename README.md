# Philippine Foreclosed Properties Scraper

A consolidated Python tool to scrape foreclosed property listings from major Philippine banks using a unified command-line interface.

## 🏦 Supported Banks

| Bank | Type | Status |
|------|------|--------|
| **BDO** | Automated Web Scraping | ✅ Working |
| **BPI** | Manual HTML Parser | ✅ Working |
| **Security Bank** | PDF Extraction | ✅ Working |
| **Metrobank** | PDF Extraction | ✅ Working |
| **Eastwest Bank** | Automated Web Scraping | ✅ Working |
| **PNB** | PDF Extraction | ✅ Working |

## 🚀 Quick Start

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd Foreclosed_properties
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Playwright (for automated scrapers):**
   ```bash
   python -m playwright install chromium
   ```

### Usage

**One simple command from the root directory:**

```bash
# List all available banks
python consolidated_scraper.py --list

# Scrape a specific bank
python consolidated_scraper.py --bank bpi
python consolidated_scraper.py --bank bdo
python consolidated_scraper.py --bank security_bank

# Scrape multiple banks
python consolidated_scraper.py --bank bpi --bank security_bank

# Scrape all banks
python consolidated_scraper.py --all
```

## 📊 Bank Details

### BDO (Bank of the Philippine Islands)
- **Method**: Automated web scraping with Selenium
- **Features**: Robots.txt compliant, detailed property information
- **Note**: Time-consuming due to 10-second delays for compliance

### BPI (Bank of the Philippine Islands - Buena Mano)
- **Method**: Manual HTML parsing
- **Requirements**: Download HTML files manually from BPI website
- **Files**: Place HTML files in `foreclosed_scraper/bpi_manual_html/`
- **Output**: Extracts property IDs, prices, addresses, and detail URLs

### Security Bank, Metrobank, PNB
- **Method**: PDF extraction using pdfplumber
- **Requirements**: PDF files in `foreclosed_scraper/pdf_input/`
- **Features**: Table extraction, property classification, pricing

### Eastwest Bank
- **Method**: Automated web scraping
- **Features**: Real-time property listings

## 📁 Output Structure

```
Foreclosed_properties/
├── consolidated_scraper.py          # Main scraper script
├── data/                            # Output directory
│   ├── bpi.json                     # BPI properties
│   ├── bdo.json                     # BDO properties  
│   ├── security_bank.json           # Security Bank properties
│   ├── metrobank.json               # Metrobank properties
│   ├── eastwest_bank.json           # Eastwest Bank properties
│   └── pnb.json                     # PNB properties
├── foreclosed_scraper/
│   ├── bpi_manual_html/             # Manual HTML files for BPI
│   ├── pdf_input/                   # PDF files for bank scrapers
│   └── scrapers/                    # Individual scraper scripts
└── requirements.txt                 # Python dependencies
```

## 📋 Property Data Format

Each property is saved as a JSON object with fields like:

```json
{
  "property_id": "04601-ILO-102",
  "property_type": "Vacant Lot",
  "title": "Vacant Lot (04601-ILO-102)",
  "location": "Capiz Province",
  "address": "Lot 35 Block 2 Tierra Verde Homes...",
  "price": "P102,000.00",
  "detail_url": "https://www.buenamano.ph/property/04601-ILO-102",
  "lot_area": "150 sqm",
  "floor_area": "NA",
  "bedrooms": "NA",
  "bathrooms": "NA"
}
```

## 🔧 Requirements

- Python 3.7+
- Selenium (for automated scrapers)
- pdfplumber (for PDF extraction)
- BeautifulSoup4 (for HTML parsing)
- crawl4ai (for advanced web scraping)

## ⚠️ Important Notes

- **Respect robots.txt**: Automated scrapers include delays to comply with website policies
- **Manual downloads**: BPI requires manual HTML file downloads due to Cloudflare protection
- **PDF files**: Some banks require PDF files to be placed in the `pdf_input/` directory
- **Educational use**: This tool is for educational and research purposes only
- **Terms of service**: Always check website terms before scraping

## 🛠️ Troubleshooting

- **Import errors**: Ensure you're running from the root directory
- **Missing files**: Check that required HTML/PDF files are in the correct directories
- **Browser issues**: Install Playwright browsers if automated scrapers fail
- **Timeout errors**: Some scrapers may take time due to compliance delays

## 📈 Recent Results

- **BPI**: 10 properties extracted from manual HTML
- **Security Bank**: 243 properties extracted from PDF
- **All banks**: Successfully tested and working

---

**Last updated**: December 2024 