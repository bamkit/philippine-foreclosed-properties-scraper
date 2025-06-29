import os
import asyncio
import argparse
from pathlib import Path
import nest_asyncio
from tqdm import tqdm

# Import configuration
from .utils.config import BANKS

# Import the bank scrapers
from .scrapers.bdo_scraper import BDOScraper
from .scrapers.bpi_scraper import BPIScraper
from .scrapers.security_bank_scraper import SecurityBankScraper
from .scrapers.metrobank_scraper import MetrobankScraper
from .scrapers.eastwest_bank_scraper import EastwestBankScraper
from .scrapers.pnb_scraper import PNBScraper

# Apply nest_asyncio to allow nested event loops (useful for Jupyter notebooks)
nest_asyncio.apply()

# Bank scraper mapping
BANK_SCRAPERS = {
    "bdo": BDOScraper,
    "bpi": BPIScraper,
    "security_bank": SecurityBankScraper,
    "metrobank": MetrobankScraper,
    "eastwest_bank": EastwestBankScraper,
    "pnb": PNBScraper,
}

async def scrape_bank(bank_id: str, bank_config: dict) -> None:
    """Scrape a specific bank's foreclosed properties.
    
    Args:
        bank_id: The ID of the bank to scrape
        bank_config: The configuration for the bank
    """
    try:
        print(f"Scraping {bank_config['name']} foreclosed properties...")
        print(f"URL: {bank_config['url']}")
        
        scraper_class = BANK_SCRAPERS.get(bank_id)
        
        if scraper_class:
            scraper = scraper_class()
            properties = await scraper.scrape()
            print(f"Found {len(properties)} properties from {bank_config['name']}.")
        else:
            # For other banks, we'll use the placeholder for now
            print("This bank's scraper is not implemented yet.")
            print("This is a placeholder. The actual scraper will be implemented later.")
            # Simulate a delay
            await asyncio.sleep(1)
        
        print(f"Finished scraping {bank_config['name']}.\n")
    except Exception as e:
        print(f"Error scraping {bank_config['name']}: {str(e)}")


async def scrape_multiple_banks(bank_ids: list) -> None:
    """Scrape foreclosed properties from multiple specified banks.
    
    Args:
        bank_ids: List of bank IDs to scrape
    """
    for bank_id in tqdm(bank_ids, desc="Scraping selected banks"):
        if bank_id in BANKS:
            await scrape_bank(bank_id, BANKS[bank_id])
        else:
            print(f"Error: Bank '{bank_id}' not found. Skipping.")


async def scrape_all_banks() -> None:
    """Scrape foreclosed properties from all banks."""
    for bank_id, bank_config in tqdm(BANKS.items(), desc="Scraping all banks"):
        await scrape_bank(bank_id, bank_config)


def main():
    """Main entry point for the scraper."""
    parser = argparse.ArgumentParser(description="Scrape foreclosed properties from Philippine banks")
    parser.add_argument("--bank", type=str, action="append", help="Specific bank to scrape (e.g., 'bdo', 'bpi', etc.). Can be used multiple times.")
    parser.add_argument("--all", action="store_true", help="Scrape all banks")
    parser.add_argument("--list", action="store_true", help="List available banks")
    
    args = parser.parse_args()
    
    if args.list:
        print("Available banks:")
        for bank_id, bank_config in BANKS.items():
            implemented = bank_id in BANK_SCRAPERS
            status = "✓ Implemented" if implemented else "✗ Not implemented yet"
            print(f"  - {bank_id}: {bank_config['name']} [{status}]")
        return
    
    if args.bank:
        # Remove duplicates while preserving order
        unique_banks = []
        for bank in args.bank:
            if bank not in unique_banks:
                unique_banks.append(bank)
        
        # Check if all banks exist
        invalid_banks = [bank for bank in unique_banks if bank not in BANKS]
        if invalid_banks:
            print(f"Error: The following banks were not found: {', '.join(invalid_banks)}")
            print("Use --list to see available banks.")
            return
        
        asyncio.run(scrape_multiple_banks(unique_banks))
    elif args.all:
        asyncio.run(scrape_all_banks())
    else:
        parser.print_help()


if __name__ == "__main__":
    main() 