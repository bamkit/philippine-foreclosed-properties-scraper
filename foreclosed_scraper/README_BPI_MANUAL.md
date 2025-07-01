# BPI Manual HTML Parser

## Overview

The BPI Manual HTML Parser is a workaround solution for extracting foreclosed property data from BPI/Buena Mano website. Due to aggressive anti-bot measures (Cloudflare protection), automated scraping is not possible. This parser works with manually downloaded HTML files.

## Why Manual HTML Parser?

- **Cloudflare Protection**: BPI website uses aggressive anti-bot measures
- **IP Blocking**: Automated requests get blocked quickly
- **CAPTCHA Challenges**: Frequent CAPTCHA challenges prevent automated access
- **Rate Limiting**: Strict rate limiting on automated requests

## How It Works

1. **Manual Download**: User manually downloads HTML pages from BPI website
2. **Local Processing**: Parser reads saved HTML files locally
3. **Data Extraction**: Extracts property data without hitting the live website
4. **JSON Output**: Saves extracted data to JSON format

## Setup Instructions

### 1. Create Directory Structure

```bash
mkdir -p foreclosed_scraper/bpi_manual_html
```

### 2. Download HTML Files Manually

1. Visit: https://www.buenamano.ph/search/result
2. Navigate through all pages (usually 10-20 pages)
3. For each page:
   - Right-click → "Save As" → Save as HTML
   - Name files as: `page1.html`, `page2.html`, etc.
   - Save in: `foreclosed_scraper/bpi_manual_html/`

### 3. Download Property Detail Pages (Optional)

For detailed property information:
1. Click on individual property links
2. Save each property detail page as HTML
3. Save in: `foreclosed_scraper/bpi_manual_html/`

## Usage

### Run the Parser

```bash
cd foreclosed_scraper
python bpi_manual_html_parser.py
```

### Expected Output

```
=== BPI Manual HTML Parser ===
Looking for HTML files in: foreclosed_scraper/bpi_manual_html
This parser extracts property data from manually downloaded HTML files
==================================================
Looking for HTML files in: foreclosed_scraper/bpi_manual_html
Found 3 HTML files
Processing 3 HTML files...
Processing file 1/3: page1.html
Found 10 properties in page1.html
Processing file 2/3: page2.html
Found 10 properties in page2.html
Processing file 3/3: page3.html
Found 10 properties in page3.html
Total properties found: 30

Saved 30 unique properties to data/bpi_manual_parsed.json
Removed 0 duplicates

Summary:
   - Total properties extracted: 30
   - Properties with IDs: 30
   - Properties with prices: 30
   - Properties with addresses: 30
```

## Output Format

The parser creates a JSON file with the following structure:

```json
[
  {
    "property_id": "03997-O-247",
    "property_type": "House & Lot",
    "title": "House & Lot (03997-O-247)",
    "location": "Las Pinas",
    "address": "Lot 1, Block 1, Phase 1, Las Pinas City",
    "price": "₱2,500,000",
    "image_url": "https://www.buenamano.ph/images/property1.jpg",
    "detail_url": "https://www.buenamano.ph/property/03997-O-247",
    "lot_area": "150 sqm",
    "floor_area": "80 sqm",
    "bedrooms": "3",
    "bathrooms": "2",
    "property_classification": "Green Tag",
    "special_concerns": "None",
    "sales_advisor": "John Doe",
    "contact_no": "+63 912 345 6789",
    "alternate_contact": "Jane Smith",
    "alternate_contact_no": "+63 987 654 3210",
    "source_file": "page1.html"
  }
]
```

## File Structure

```
foreclosed_scraper/
├── bpi_manual_html_parser.py          # Main parser script
├── README_BPI_MANUAL.md               # This file
├── bpi_manual_html/                   # Directory for HTML files
│   ├── page1.html
│   ├── page2.html
│   ├── page3.html
│   └── ...
└── data/
    └── bpi_manual_parsed.json         # Output file
```

## Troubleshooting

### No HTML Files Found
```
No HTML files found. Please download BPI pages manually first.
```
**Solution**: Download HTML files manually and place them in `foreclosed_scraper/bpi_manual_html/`

### Unknown Page Type
```
Unknown page type in page1.html
```
**Solution**: Make sure you're downloading the correct pages (search results pages, not login pages)

### Encoding Issues
**Solution**: Ensure HTML files are saved with UTF-8 encoding

## Integration with Consolidated Scraper

The BPI manual parser is integrated with the consolidated scraper:

```bash
python consolidated_scraper.py --bank bpi
```

This will run the manual HTML parser instead of attempting automated scraping.

## Advantages

- ✅ **Bypasses Anti-Bot Protection**: No risk of IP blocking
- ✅ **Reliable**: Works consistently without rate limiting
- ✅ **Complete Data**: Can extract all available property information
- ✅ **No Dependencies**: Doesn't require special browser configurations

## Disadvantages

- ❌ **Manual Work**: Requires manual downloading of HTML files
- ❌ **Not Real-Time**: Data is only as current as the downloaded files
- ❌ **Time-Consuming**: Manual process takes time

## Property Classifications

BPI properties are classified by color tags:

- **Green Tag**: Properties with cleared titles and tax declarations under the bank's name
- **Yellow Tag**: Properties with special concerns (e.g., titles in transfer process, occupied)
- **Red Tag**: Properties with pending court cases or legal issues

## Contact Information

For questions about BPI foreclosed properties:
- Website: https://www.buenamano.ph
- Email: buenamano@bpi.com.ph
- Phone: +63 2 8891 0000 