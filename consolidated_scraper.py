#!/usr/bin/env python3
"""
Consolidated Foreclosed Properties Scraper
A unified script to scrape foreclosed properties from multiple Philippine banks.
Supports both automated scraping and manual HTML parsing for BPI.
"""

import os
import sys
import json
import asyncio
import argparse
import subprocess
from pathlib import Path
from typing import List, Dict, Any

class ConsolidatedScraper:
    """Consolidated scraper for all Philippine banks."""
    
    def __init__(self):
        """Initialize the consolidated scraper."""
        self.output_dir = Path("data")
        self.output_dir.mkdir(exist_ok=True)
        
        # Bank configurations
        self.banks = {
            "bdo": {
                "name": "BDO",
                "description": "Bank of the Philippine Islands",
                "status": "✅ Working (Automated)",
                "scraper_type": "automated",
                "script": "foreclosed_scraper/scrapers/bdo_scraper.py"
            },
            "bpi": {
                "name": "BPI",
                "description": "Bank of the Philippine Islands (Buena Mano)",
                "status": "✅ Working (Manual HTML)",
                "scraper_type": "manual",
                "script": "foreclosed_scraper/bpi_manual_html_parser.py"
            },
            "security_bank": {
                "name": "Security Bank",
                "description": "Security Bank Corporation",
                "status": "✅ Working (Automated)",
                "scraper_type": "automated",
                "script": "foreclosed_scraper/scrapers/security_bank_scraper.py"
            },
            "metrobank": {
                "name": "Metrobank",
                "description": "Metropolitan Bank and Trust Company",
                "status": "✅ Working (PDF-based)",
                "scraper_type": "automated",
                "script": "foreclosed_scraper/scrapers/metrobank_scraper.py"
            },
            "eastwest_bank": {
                "name": "Eastwest Bank",
                "description": "East West Banking Corporation",
                "status": "✅ Working (Automated)",
                "scraper_type": "automated",
                "script": "foreclosed_scraper/scrapers/eastwest_bank_scraper.py"
            },
            "pnb": {
                "name": "PNB",
                "description": "Philippine National Bank",
                "status": "✅ Working (PDF-based)",
                "scraper_type": "automated",
                "script": "foreclosed_scraper/scrapers/pnb_scraper.py"
            }
        }
    
    def list_banks(self):
        """List all available banks with their status."""
        print("🏦 Available Philippine Banks:")
        print("=" * 60)
        
        for bank_id, bank_info in self.banks.items():
            print(f"📋 {bank_id.upper()}: {bank_info['name']}")
            print(f"   Description: {bank_info['description']}")
            print(f"   Status: {bank_info['status']}")
            print(f"   Type: {bank_info['scraper_type']}")
            print()
    
    def run_script(self, script_path: str) -> bool:
        """Run a Python script and return success status."""
        try:
            result = subprocess.run([sys.executable, script_path], 
                                  capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                print(f"✅ Script {script_path} completed successfully")
                if result.stdout:
                    print(result.stdout)
                return True
            else:
                print(f"❌ Script {script_path} failed with return code {result.returncode}")
                if result.stderr:
                    print(f"Error: {result.stderr}")
                return False
        except subprocess.TimeoutExpired:
            print(f"❌ Script {script_path} timed out")
            return False
        except Exception as e:
            print(f"❌ Error running script {script_path}: {e}")
            return False
    
    def scrape_bank(self, bank_id: str) -> bool:
        """Scrape a specific bank."""
        if bank_id not in self.banks:
            print(f"❌ Unknown bank: {bank_id}")
            return False
        
        bank_info = self.banks[bank_id]
        script_path = bank_info["script"]
        
        print(f"\n🎯 Starting {bank_info['name']} scraper...")
        print(f"📁 Script: {script_path}")
        
        # Check if script exists
        if not Path(script_path).exists():
            print(f"❌ Script not found: {script_path}")
            return False
        
        # Run the script
        success = self.run_script(script_path)
        
        if success:
            print(f"✅ Successfully completed {bank_info['name']} scraping")
        else:
            print(f"❌ Failed to complete {bank_info['name']} scraping")
        
        return success
    
    def scrape_multiple_banks(self, bank_ids: List[str]):
        """Scrape multiple banks."""
        print(f"🚀 Starting scraping for {len(bank_ids)} banks...")
        
        results = {}
        for bank_id in bank_ids:
            success = self.scrape_bank(bank_id)
            results[bank_id] = success
        
        # Print summary
        print(f"\n📊 Scraping Summary:")
        print("=" * 40)
        successful = 0
        for bank_id, success in results.items():
            status = "✅ Success" if success else "❌ Failed"
            print(f"   {bank_id.upper()}: {status}")
            if success:
                successful += 1
        
        print(f"   Total: {successful}/{len(bank_ids)} banks successful")
    
    def scrape_all_banks(self):
        """Scrape all available banks."""
        bank_ids = list(self.banks.keys())
        self.scrape_multiple_banks(bank_ids)

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Consolidated Foreclosed Properties Scraper for Philippine Banks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python consolidated_scraper.py --list                    # List all banks
  python consolidated_scraper.py --bank bdo               # Scrape BDO only
  python consolidated_scraper.py --bank bpi               # Parse BPI manual HTML
  python consolidated_scraper.py --bank bdo --bank bpi    # Scrape BDO and parse BPI
  python consolidated_scraper.py --all                    # Scrape all banks
        """
    )
    
    parser.add_argument(
        "--bank", 
        type=str, 
        action="append", 
        help="Specific bank to scrape (bdo, bpi, security_bank, metrobank, eastwest_bank, pnb). Can be used multiple times."
    )
    parser.add_argument(
        "--all", 
        action="store_true", 
        help="Scrape all available banks"
    )
    parser.add_argument(
        "--list", 
        action="store_true", 
        help="List all available banks with their status"
    )
    
    args = parser.parse_args()
    
    scraper = ConsolidatedScraper()
    
    if args.list:
        scraper.list_banks()
        return
    
    if args.bank:
        # Remove duplicates while preserving order
        unique_banks = []
        for bank in args.bank:
            if bank not in unique_banks:
                unique_banks.append(bank)
        
        # Validate bank names
        invalid_banks = [bank for bank in unique_banks if bank not in scraper.banks]
        if invalid_banks:
            print(f"❌ Error: Unknown banks: {', '.join(invalid_banks)}")
            print("Use --list to see available banks.")
            return
        
        scraper.scrape_multiple_banks(unique_banks)
    
    elif args.all:
        scraper.scrape_all_banks()
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 