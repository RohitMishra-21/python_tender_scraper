#!/usr/bin/env python3
"""
Debug run script for the tender scraper - keeps browser open longer for inspection
"""

import sys
import os
import time

# Add the src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from scraper.tender_scrapper import OdishaTenderScraperEnhanced

def debug_run():
    """Run scraper with debug settings"""
    try:
        print("Starting DEBUG run of the tender scraper...")
        
        # Initialize scraper
        scraper = OdishaTenderScraperEnhanced()
        scraper.set_max_records(5)  # Small number for testing
        scraper.config["debug_keep_browser_open"] = True
        
        print(f"Debug settings:")
        print(f"  - Max records: {scraper.max_records}")
        print(f"  - Keep browser open: {scraper.config.get('debug_keep_browser_open', False)}")
        
        # Setup driver
        if not scraper.setup_driver():
            print("Failed to setup browser driver")
            return False
        
        # Navigate to target URL
        print("Navigating to tender website...")
        scraper.driver.get(scraper.target_url)
        
        # Wait for page to load
        if not scraper.wait_for_element(scraper.driver.find_element, By.NAME, "tenderStatus"):
            print("Failed to load initial page")
            return False
        
        # Set tender status to AOC
        print("Setting tender status to AOC...")
        if not scraper.set_tender_status_aoc():
            print("Failed to set tender status to AOC")
            return False
        
        # Manual captcha - give user instructions
        print("\n" + "="*50)
        print("MANUAL CAPTCHA STEP:")
        print("1. Look at the browser window")
        print("2. Find and solve the captcha")
        print("3. Press Enter here when ready to continue")
        print("="*50)
        input("Press Enter when captcha is solved...")
        
        # Find and click search button
        search_selectors = [
            "//input[@value='Search']",
            "//button[contains(text(), 'Search')]",
            "//input[@type='submit'][contains(@value, 'Search')]"
        ]
        
        search_button = None
        for selector in search_selectors:
            try:
                search_button = scraper.driver.find_element(By.XPATH, selector)
                if search_button and search_button.is_displayed():
                    break
            except:
                continue
        
        if search_button:
            print("Clicking search button...")
            search_button.click()
            time.sleep(5)  # Wait for results
        else:
            print("Could not find search button")
            return False
        
        # Now debug the results page
        print("Debugging results page...")
        
        # Save page source
        with open("debug_page_source.html", "w", encoding="utf-8") as f:
            f.write(scraper.driver.page_source)
        print("Saved page source to debug_page_source.html")
        
        # Find tables
        all_tables = scraper.driver.find_elements(By.TAG_NAME, "table")
        print(f"Found {len(all_tables)} table(s) on the page")
        
        for i, table in enumerate(all_tables):
            try:
                rows = table.find_elements(By.TAG_NAME, "tr")
                print(f"Table {i+1}: {len(rows)} rows")
                if len(rows) > 0:
                    # Get first row text as sample
                    first_row_text = rows[0].text[:100] if rows[0].text else "Empty"
                    print(f"  First row sample: {first_row_text}")
            except Exception as e:
                print(f"  Error reading table {i+1}: {e}")
        
        # Keep browser open
        print("\n" + "="*50)
        print("Browser will stay open for inspection.")
        print("Check debug_page_source.html for the full page source.")
        print("Press Ctrl+C to exit.")
        print("="*50)
        
        while True:
            time.sleep(10)
            
    except KeyboardInterrupt:
        print("Exiting...")
    except Exception as e:
        print(f"Debug run failed: {e}")
    finally:
        if scraper.driver:
            scraper.driver.quit()
            print("Browser closed")

if __name__ == "__main__":
    debug_run()