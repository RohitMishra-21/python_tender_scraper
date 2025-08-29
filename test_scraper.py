#!/usr/bin/env python3
"""
Test script for the enhanced tender scraper
"""

import sys
import os

# Add the src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from scraper.tender_scrapper import OdishaTenderScraperEnhanced

def test_scraper():
    """Test the basic functionality"""
    try:
        print("Testing Enhanced Odisha Tender Scraper...")
        
        # Initialize scraper
        scraper = OdishaTenderScraperEnhanced()
        print(f"[OK] Scraper initialized with default max_records: {scraper.max_records}")
        
        # Test setting max records
        test_records = 10
        scraper.set_max_records(test_records)
        print(f"[OK] Max records set to: {scraper.max_records}")
        
        # Test config loading
        print(f"[OK] Configuration loaded:")
        print(f"  - Target URL: {scraper.target_url}")
        print(f"  - Excel file: {scraper.excel_file}")
        print(f"  - Download folder: {scraper.download_folder}")
        
        print("\n[SUCCESS] Basic tests passed!")
        print("\nTo run the full scraper, use:")
        print("python -m src.scraper.tender_scrapper")
        print("or")
        print("python src/scraper/tender_scrapper.py --records 50")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        return False

if __name__ == "__main__":
    test_scraper()