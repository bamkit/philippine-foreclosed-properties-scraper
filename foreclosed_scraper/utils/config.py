import os
import dotenv
from pathlib import Path

# Load environment variables
dotenv_path = Path(__file__).parent.parent / ".env"
if dotenv_path.exists():
    dotenv.load_dotenv(dotenv_path)
else:
    print("Warning: .env file not found. Using environment variables or defaults.")

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

# Scraper Settings
MAX_RESULTS_PER_BANK = int(os.getenv("MAX_RESULTS_PER_BANK", "20"))
USER_AGENT = os.getenv(
    "USER_AGENT", 
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
)

# Output Settings
OUTPUT_DIRECTORY = os.getenv("OUTPUT_DIRECTORY", "./data")
OUTPUT_PATH = Path(__file__).parent.parent / Path(OUTPUT_DIRECTORY.strip("./"))

# Bank configurations
BANKS = {
    "bdo": {
        "name": "BDO",
        "url": "https://www.bdo.com.ph/properties-for-sale",
        "pagination": True,
    },
    "bdo_playwright": {
        "name": "BDO (Enhanced Playwright)",
        "url": "https://www.bdo.com.ph/personal/assets-for-sale/real-estate/results-page",
        "pagination": True,
    },
    "bdo_stealth": {
        "name": "BDO (Stealth Mode)",
        "url": "https://www.bdo.com.ph/personal/assets-for-sale/real-estate/results-page",
        "pagination": True,
    },
    "bdo_manual": {
        "name": "BDO (Manual Mode)",
        "url": "https://www.bdo.com.ph/personal/assets-for-sale/real-estate/results-page",
        "pagination": True,
    },
    "bpi": {
        "name": "BPI",
        "url": "https://www.bpiloans.com/properties-for-sale",
        "pagination": True,
    },
    "security_bank": {
        "name": "Security Bank",
        "url": "https://www.securitybank.com/personal/loans/repossessed-assets/properties-for-sale/",
        "pagination": True,
    },
    "metrobank": {
        "name": "Metrobank",
        "url": "https://www.metrobank.com.ph/acquire/properties-for-sale",
        "pagination": True,
    },
    "eastwest_bank": {
        "name": "Eastwest Bank",
        "url": "https://pre-owned-properties.eastwestbanker.com/",
        "pagination": True,
    },
    "pnb": {
        "name": "PNB",
        "url": "https://www.pnb.com.ph/index.php/search-properties?tpl=2",
        "pagination": True,
    },
    "landbank": {
        "name": "Landbank",
        "url": "https://www.landbank.com/properties-for-sale",
        "pagination": True,
    }
}

# Ensure output directory exists
OUTPUT_PATH.mkdir(parents=True, exist_ok=True) 