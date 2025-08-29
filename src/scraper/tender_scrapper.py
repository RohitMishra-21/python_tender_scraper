import requests
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.service import Service as EdgeService
import time
import os
from urllib.parse import urljoin
import tkinter as tk
from tkinter import messagebox, simpledialog
from datetime import datetime
import logging
import json
from typing import List, Dict, Optional
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)

class CaptchaHandler:
    """Bulletproof captcha handler - guaranteed to work"""
    
    def get_captcha_input(self, attempt=1, max_attempts=3):
        """Simple approach using only built-in dialogs"""
        from tkinter import simpledialog, messagebox
        import tkinter as tk
        
        print(f"DEBUG: Starting captcha collection, attempt {attempt}")
        
        # Create a temporary root window (required for dialogs)
        temp_root = tk.Tk()
        temp_root.withdraw()  # Hide it
        temp_root.lift()      # Bring to front
        temp_root.focus_force()
        
        try:
            # Show instructions
            messagebox.showinfo("Captcha Required", 
                               f"Captcha Required - Attempt {attempt} of {max_attempts}\n\n"
                               "Instructions:\n"
                               "1. Look at the browser window\n"
                               "2. Find the captcha image on the webpage\n"
                               "3. Enter the captcha text in the next dialog\n\n"
                               "Click OK to continue...",
                               parent=temp_root)
            
            # Get captcha text using simple dialog
            captcha_text = simpledialog.askstring("Enter Captcha", 
                                                 "Enter the captcha text you see in the browser:",
                                                 parent=temp_root)
            
            print(f"DEBUG: User entered: '{captcha_text}'")
            
            # Clean up
            temp_root.destroy()
            
            # Process result
            if captcha_text and captcha_text.strip():
                result_text = captcha_text.strip()
                print(f"DEBUG: Returning successful result: '{result_text}'")
                logging.info(f"Captcha entered: '{result_text}'")
                return {"submitted": True, "text": result_text}
            else:
                print("DEBUG: No captcha text provided")
                logging.info("Captcha cancelled or empty")
                return {"submitted": False, "text": ""}
                
        except Exception as e:
            print(f"DEBUG: Dialog error: {e}")
            try:
                temp_root.destroy()
            except:
                pass
            return {"submitted": False, "text": ""}

class ManualCaptchaHandler:
    """Manual captcha handler - user solves captcha in browser directly"""
    
    def __init__(self, driver):
        self.driver = driver
    
    def wait_for_manual_captcha(self, attempt=1, max_attempts=3):
        """Wait for user to manually solve captcha and confirm"""
        from tkinter import messagebox
        import tkinter as tk
        
        print(f"\n=== MANUAL CAPTCHA VERIFICATION - Attempt {attempt}/{max_attempts} ===")
        
        # Create a simple root window for the dialog
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        root.lift()
        root.focus_force()
        
        try:
            # Show instructions to user
            user_choice = messagebox.askyesno(
                "Manual Captcha Verification",
                f"CAPTCHA VERIFICATION REQUIRED - Attempt {attempt} of {max_attempts}\n\n"
                "INSTRUCTIONS:\n"
                "1. Look at the browser window\n"
                "2. Find the captcha image on the webpage\n"
                "3. Type the captcha characters directly in the browser's captcha field\n"
                "4. DO NOT click Search yet - just enter the captcha\n"
                "5. Once you've entered the captcha, click 'Yes' below\n\n"
                "Have you entered the captcha in the browser?\n\n"
                "Click 'Yes' when ready to continue\n"
                "Click 'No' to cancel",
                parent=root
            )
            
            root.destroy()
            
            if user_choice:
                print("[OK] User confirmed captcha has been entered manually")
                logging.info("User completed manual captcha verification")
                return True
            else:
                print("[FAIL] User cancelled captcha verification")
                logging.info("User cancelled manual captcha verification")
                return False
                
        except Exception as e:
            print(f"[FAIL] Error in manual captcha dialog: {e}")
            try:
                root.destroy()
            except:
                pass
            return False

class OdishaTenderScraperEnhanced:
    def __init__(self, config_file: str = "scraper_config.json", max_records: int = 100):
        """Initialize with max records parameter"""
        self.driver = None
        self.max_records = max_records
        self.current_record_count = 0
        self.load_config(config_file)
        self.setup_directories()
        # GUI integration callbacks
        self.gui_show_captcha_button = None
        self.gui_captcha_event = None
        
    def load_config(self, config_file: str):
        """Load configuration from JSON file or use defaults"""
        default_config = {
            "base_url": "https://tendersodisha.gov.in",
            "target_url": "https://tendersodisha.gov.in/nicgep/app?page=WebTenderStatusLists&service=page",
            "download_folder": "tender_downloads",
            "excel_file_prefix": "odisha_tenders",
            "timeout_seconds": 15,
            "delay_between_requests": 2,
            "max_retries": 3,
            "headless_mode": False
        }
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
                logging.info(f"Configuration loaded from {config_file}")
            except Exception as e:
                logging.warning(f"Could not load config file: {e}. Using defaults.")
        else:
            # Create default config file
            with open(config_file, 'w') as f:
                json.dump(default_config, f, indent=4)
            logging.info(f"Created default config file: {config_file}")
        
        self.config = default_config
        self.base_url = self.config["base_url"]
        self.target_url = self.config["target_url"]
        self.download_folder = self.config["download_folder"]
        self.excel_file = f"{self.config['excel_file_prefix']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
    def setup_directories(self):
        """Create necessary directories"""
        os.makedirs(self.download_folder, exist_ok=True)
        os.makedirs("logs", exist_ok=True)
    
    def detect_default_browser(self):
        """Detect the default browser on Windows"""
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\Shell\Associations\UrlAssociations\http\UserChoice") as key:
                prog_id = winreg.QueryValueEx(key, "Progid")[0]
                
            if "chrome" in prog_id.lower() or "brave" in prog_id.lower():
                return "chrome"
            elif "firefox" in prog_id.lower():
                return "firefox"
            elif "edge" in prog_id.lower() or "msedge" in prog_id.lower():
                return "edge"
            else:
                return "chrome"  # Default fallback
        except:
            return "chrome"  # Default fallback
    
    def find_brave_executable(self):
        """Find Brave browser executable"""
        possible_paths = [
            r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
            r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
            os.path.expanduser(r"~\AppData\Local\BraveSoftware\Brave-Browser\Application\brave.exe"),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        return None

    def setup_chrome_driver(self):
        """Setup Chrome/Brave driver"""
        try:
            chrome_options = ChromeOptions()
            
            # Try to find and use Brave if available
            brave_path = self.find_brave_executable()
            if brave_path:
                chrome_options.binary_location = brave_path
                logging.info(f"Using Brave browser at: {brave_path}")
            
            # Download preferences
            prefs = {
                "download.default_directory": os.path.abspath(self.download_folder),
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True,
                "profile.default_content_settings.popups": 0
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            # Performance options
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--allow-running-insecure-content")
            
            if self.config["headless_mode"]:
                chrome_options.add_argument("--headless")
            
            # Try to use system Chrome/Brave executable directly first
            try:
                self.driver = webdriver.Chrome(options=chrome_options)
                logging.info("Using system Chrome/Brave executable")
                return True
            except:
                # If system executable fails, try with webdriver manager
                service = ChromeService(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                logging.info("Using webdriver manager Chrome")
                return True
            
        except Exception as e:
            logging.error(f"Failed to setup Chrome driver: {e}")
            return False
    
    def setup_firefox_driver(self):
        """Setup Firefox driver"""
        try:
            firefox_options = FirefoxOptions()
            
            # Set download preferences
            firefox_options.set_preference("browser.download.folderList", 2)
            firefox_options.set_preference("browser.download.dir", os.path.abspath(self.download_folder))
            firefox_options.set_preference("browser.download.useDownloadDir", True)
            firefox_options.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/pdf")
            
            if self.config["headless_mode"]:
                firefox_options.add_argument("--headless")
                
            service = FirefoxService(GeckoDriverManager().install())
            self.driver = webdriver.Firefox(service=service, options=firefox_options)
            return True
            
        except Exception as e:
            logging.error(f"Failed to setup Firefox driver: {e}")
            return False
    
    def setup_edge_driver(self):
        """Setup Edge driver"""
        try:
            edge_options = EdgeOptions()
            
            # Download preferences
            prefs = {
                "download.default_directory": os.path.abspath(self.download_folder),
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "profile.default_content_settings.popups": 0
            }
            edge_options.add_experimental_option("prefs", prefs)
            
            # Performance options
            edge_options.add_argument("--no-sandbox")
            edge_options.add_argument("--disable-dev-shm-usage")
            edge_options.add_argument("--disable-gpu")
            edge_options.add_argument("--window-size=1920,1080")
            
            if self.config["headless_mode"]:
                edge_options.add_argument("--headless")
            
            service = EdgeService(EdgeChromiumDriverManager().install())
            self.driver = webdriver.Edge(service=service, options=edge_options)
            return True
            
        except Exception as e:
            logging.error(f"Failed to setup Edge driver: {e}")
            return False

    def setup_driver(self):
        """Setup web driver with automatic browser detection"""
        try:
            # Detect default browser
            default_browser = self.detect_default_browser()
            logging.info(f"Detected default browser: {default_browser}")
            
            # Try to setup the detected browser first
            if default_browser == "chrome":
                if self.setup_chrome_driver():
                    logging.info("Chrome/Brave driver setup successfully")
                    if not self.config["headless_mode"]:
                        self.driver.maximize_window()
                    return True
                    
            elif default_browser == "firefox":
                if self.setup_firefox_driver():
                    logging.info("Firefox driver setup successfully")
                    if not self.config["headless_mode"]:
                        self.driver.maximize_window()
                    return True
                    
            elif default_browser == "edge":
                if self.setup_edge_driver():
                    logging.info("Edge driver setup successfully")
                    if not self.config["headless_mode"]:
                        self.driver.maximize_window()
                    return True
            
            # Fallback: try other browsers if default failed
            logging.info("Trying fallback browsers...")
            
            # Try Chrome first
            if self.setup_chrome_driver():
                logging.info("Chrome driver setup successfully (fallback)")
                if not self.config["headless_mode"]:
                    self.driver.maximize_window()
                return True
                
            # Try Edge second
            if self.setup_edge_driver():
                logging.info("Edge driver setup successfully (fallback)")
                if not self.config["headless_mode"]:
                    self.driver.maximize_window()
                return True
                
            # Try Firefox last
            if self.setup_firefox_driver():
                logging.info("Firefox driver setup successfully (fallback)")
                if not self.config["headless_mode"]:
                    self.driver.maximize_window()
                return True
            
            logging.error("Failed to setup any browser driver")
            return False
            
        except Exception as e:
            logging.error(f"Failed to setup driver: {e}")
            return False
    
    def wait_for_element(self, by: By, value: str, timeout: int = None) -> Optional[object]:
        """Wait for element with enhanced error handling"""
        if timeout is None:
            timeout = self.config["timeout_seconds"]
        
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except Exception as e:
            logging.error(f"Element not found: {by}={value}, Error: {e}")
            return None
    
    def handle_captcha_enhanced(self) -> bool:
        """Simplified captcha handling - focus on making it work"""
        max_attempts = 3
        
        for attempt in range(max_attempts):
            print(f"\n=== CAPTCHA ATTEMPT {attempt + 1}/{max_attempts} ===")
            
            try:
                # Step 1: Find the captcha input field
                print("Step 1: Looking for captcha field...")
                captcha_element = None
                
                # Try name first
                try:
                    captcha_element = self.driver.find_element(By.NAME, "captcha")
                    print("[OK] Found captcha field by name='captcha'")
                except:
                    print("[FAIL] name='captcha' not found")
                
                # Try ID if name failed
                if not captcha_element:
                    try:
                        captcha_element = self.driver.find_element(By.ID, "captcha")
                        print("[OK] Found captcha field by id='captcha'")
                    except:
                        print("[FAIL] id='captcha' not found")
                
                if not captcha_element:
                    print("[FAIL] ERROR: Could not find captcha field")
                    return False
                
                # Step 2: Get captcha from user
                print("Step 2: Getting captcha text from user...")
                captcha_handler = CaptchaHandler()
                result = captcha_handler.get_captcha_input(attempt + 1, max_attempts)
                
                print(f"Step 2 Result: {result}")
                
                if not result or not result.get("submitted"):
                    print("[FAIL] User cancelled captcha input")
                    continue
                
                captcha_text = result.get("text", "").strip()
                if not captcha_text:
                    print("[FAIL] Empty captcha text received")
                    continue
                
                print(f"[OK] Received captcha text: '{captcha_text}' (length: {len(captcha_text)})")
                
                # Step 3: Enter captcha into website field
                print("Step 3: Entering captcha into website...")
                
                try:
                    # Method 1: Standard approach
                    print("  Trying standard input method...")
                    captcha_element.clear()
                    time.sleep(0.5)
                    captcha_element.send_keys(captcha_text)
                    time.sleep(1)
                    
                    # Check if it worked
                    current_value = captcha_element.get_attribute('value')
                    print(f"  Current field value: '{current_value}'")
                    
                    if current_value == captcha_text:
                        print("[OK] SUCCESS: Captcha entered correctly!")
                        return True
                    
                    # Method 2: JavaScript approach
                    print("  Trying JavaScript input method...")
                    self.driver.execute_script(f"arguments[0].value = '{captcha_text}';", captcha_element)
                    time.sleep(1)
                    
                    current_value = captcha_element.get_attribute('value')
                    print(f"  Current field value after JS: '{current_value}'")
                    
                    if current_value == captcha_text:
                        print("[OK] SUCCESS: Captcha entered via JavaScript!")
                        return True
                    
                    print("[FAIL] Both input methods failed")
                    
                except Exception as e:
                    print(f"[FAIL] Error entering captcha: {e}")
                    
            except Exception as e:
                print(f"[FAIL] Attempt {attempt + 1} failed: {e}")
            
            print(f"Attempt {attempt + 1} failed, trying again...\n")
        
        print("[FAIL] All captcha attempts failed")
        return False
    
    def handle_manual_captcha(self) -> bool:
        """Handle captcha manually - user solves it in browser"""
        max_attempts = 3
        
        for attempt in range(max_attempts):
            try:
                print(f"\n[CAPTCHA] Starting manual captcha verification (attempt {attempt + 1}/{max_attempts})")
                
                # First, check if captcha field exists and is visible
                captcha_element = None
                try:
                    captcha_element = self.driver.find_element(By.NAME, "captcha")
                    if captcha_element.is_displayed():
                        print("[OK] Captcha field found and is visible")
                    else:
                        print("[FAIL] Captcha field found but not visible")
                        continue
                except:
                    print("[FAIL] Captcha field not found")
                    continue
                
                # Create manual captcha handler
                manual_handler = ManualCaptchaHandler(self.driver)
                
                # Wait for user to manually solve captcha
                if manual_handler.wait_for_manual_captcha(attempt + 1, max_attempts):
                    print("[OK] User confirmed manual captcha completion")
                    
                    # Optional: Verify that something was entered in the captcha field
                    try:
                        captcha_value = captcha_element.get_attribute('value')
                        if captcha_value and captcha_value.strip():
                            print(f"[OK] Captcha field contains text: '{captcha_value}' (length: {len(captcha_value)})")
                            logging.info(f"Manual captcha completed: '{captcha_value}'")
                            return True
                        else:
                            print("[WARN] Warning: Captcha field appears empty")
                            # Ask user if they want to continue anyway
                            from tkinter import messagebox
                            import tkinter as tk
                            
                            root = tk.Tk()
                            root.withdraw()
                            
                            continue_anyway = messagebox.askyesno(
                                "Captcha Field Empty",
                                "The captcha field appears to be empty.\n\n"
                                "Did you enter the captcha correctly?\n\n"
                                "Click 'Yes' to continue anyway\n"
                                "Click 'No' to try again",
                                parent=root
                            )
                            
                            root.destroy()
                            
                            if continue_anyway:
                                print("[OK] User chose to continue with empty captcha field")
                                return True
                            else:
                                print("-> User chose to retry captcha")
                                continue
                                
                    except Exception as e:
                        print(f"[WARN] Could not verify captcha field content: {e}")
                        # Continue anyway since user confirmed
                        return True
                else:
                    print("[FAIL] User cancelled or failed manual captcha")
                    
            except Exception as e:
                print(f"[FAIL] Manual captcha attempt {attempt + 1} failed: {e}")
                logging.error(f"Manual captcha error (attempt {attempt + 1}): {e}")
        
        print("[FAIL] All manual captcha attempts failed")
        logging.error("All manual captcha attempts failed")
        return False
    
    def search_tenders_manual(self) -> bool:
        """Submit search after manual captcha verification"""
        try:
            # Handle manual captcha
            print("[SEARCH] Starting manual captcha process...")
            if not self.handle_manual_captcha():
                print("[ERROR] Manual captcha verification failed")
                return False
            
            print("[SUCCESS] Manual captcha completed, proceeding with search...")
            
            # Small delay before clicking search
            time.sleep(2)
            
            # Find and click search button
            search_selectors = [
                (By.XPATH, "//input[@value='Search']"),
                (By.XPATH, "//button[contains(text(), 'Search')]"),
                (By.XPATH, "//input[@type='submit'][contains(@value, 'Search')]"),
                (By.ID, "searchButton"),
                (By.NAME, "search")
            ]
            
            search_button = None
            for by, value in search_selectors:
                try:
                    search_button = self.driver.find_element(by, value)
                    if search_button and search_button.is_displayed():
                        print(f"[OK] Found search button using: {by}='{value}'")
                        break
                except:
                    continue
            
            if not search_button:
                print("[ERROR] Search button not found")
                logging.error("Search button not found")
                return False
            
            # Scroll to search button if needed
            self.driver.execute_script("arguments[0].scrollIntoView(true);", search_button)
            time.sleep(0.5)
            
            # Click search button
            try:
                print("[SEARCH] Clicking search button...")
                search_button.click()
                logging.info("Search button clicked")
            except:
                # If normal click fails, try JavaScript click
                print("[SEARCH] Trying JavaScript click...")
                self.driver.execute_script("arguments[0].click();", search_button)
                logging.info("Search button clicked via JavaScript")
            
            # Wait for results with enhanced detection
            print("[WAIT] Waiting for search results...")
            results_found = False
            for attempt in range(5):
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.any_of(
                            EC.presence_of_element_located((By.CLASS_NAME, "list-table")),
                            EC.presence_of_element_located((By.XPATH, "//table")),
                            EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'tender')]")),
                            EC.presence_of_element_located((By.XPATH, "//td[contains(text(), 'Tender ID')]")),
                            EC.presence_of_element_located((By.XPATH, "//th[contains(text(), 'S.No')]"))
                        )
                    )
                    results_found = True
                    print("[SUCCESS] Search results loaded successfully!")
                    break
                except:
                    print(f"[WAIT] Results loading attempt {attempt + 1} failed, retrying...")
                    time.sleep(3)
            
            if not results_found:
                # Check for error messages
                try:
                    error_elements = self.driver.find_elements(By.XPATH, 
                        "//div[contains(@class, 'error')] | //span[contains(@class, 'error')] | "
                        "//div[contains(text(), 'error')] | //div[contains(text(), 'No records found')]")
                    if error_elements:
                        error_text = error_elements[0].text
                        print(f"[ERROR] Website error: {error_text}")
                        logging.error(f"Website error: {error_text}")
                        return False
                except:
                    pass
                
                print("[ERROR] No results found after search")
                logging.error("No results found after search")
                return False
            
            logging.info("Search completed successfully with manual captcha")
            return True
            
        except Exception as e:
            print(f"[ERROR] Error during search: {e}")
            logging.error(f"Error during search: {e}")
            return False
    
    def run_scraper_with_manual_captcha(self) -> bool:
        """Main method with manual captcha handling"""
        try:
            logging.info("[ROCKET] [START] Starting Enhanced Odisha Tender Scraper with Manual Captcha...")
            
            # Setup driver
            if not self.setup_driver():
                logging.error("[ERROR] Failed to setup browser driver")
                return False
            
            # Navigate to target URL
            logging.info("[NAV] Navigating to tender website...")
            self.driver.get(self.target_url)
            
            # Wait for page to load
            if not self.wait_for_element(By.NAME, "tenderStatus"):
                logging.error("[ERROR] Failed to load initial page")
                return False
            
            # Set tender status to AOC
            logging.info("[CONFIG] Setting tender status to AOC...")
            if not self.set_tender_status_aoc():
                logging.error("[ERROR] Failed to set tender status to AOC")
                return False
            
            # Search for tenders with manual captcha
            logging.info("[SEARCH] Starting search with manual captcha...")
            if not self.search_tenders_manual():
                logging.error("[ERROR] Failed to search for tenders")
                return False
            
            # Extract tender list
            logging.info("[EXTRACT] Extracting tender list...")
            tender_data = self.extract_tender_list()
            if not tender_data:
                logging.error("[ERROR] No tender data found")
                return False
            
            # Extract detailed information
            logging.info(f"[SEARCH] [DETAILS] Extracting detailed information for {len(tender_data)} tenders...")
            for i, tender in enumerate(tender_data):
                logging.info(f"Processing tender {i+1}/{len(tender_data)}: {tender['Tender ID']}")
                tender_data[i] = self.extract_tender_details(tender)
                time.sleep(self.config["delay_between_requests"])
            
            # Save to Excel
            logging.info("[SAVE] Saving data to Excel...")
            if self.save_to_excel_enhanced(tender_data):
                logging.info("[SUCCESS] Scraping completed successfully!")
                logging.info(f"[EXTRACT] Total records: {len(tender_data)}")
                logging.info(f"[FOLDER] Excel file: {self.excel_file}")
                logging.info(f"[FOLDER] Downloads folder: {self.download_folder}")
                return True
            else:
                logging.error("[ERROR] Failed to save data")
                return False
            
        except KeyboardInterrupt:
            logging.info("Scraping interrupted by user")
            return False
        except Exception as e:
            logging.error(f"[ERROR] Unexpected error during scraping: {e}")
            return False
        finally:
            if self.driver:
                self.driver.quit()
                logging.info("[CLOSED] Browser closed")
    
    def handle_gui_captcha(self) -> bool:
        """Handle captcha with GUI button integration"""
        max_attempts = 3
        
        for attempt in range(max_attempts):
            try:
                print(f"\n[CAPTCHA] GUI Captcha verification (attempt {attempt + 1}/{max_attempts})")
                
                # Check if captcha field exists and is visible
                captcha_element = None
                try:
                    captcha_element = self.driver.find_element(By.NAME, "captcha")
                    if captcha_element.is_displayed():
                        print("[OK] Captcha field found and is visible")
                    else:
                        print("[FAIL] Captcha field found but not visible")
                        continue
                except:
                    print("[FAIL] Captcha field not found")
                    continue
                
                # Show the captcha button in GUI if callback is available
                if self.gui_show_captcha_button:
                    print("Showing captcha button in GUI...")
                    self.gui_show_captcha_button()
                    
                    # Wait for user to complete captcha and click the GUI button
                    if self.gui_captcha_event:
                        print("[WAIT] Waiting for user to solve captcha and click GUI button...")
                        logging.info("Please solve the captcha in the browser and click 'Captcha Done' in the application")
                        
                        # Wait for the event to be set (user clicked the button)
                        self.gui_captcha_event.wait()
                        self.gui_captcha_event.clear()  # Reset for next use
                        
                        print("[SUCCESS] User confirmed captcha completion via GUI")
                        
                        # Optionally verify that captcha field has content
                        try:
                            captcha_value = captcha_element.get_attribute('value')
                            if captcha_value and captcha_value.strip():
                                print(f"[OK] Captcha field contains: '{captcha_value}' (length: {len(captcha_value)})")
                                logging.info(f"GUI captcha completed: '{captcha_value}'")
                                return True
                            else:
                                print("[WARN] Warning: Captcha field appears empty, but continuing as user confirmed")
                                logging.info("Captcha field empty but user confirmed completion")
                                return True
                        except Exception as e:
                            print(f"[WARN] Could not verify captcha field: {e}")
                            # Continue anyway since user confirmed via GUI
                            return True
                    else:
                        print("[FAIL] No GUI event available")
                        return False
                else:
                    print("[FAIL] No GUI callback available, falling back to manual method")
                    # Fallback to manual captcha handler
                    manual_handler = ManualCaptchaHandler(self.driver)
                    return manual_handler.wait_for_manual_captcha(attempt + 1, max_attempts)
                    
            except Exception as e:
                print(f"[FAIL] GUI captcha attempt {attempt + 1} failed: {e}")
                logging.error(f"GUI captcha error (attempt {attempt + 1}): {e}")
        
        print("[FAIL] All GUI captcha attempts failed")
        logging.error("All GUI captcha attempts failed")
        return False
    
    def search_tenders_gui(self) -> bool:
        """Submit search after GUI captcha verification"""
        try:
            # Handle GUI captcha
            print("[SEARCH] Starting GUI captcha process...")
            if not self.handle_gui_captcha():
                print("[ERROR] GUI captcha verification failed")
                return False
            
            print("[SUCCESS] GUI captcha completed, proceeding with search...")
            
            # Small delay before clicking search
            time.sleep(2)
            
            # Find and click search button
            search_selectors = [
                (By.XPATH, "//input[@value='Search']"),
                (By.XPATH, "//button[contains(text(), 'Search')]"),
                (By.XPATH, "//input[@type='submit'][contains(@value, 'Search')]"),
                (By.ID, "searchButton"),
                (By.NAME, "search")
            ]
            
            search_button = None
            for by, value in search_selectors:
                try:
                    search_button = self.driver.find_element(by, value)
                    if search_button and search_button.is_displayed():
                        print(f"[OK] Found search button using: {by}='{value}'")
                        break
                except:
                    continue
            
            if not search_button:
                print("[ERROR] Search button not found")
                logging.error("Search button not found")
                return False
            
            # Scroll to search button if needed
            self.driver.execute_script("arguments[0].scrollIntoView(true);", search_button)
            time.sleep(0.5)
            
            # Click search button
            try:
                print("[SEARCH] Clicking search button...")
                search_button.click()
                logging.info("Search button clicked")
            except:
                # If normal click fails, try JavaScript click
                print("[SEARCH] Trying JavaScript click...")
                self.driver.execute_script("arguments[0].click();", search_button)
                logging.info("Search button clicked via JavaScript")
            
            # Wait for results with enhanced detection
            print("[WAIT] Waiting for search results...")
            results_found = False
            for attempt in range(5):
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.any_of(
                            EC.presence_of_element_located((By.CLASS_NAME, "list-table")),
                            EC.presence_of_element_located((By.XPATH, "//table")),
                            EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'tender')]")),
                            EC.presence_of_element_located((By.XPATH, "//td[contains(text(), 'Tender ID')]")),
                            EC.presence_of_element_located((By.XPATH, "//th[contains(text(), 'S.No')]"))
                        )
                    )
                    results_found = True
                    print("[SUCCESS] Search results loaded successfully!")
                    break
                except:
                    print(f"[WAIT] Results loading attempt {attempt + 1} failed, retrying...")
                    time.sleep(3)
            
            if not results_found:
                # Check for error messages
                try:
                    error_elements = self.driver.find_elements(By.XPATH, 
                        "//div[contains(@class, 'error')] | //span[contains(@class, 'error')] | "
                        "//div[contains(text(), 'error')] | //div[contains(text(), 'No records found')]")
                    if error_elements:
                        error_text = error_elements[0].text
                        print(f"[ERROR] Website error: {error_text}")
                        logging.error(f"Website error: {error_text}")
                        return False
                except:
                    pass
                
                print("[ERROR] No results found after search")
                logging.error("No results found after search")
                return False
            
            logging.info("Search completed successfully with GUI captcha")
            return True
            
        except Exception as e:
            print(f"[ERROR] Error during search: {e}")
            logging.error(f"Error during search: {e}")
            return False
    
    def run_scraper_with_gui_captcha(self) -> bool:
        """Main method with GUI captcha handling"""
        try:
            logging.info("[GUI] [START] Starting Enhanced Odisha Tender Scraper with GUI Captcha...")
            
            # Setup driver
            if not self.setup_driver():
                logging.error("[ERROR] Failed to setup browser driver")
                return False
            
            # Navigate to target URL
            logging.info("[NAV] Navigating to tender website...")
            self.driver.get(self.target_url)
            
            # Wait for page to load
            if not self.wait_for_element(By.NAME, "tenderStatus"):
                logging.error("[ERROR] Failed to load initial page")
                return False
            
            # Set tender status to AOC
            logging.info("[CONFIG] Setting tender status to AOC...")
            if not self.set_tender_status_aoc():
                logging.error("[ERROR] Failed to set tender status to AOC")
                return False
            
            # Search for tenders with GUI captcha
            logging.info("[SEARCH] Starting search with GUI captcha...")
            if not self.search_tenders_gui():
                logging.error("[ERROR] Failed to search for tenders")
                return False
            
            # Extract tender list
            logging.info("[EXTRACT] Extracting tender list...")
            tender_data = self.extract_tender_list()
            if not tender_data:
                logging.error("[ERROR] No tender data found")
                return False
            
            # Extract detailed information
            logging.info(f"[SEARCH] [DETAILS] Extracting detailed information for {len(tender_data)} tenders...")
            for i, tender in enumerate(tender_data):
                logging.info(f"Processing tender {i+1}/{len(tender_data)}: {tender['Tender ID']}")
                tender_data[i] = self.extract_tender_details(tender)
                time.sleep(self.config["delay_between_requests"])
            
            # Save to Excel
            logging.info("[SAVE] Saving data to Excel...")
            if self.save_to_excel_enhanced(tender_data):
                logging.info("[SUCCESS] Scraping completed successfully!")
                logging.info(f"[EXTRACT] Total records: {len(tender_data)}")
                logging.info(f"[FOLDER] Excel file: {self.excel_file}")
                logging.info(f"[FOLDER] Downloads folder: {self.download_folder}")
                return True
            else:
                logging.error("[ERROR] Failed to save data")
                return False
            
        except KeyboardInterrupt:
            logging.info("Scraping interrupted by user")
            return False
        except Exception as e:
            logging.error(f"[ERROR] Unexpected error during scraping: {e}")
            return False
        finally:
            if self.driver:
                self.driver.quit()
                logging.info("[CLOSED] Browser closed")
    
    def set_max_records(self, max_records: int):
        """Set maximum number of records to scrape"""
        self.max_records = max_records
        logging.info(f"Max records set to: {max_records}")

    def extract_tender_list_paginated(self) -> List[Dict]:
        """Extract tender data with pagination support"""
        all_tender_data = []
        page_number = 1
        
        while len(all_tender_data) < self.max_records:
            try:
                logging.info(f"[PAGE] Processing page {page_number} (Records so far: {len(all_tender_data)}/{self.max_records})")
                
                # Extract data from current page
                page_data = self.extract_current_page_data()
                
                if not page_data:
                    logging.info("No more data found on current page")
                    break
                
                # Add to total data (limit to max_records)
                for tender in page_data:
                    if len(all_tender_data) >= self.max_records:
                        break
                    all_tender_data.append(tender)
                
                logging.info(f"Extracted {len(page_data)} records from page {page_number}")
                
                # Check if we have enough records
                if len(all_tender_data) >= self.max_records:
                    logging.info(f"Reached target of {self.max_records} records")
                    break
                
                # Try to go to next page
                if not self.go_to_next_page():
                    logging.info("No more pages available")
                    break
                    
                page_number += 1
                time.sleep(2)  # Brief pause between pages
                
            except Exception as e:
                logging.error(f"Error processing page {page_number}: {e}")
                break
        
        # Limit to max_records
        final_data = all_tender_data[:self.max_records]
        logging.info(f"Total records collected: {len(final_data)}")
        return final_data

    def extract_current_page_data(self) -> List[Dict]:
        """Extract tender data from current page"""
        tender_data = []
        
        try:
            # Wait for results to load
            time.sleep(3)
            
            # Debug: Check what's on the page
            page_source_snippet = self.driver.page_source[:1000]
            logging.info(f"Page source snippet: {page_source_snippet}")
            
            # Try to find any table on the page first
            all_tables = self.driver.find_elements(By.TAG_NAME, "table")
            logging.info(f"Found {len(all_tables)} table(s) on the page")
            
            # More comprehensive table selectors
            table_selectors = [
                "//table[contains(@class, 'list-table')]",
                "//table[.//th[contains(text(), 'Tender ID')]]",
                "//table[.//th[contains(text(), 'S.No')]]",
                "//table[.//td[contains(text(), 'Tender')]]",
                "//table[.//th[contains(text(), 'Title')]]",
                "//table[contains(@class, 'table')]",
                "//table[contains(@id, 'result')]",
                "//table[contains(@id, 'tender')]",
                "//table"  # Last resort: any table
            ]
            
            table = None
            successful_selector = None
            
            for selector in table_selectors:
                try:
                    tables = self.driver.find_elements(By.XPATH, selector)
                    for t in tables:
                        if t.is_displayed():
                            # Check if this table has data rows
                            rows = t.find_elements(By.TAG_NAME, "tr")
                            if len(rows) > 1:  # Has header + data rows
                                table = t
                                successful_selector = selector
                                logging.info(f"Found table with {len(rows)} rows using selector: {selector}")
                                break
                    if table:
                        break
                except Exception as e:
                    logging.debug(f"Selector {selector} failed: {e}")
                    continue
            
            if not table:
                logging.error("Could not find results table")
                
                # Debug: Save page source to file for inspection
                try:
                    with open("debug_page_source.html", "w", encoding="utf-8") as f:
                        f.write(self.driver.page_source)
                    logging.info("Saved page source to debug_page_source.html")
                except:
                    pass
                    
                return []
            
            # Get data rows (skip header)
            rows = table.find_elements(By.TAG_NAME, "tr")[1:]
            
            for i, row in enumerate(rows):
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) < 5:
                        continue
                    
                    tender_info = {
                        'S.No': self.safe_get_text(cells, 0),
                        'Tender ID': self.safe_get_text(cells, 1),
                        'Title and Ref.No.': self.safe_get_text(cells, 2),
                        'Organisation Chain': self.safe_get_text(cells, 3),
                        'Tender Stage': self.safe_get_text(cells, 4),
                        'Status': self.safe_get_text(cells, 5) if len(cells) > 5 else '<empty>',
                        'Status_Link': '<empty>',
                        'AOC_PDF_Link': '<empty>',
                        'AOC_PDF_File': '<empty>',
                        'Stage_Summary_Data': '<empty>',
                        'Contract_Value': '<empty>',
                        'Contractor_Name': '<empty>',
                        'Email': '<empty>',
                        'Mobile': '<empty>',
                        'GST_Number': '<empty>',
                        'PDF_Details': '<empty>'
                    }
                    
                    # Extract status link
                    try:
                        if len(cells) > 5:
                            status_cell = cells[5]
                            links = status_cell.find_elements(By.TAG_NAME, "a")
                            if links:
                                href = links[0].get_attribute('href')
                                if href:
                                    tender_info['Status_Link'] = href
                    except:
                        pass
                    
                    tender_data.append(tender_info)
                    
                except Exception as e:
                    logging.warning(f"Error processing row {i}: {e}")
                    continue
            
            return tender_data
            
        except Exception as e:
            logging.error(f"Error extracting current page data: {e}")
            return []

    def go_to_next_page(self) -> bool:
        """Navigate to next page of results"""
        try:
            # Look for "Next" button or pagination links
            next_selectors = [
                "//a[contains(text(), 'Next')]",
                "//a[contains(text(), 'next')]",
                "//a[contains(text(), '>>')]",
                "//a[contains(text(), '->')]",
                "//input[@value='Next']",
                "//button[contains(text(), 'Next')]"
            ]
            
            next_button = None
            for selector in next_selectors:
                try:
                    next_button = self.driver.find_element(By.XPATH, selector)
                    if next_button.is_displayed() and next_button.is_enabled():
                        break
                except:
                    continue
            
            if not next_button:
                # Try to find pagination with page numbers
                try:
                    # Look for the last visible page number and try next one
                    page_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, 'page=') or contains(@onclick, 'page')]")
                    if page_links:
                        # Find current page and get next
                        for link in page_links:
                            if 'current' in link.get_attribute('class') or 'active' in link.get_attribute('class'):
                                # Found current page, try to find next
                                continue
                        # If no specific next found, try the last pagination link
                        if page_links:
                            next_button = page_links[-1]
                except:
                    pass
            
            if next_button:
                # Scroll to next button
                self.driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
                time.sleep(1)
                
                # Click next button
                try:
                    next_button.click()
                except:
                    self.driver.execute_script("arguments[0].click();", next_button)
                
                # Wait for page to load
                time.sleep(3)
                
                # Verify page changed (look for loading or new content)
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//table"))
                    )
                    logging.info("[SUCCESS] Successfully navigated to next page")
                    return True
                except:
                    logging.warning("Page may not have changed after clicking next")
                    return False
            else:
                logging.info("No next page button found")
                return False
                
        except Exception as e:
            logging.error(f"Error navigating to next page: {e}")
            return False

    def extract_aoc_details_enhanced(self, tender_info: Dict) -> Dict:
        """Enhanced extraction focusing on AOC-specific data and PDFs"""
        if tender_info['Status_Link'] == '<empty>' or not tender_info['Status_Link']:
            logging.info(f"No status link for tender {tender_info['Tender ID']}")
            return tender_info
        
        original_window = self.driver.current_window_handle
        
        try:
            # Navigate to details page
            self.driver.get(tender_info['Status_Link'])
            time.sleep(3)
            
            # Extract AOC-specific information
            self.extract_aoc_contract_details(tender_info)
            
            # Extract contractor information
            self.extract_contractor_details(tender_info)
            
            # Download AOC PDFs (priority focus)
            self.download_aoc_pdfs(tender_info)
            
            # Extract stage summary data
            self.extract_stage_summary(tender_info)
            
            # Try to find and click stage summary details link
            self.extract_detailed_stage_summary(tender_info)
            
            logging.info(f"Successfully extracted AOC details for tender {tender_info['Tender ID']}")
            
        except Exception as e:
            logging.error(f"Error extracting AOC details for {tender_info['Tender ID']}: {e}")
        
        finally:
            # Ensure we're back to the original window
            try:
                self.driver.switch_to.window(original_window)
            except:
                pass
        
        return tender_info

    def extract_aoc_contract_details(self, tender_info: Dict):
        """Extract contract value and other AOC-specific details"""
        try:
            logging.info(f"[DEBUG] Starting contract value extraction for tender: {tender_info.get('Tender ID', 'Unknown')}")
            
            # Debug: Check if page contains relevant keywords
            try:
                page_text = self.driver.page_source.lower()
                if 'contract' in page_text:
                    logging.info("[DEBUG] Found 'contract' text in page")
                if 'value' in page_text:
                    logging.info("[DEBUG] Found 'value' text in page")
                if 'inr' in page_text or '₹' in page_text:
                    logging.info("[DEBUG] Found currency indicators in page")
                if 'aoc' in page_text:
                    logging.info("[DEBUG] Found 'AOC' text in page")
            except:
                pass
                
            # Priority 1: Extract from AOC table (most comprehensive)
            aoc_amount_selectors = [
                # Exact match patterns
                "//table[contains(.//text(), 'AOC')]//td[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'contract value')]/../td[position()=2]",
                "//table[contains(.//text(), 'AOC')]//td[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'contract value :')]/../td[position()=2]",
                # AOC section currency patterns
                "//h3[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'aoc')]/..//table//td[contains(text(), 'INR') or contains(text(), '₹')]",
                "//table[contains(.//text(), 'AOC')]//td[contains(text(), 'INR') or contains(text(), '₹')]",
                # Broader AOC patterns
                "//table[.//td[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'aoc')]]//td[contains(text(), 'INR') or contains(text(), '₹')]"
            ]
            
            # Try AOC-specific selectors first
            contract_found = False
            for i, selector in enumerate(aoc_amount_selectors):
                try:
                    logging.info(f"[DEBUG] Trying AOC amount selector {i+1}: {selector[:60]}...")
                    elements = self.driver.find_elements(By.XPATH, selector)
                    logging.info(f"[DEBUG] Found {len(elements)} elements with AOC selector {i+1}")
                    
                    for j, element in enumerate(elements[:5]):  # Check first 5 elements
                        try:
                            text = element.text.strip()
                            logging.info(f"[DEBUG] AOC amount element {j+1} text: '{text}'")
                            
                            if text and any(char.isdigit() for char in text):
                                # Clean up the amount but preserve INR prefix
                                import re
                                if 'INR' in text.upper():
                                    tender_info['Contract_Value'] = text
                                else:
                                    amount = re.sub(r'[^\d.,]', '', text)
                                    if amount:
                                        tender_info['Contract_Value'] = f"INR {amount}"
                                contract_found = True
                                logging.info(f"[SUCCESS] Found contract value from AOC table: '{tender_info['Contract_Value']}'")
                                break
                        except Exception as elem_e:
                            logging.debug(f"[DEBUG] Error processing AOC amount element {j+1}: {elem_e}")
                            continue
                    if contract_found:
                        break
                except Exception as e:
                    logging.debug(f"[DEBUG] AOC amount selector {i+1} failed: {e}")
                    continue
            
            # Priority 2: General amount selectors as fallback
            if not contract_found:
                logging.info("[DEBUG] Trying fallback amount selectors...")
                amount_selectors = [
                    "//td[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'contract value')]/../td[position()=2]",
                    "//td[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'awarded value')]/../td[position()=2]",
                    "//td[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'amount')]/../td[position()=2]",
                    "//td[contains(text(), 'INR') or contains(text(), '₹')]",
                    # Look for any cell with currency and numbers
                    "//td[contains(text(), 'INR') and contains(text(), ',')]",  # INR with comma-separated numbers
                    "//td[text()[contains(., 'INR') and string-length(.) > 8]]"  # INR with reasonable length
                ]
            
                for i, selector in enumerate(amount_selectors):
                    try:
                        logging.info(f"[DEBUG] Trying fallback amount selector {i+1}: {selector[:50]}...")
                        elements = self.driver.find_elements(By.XPATH, selector)
                        logging.info(f"[DEBUG] Found {len(elements)} elements with fallback selector {i+1}")
                        
                        for j, element in enumerate(elements[:10]):  # Check first 10
                            try:
                                text = element.text.strip()
                                logging.info(f"[DEBUG] Fallback amount element {j+1} text: '{text}'")
                                
                                if text and any(char.isdigit() for char in text):
                                    # Clean up the amount but preserve formatting
                                    import re
                                    if 'INR' in text.upper():
                                        tender_info['Contract_Value'] = text
                                    else:
                                        amount = re.sub(r'[^\d.,]', '', text)
                                        if amount:
                                            tender_info['Contract_Value'] = f"INR {amount}"
                                    contract_found = True
                                    logging.info(f"[SUCCESS] Found contract value via fallback: '{tender_info['Contract_Value']}'")
                                    break
                            except Exception as elem_e:
                                logging.debug(f"[DEBUG] Error processing fallback amount element {j+1}: {elem_e}")
                                continue
                                
                        if contract_found:
                            break
                    except Exception as e:
                        logging.debug(f"[DEBUG] Fallback amount selector {i+1} failed: {e}")
                        continue
            
            if not contract_found:
                logging.warning(f"[WARNING] No contract value found for tender {tender_info.get('Tender ID', 'Unknown')}")
            
            if contract_found:
                logging.info(f"[FINAL] Contract value extracted: {tender_info['Contract_Value']}")
            else:
                logging.info(f"[FINAL] No contract value found")
            
        except Exception as e:
            logging.error(f"[ERROR] Could not extract contract details: {e}")
            import traceback
            logging.debug(f"[TRACEBACK] {traceback.format_exc()}")

    def extract_contractor_details(self, tender_info: Dict):
        """Extract contractor name, email, mobile, GST details with enhanced debugging"""
        try:
            logging.info(f"[DEBUG] Starting contractor extraction for tender: {tender_info.get('Tender ID', 'Unknown')}")
            
            # Add debug: Print page source snippet to understand structure
            try:
                page_text = self.driver.page_source.lower()
                if 'awarded' in page_text:
                    logging.info("[DEBUG] Found 'awarded' text in page")
                if 'bidder' in page_text:
                    logging.info("[DEBUG] Found 'bidder' text in page")
                if 'contractor' in page_text:
                    logging.info("[DEBUG] Found 'contractor' text in page")
            except:
                pass
            
            # Priority 1: More comprehensive Awarded Bids List extraction
            awarded_bids_selectors = [
                # Look for any table with "Awarded" or "Bidder" in headers
                "//table[.//th[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'bidder name')]]//tr[position()>1]/td[position()=3]",
                "//table[.//th[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'contractor')]]//tr[position()>1]/td[position()=2]",
                "//table[contains(.//text(), 'Awarded')]//tr[position()>1]/td[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'name') or position()=3]",
                "//h3[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'awarded')]/..//table//tr[position()>1]/td[position()=3]",
                # Broader selectors
                "//table//th[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'bidder name')]/../../..//tr[position()>1]/td[position()=3]",
                "//table//td[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'bidder name')]/../td[position()=2]"
            ]
            
            contractor_found = False
            for i, selector in enumerate(awarded_bids_selectors):
                try:
                    logging.info(f"[DEBUG] Trying awarded bids selector {i+1}: {selector[:50]}...")
                    elements = self.driver.find_elements(By.XPATH, selector)
                    logging.info(f"[DEBUG] Found {len(elements)} elements with selector {i+1}")
                    
                    for j, element in enumerate(elements[:5]):  # Check first 5 elements
                        try:
                            text = element.text.strip()
                            logging.info(f"[DEBUG] Element {j+1} text: '{text}'")
                            
                            # More robust validation
                            if (text and len(text) > 3 and 
                                text not in ['Bidder Name', 'Contractor', 'Name', 'S.No', 'Sl No'] and
                                not text.isdigit() and
                                not text.startswith('http') and
                                ' ' in text):  # Names usually have spaces
                                
                                tender_info['Contractor_Name'] = text
                                contractor_found = True
                                logging.info(f"[SUCCESS] Found contractor from Awarded Bids List: '{text}'")
                                break
                        except Exception as elem_e:
                            logging.debug(f"[DEBUG] Error processing element {j+1}: {elem_e}")
                            continue
                    
                    if contractor_found:
                        break
                        
                except Exception as e:
                    logging.debug(f"[DEBUG] Awarded bids selector {i+1} failed: {e}")
                    continue
            
            # Priority 2: Fallback to general contractor/bidder selectors
            if not contractor_found:
                logging.info("[DEBUG] Trying fallback contractor selectors...")
                contractor_selectors = [
                    "//td[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'contractor')]/../td[position()=2]",
                    "//td[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'bidder')]/../td[position()=2]",
                    "//td[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'awarded to')]/../td[position()=2]",
                    "//td[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'winner')]/../td[position()=2]",
                    # Try any cell that looks like a name next to contractor-related text
                    "//td[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'name')]/following-sibling::td[1]",
                    "//td[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'name')]/preceding-sibling::td[1]"
                ]
                
                for i, selector in enumerate(contractor_selectors):
                    try:
                        logging.info(f"[DEBUG] Trying fallback selector {i+1}: {selector[:50]}...")
                        element = self.driver.find_element(By.XPATH, selector)
                        if element and element.text.strip():
                            text = element.text.strip()
                            if len(text) > 3 and ' ' in text:  # Basic name validation
                                tender_info['Contractor_Name'] = text
                                logging.info(f"[SUCCESS] Found contractor via fallback: '{text}'")
                                contractor_found = True
                                break
                    except Exception as e:
                        logging.debug(f"[DEBUG] Fallback selector {i+1} failed: {e}")
                        continue
            
            # Priority 3: Extract from any table cell that looks like a person's name
            if not contractor_found:
                logging.info("[DEBUG] Trying generic name pattern extraction...")
                try:
                    # Look for cells containing names (multiple words, proper case)
                    name_candidates = self.driver.find_elements(By.XPATH, "//td[string-length(text()) > 10 and contains(text(), ' ')]")
                    logging.info(f"[DEBUG] Found {len(name_candidates)} potential name candidates")
                    
                    for candidate in name_candidates[:20]:  # Check first 20
                        try:
                            text = candidate.text.strip()
                            # Check if it looks like a person's name
                            if (text and len(text.split()) >= 2 and len(text.split()) <= 5 and
                                text[0].isupper() and  # Starts with capital
                                any(word[0].isupper() for word in text.split()) and  # Has capital letters
                                not any(char.isdigit() for char in text) and  # No numbers
                                not text.startswith('http') and  # Not a URL
                                'tender' not in text.lower() and
                                'date' not in text.lower() and
                                'department' not in text.lower()):
                                
                                tender_info['Contractor_Name'] = text
                                logging.info(f"[SUCCESS] Found contractor via pattern matching: '{text}'")
                                contractor_found = True
                                break
                        except:
                            continue
                except Exception as e:
                    logging.debug(f"[DEBUG] Generic pattern extraction failed: {e}")
            
            if not contractor_found:
                logging.warning(f"[WARNING] No contractor found for tender {tender_info.get('Tender ID', 'Unknown')}")
            
            # Look for email
            email_selectors = [
                "//td[contains(text(), 'Email')]/../td[2]",
                "//a[contains(@href, 'mailto:')]"
            ]
            
            for selector in email_selectors:
                try:
                    element = self.driver.find_element(By.XPATH, selector)
                    if element:
                        email = element.text.strip() if 'mailto:' not in selector else element.get_attribute('href').replace('mailto:', '')
                        if '@' in email:
                            tender_info['Email'] = email
                            break
                except:
                    continue
            
            # Look for mobile/phone
            mobile_selectors = [
                "//td[contains(text(), 'Mobile')]/../td[2]",
                "//td[contains(text(), 'Phone')]/../td[2]",
                "//td[contains(text(), 'Contact')]/../td[2]"
            ]
            
            for selector in mobile_selectors:
                try:
                    element = self.driver.find_element(By.XPATH, selector)
                    if element:
                        mobile = element.text.strip()
                        if any(char.isdigit() for char in mobile):
                            tender_info['Mobile'] = mobile
                            break
                except:
                    continue
            
            # Look for GST number
            gst_selectors = [
                "//td[contains(text(), 'GST')]/../td[2]",
                "//td[contains(text(), 'GSTIN')]/../td[2]",
                "//td[contains(text(), 'Tax')]/../td[2]"
            ]
            
            for selector in gst_selectors:
                try:
                    element = self.driver.find_element(By.XPATH, selector)
                    if element:
                        gst = element.text.strip()
                        if len(gst) >= 10:  # GST numbers are typically 15 characters
                            tender_info['GST_Number'] = gst
                            break
                except:
                    continue
            
            logging.debug(f"Contractor details - Name: {tender_info['Contractor_Name']}, Email: {tender_info['Email']}")
            
        except Exception as e:
            logging.error(f"[ERROR] Could not extract contractor details: {e}")
            import traceback
            logging.debug(f"[TRACEBACK] {traceback.format_exc()}")

    def download_aoc_pdfs(self, tender_info: Dict):
        """Download AOC-specific PDFs with enhanced detection and debugging"""
        try:
            logging.info(f"[DEBUG] Starting AOC PDF extraction for tender: {tender_info.get('Tender ID', 'Unknown')}")
            
            # Debug: Check if page contains PDF-related keywords
            try:
                page_text = self.driver.page_source.lower()
                if '.pdf' in page_text:
                    logging.info("[DEBUG] Found '.pdf' text in page")
                if 'document' in page_text:
                    logging.info("[DEBUG] Found 'document' text in page")
                if 'download' in page_text:
                    logging.info("[DEBUG] Found 'download' text in page")
            except:
                pass
            # Look for AOC-specific PDF links (like the one circled in your image)
            aoc_pdf_selectors = [
                "//a[contains(@href, '.pdf') and contains(text(), 'AOC')]",
                "//a[contains(@href, '.pdf') and contains(@onclick, 'AOC')]",
                "//a[contains(@href, '.pdf')][contains(preceding-sibling::text(), 'AOC')]",
                "//a[contains(@href, '.pdf')][contains(following-sibling::text(), 'AOC')]",
                "//td[contains(text(), 'AOC')]//a[contains(@href, '.pdf')]",
                "//tr[contains(.//text(), 'AOC')]//a[contains(@href, '.pdf')]"
            ]
            
            aoc_pdf_found = False
            
            # First priority: Find AOC-specific PDFs
            for selector in aoc_pdf_selectors:
                try:
                    aoc_links = self.driver.find_elements(By.XPATH, selector)
                    for link in aoc_links:
                        try:
                            if link.is_displayed():
                                href = link.get_attribute('href')
                                if href and '.pdf' in href.lower():
                                    tender_info['AOC_PDF_Link'] = href
                                    # Store the link text/filename as well
                                    link_text = link.text.strip() if link.text else ''
                                    if link_text:
                                        tender_info['AOC_PDF_File'] = link_text
                                    
                                    # Download the AOC PDF
                                    filename = self.download_pdf_file(href, tender_info['Tender ID'], 'AOC')
                                    if filename:
                                        # If download successful, use downloaded filename
                                        tender_info['AOC_PDF_File'] = filename
                                    elif link_text:
                                        # If download failed but we have link text, use that
                                        tender_info['AOC_PDF_File'] = link_text
                                    
                                    aoc_pdf_found = True
                                    logging.info(f"[SUCCESS] Found AOC PDF link: {href} ({link_text})")
                                    break
                        except Exception as link_e:
                            logging.debug(f"[DEBUG] Error processing PDF link: {link_e}")
                            continue
                    if aoc_pdf_found:
                        break
                except Exception as e:
                    logging.debug(f"[DEBUG] Error with PDF selector: {e}")
                    continue
            
            # Second priority: General PDF links
            if not aoc_pdf_found:
                general_pdf_selectors = [
                    "//a[contains(@href, '.pdf')]",
                    "//a[contains(text(), 'PDF')]",
                    "//a[contains(text(), 'Download')]",
                    "//a[contains(text(), 'Document')]"
                ]
                
                pdf_links = []
                for selector in general_pdf_selectors:
                    try:
                        links = self.driver.find_elements(By.XPATH, selector)
                        pdf_links.extend(links)
                    except:
                        continue
                
                # Remove duplicates and download
                unique_links = []
                seen_hrefs = set()
                for link in pdf_links:
                    href = link.get_attribute('href')
                    if href and href not in seen_hrefs and '.pdf' in href.lower():
                        unique_links.append(href)
                        seen_hrefs.add(href)
                
                if unique_links:
                    downloaded_files = []
                    for i, pdf_url in enumerate(unique_links[:3]):  # Limit to 3 PDFs
                        filename = self.download_pdf_file(pdf_url, tender_info['Tender ID'], f'doc{i+1}')
                        if filename:
                            downloaded_files.append(filename)
                    
                    if downloaded_files:
                        tender_info['PDF_Details'] = " | ".join(downloaded_files)
                        if not aoc_pdf_found and downloaded_files:
                            # Use first PDF as AOC PDF if no specific AOC PDF found
                            tender_info['AOC_PDF_File'] = downloaded_files[0]
                    else:
                        tender_info['PDF_Details'] = '<download_failed>'
            
            if not aoc_pdf_found and tender_info['AOC_PDF_File'] == '<empty>':
                logging.warning(f"No AOC PDF found for tender {tender_info['Tender ID']}")
            
        except Exception as e:
            logging.error(f"[ERROR] Error downloading AOC PDFs for {tender_info['Tender ID']}: {e}")
            import traceback
            logging.debug(f"[TRACEBACK] {traceback.format_exc()}")

    def save_to_excel_format_compliant(self, tender_data: List[Dict]) -> bool:
        """Save data to Excel following the exact format from FORMAT AUGUST 2025.xlsx"""
        try:
            if not tender_data:
                logging.error("No data to save")
                return False
            
            # Prepare data in the exact format required
            formatted_data = []
            
            for i, tender in enumerate(tender_data):
                # Map to the exact column structure from FORMAT AUGUST 2025.csv
                # Note: "AMOUNT " and "Details " have trailing spaces in the CSV header
                formatted_record = {
                    'SL NO': i + 1,
                    'NAME OF CONTRACTOR': tender.get('Contractor_Name', ''),
                    'EMAIL': tender.get('Email', ''),
                    'MOBILE NO': tender.get('Mobile', ''),
                    'CONTACT DETAILS': '',  # Additional contact info
                    'JSW CONTACT NO': '',   # Specific to JSW, leave empty
                    'GST NUMBER': tender.get('GST_Number', ''),
                    'REMARK': '',           # For manual notes
                    'Customer Category': '', # Classification
                    'FOLLOW UP DATE': datetime.now().strftime('%Y-%m-%d'),
                    'DESCRIPTION': tender.get('Title and Ref.No.', ''),
                    'AMOUNT ': tender.get('Contract_Value', ''),  # Note trailing space to match CSV
                    'COMMITTEE CHAIRPERSON': self.extract_chairperson_from_org(tender.get('Organisation Chain', '')),
                    'ORGANISATION': tender.get('Organisation Chain', ''),
                    'TENDER ID': tender.get('Tender ID', ''),
                    'LAST ENTRY DATE': datetime.now().strftime('%Y-%m-%d'),
                    'EXISTING CUSTOMER': '',  # For tracking
                    'Details ': self.format_details_column(tender)  # Combined details with trailing space to match CSV
                }
                
                formatted_data.append(formatted_record)
            
            # Create DataFrame
            df = pd.DataFrame(formatted_data)
            
            # Save to Excel with proper formatting in the configured output directory
            output_dir = self.config.get('download_folder', self.download_folder)
            # Ensure output directory exists
            os.makedirs(output_dir, exist_ok=True)
            excel_path = os.path.join(output_dir, os.path.basename(self.excel_file))
            
            with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='AOC', index=False)
                
                # Get workbook and worksheet for formatting
                workbook = writer.book
                worksheet = writer.sheets['AOC']
                
                # Auto-adjust column widths
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)  # Cap at 50 characters
                    worksheet.column_dimensions[column_letter].width = adjusted_width
                
                # Add header formatting
                for cell in worksheet[1]:
                    cell.font = cell.font.copy(bold=True)
                    cell.fill = cell.fill.copy(fgColor="DDDDDD")
            
            # Save summary with enhanced stats
            summary = {
                'timestamp': datetime.now().isoformat(),
                'total_records': len(tender_data),
                'records_with_aoc_pdfs': len([t for t in tender_data if t.get('AOC_PDF_File', '<empty>') != '<empty>']),
                'records_with_contractor_info': len([t for t in tender_data if t.get('Contractor_Name', '<empty>') != '<empty>']),
                'records_with_contract_value': len([t for t in tender_data if t.get('Contract_Value', '<empty>') != '<empty>']),
                'records_with_email': len([t for t in tender_data if t.get('Email', '<empty>') != '<empty>']),
                'max_records_requested': self.max_records
            }
            
            # Save summary in the same output directory
            summary_path = os.path.join(output_dir, f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            with open(summary_path, 'w') as f:
                json.dump(summary, f, indent=2)
            
            logging.info(f"[SUCCESS] Data saved to {excel_path} in FORMAT AUGUST 2025 compliance")
            # Update excel_file path for return reference
            self.excel_file = excel_path
            logging.info(f"[EXTRACT] Summary: {summary}")
            return True
            
        except Exception as e:
            logging.error(f"Error saving to Excel: {e}")
            return False

    def extract_chairperson_from_org(self, org_chain: str) -> str:
        """Extract chairperson/committee head from organization chain"""
        try:
            # Look for common patterns in organization chains
            if '||' in org_chain:
                parts = org_chain.split('||')
                # Usually the last part contains the most specific role
                for part in reversed(parts):
                    if any(keyword in part.lower() for keyword in ['chairperson', 'chairman', 'head', 'director', 'chief']):
                        return part.strip()
                # If no specific role found, return the last part
                return parts[-1].strip() if parts else '<empty>'
            else:
                return org_chain.strip() if org_chain else '<empty>'
        except:
            return '<empty>'
    
    def format_details_column(self, tender: Dict) -> str:
        """Format the Details column with all available information"""
        details_parts = []
        
        # Add AOC PDF link if available
        aoc_pdf = tender.get('AOC_PDF_File', '')
        aoc_link = tender.get('AOC_PDF_Link', '')
        if aoc_pdf:
            if aoc_link:
                details_parts.append(f"AOC_PDF: {aoc_pdf} ({aoc_link})")
            else:
                details_parts.append(f"AOC_PDF: {aoc_pdf}")
        
        # Add status link if available
        status_link = tender.get('Status_Link', '')
        if status_link:
            details_parts.append(f"STATUS_LINK: {status_link}")
        
        # Add stage summary if available
        stage_summary = tender.get('Stage_Summary_Data', '')
        if stage_summary:
            details_parts.append(f"STAGE: {stage_summary[:100]}...")  # Truncate if too long
        
        # Add contract value if available
        contract_value = tender.get('Contract_Value', '')
        if contract_value:
            details_parts.append(f"CONTRACT: {contract_value}")
        
        # Join all parts with separator
        return ' | '.join(details_parts) if details_parts else ''

    def run_scraper_paginated(self) -> bool:
        """Main method with pagination support and format compliance"""
        try:
            logging.info(f"[ROCKET] [START] Starting Enhanced Odisha Tender Scraper (Target: {self.max_records} records)...")
            
            # Setup driver
            if not self.setup_driver():
                logging.error("[ERROR] Failed to setup browser driver")
                return False
            
            # Navigate to target URL
            logging.info("[NAV] Navigating to tender website...")
            self.driver.get(self.target_url)
            
            # Wait for page to load
            if not self.wait_for_element(By.NAME, "tenderStatus"):
                logging.error("[ERROR] Failed to load initial page")
                return False
            
            # Set tender status to AOC
            logging.info("[CONFIG] Setting tender status to AOC...")
            if not self.set_tender_status_aoc():
                logging.error("[ERROR] Failed to set tender status to AOC")
                return False
            
            # Search for tenders with manual captcha
            logging.info("[SEARCH] Starting search with manual captcha...")
            if not self.search_tenders_manual():
                logging.error("[ERROR] Failed to search for tenders")
                return False
            
            # Extract tender list with pagination
            logging.info(f"[EXTRACT] Extracting tender list with pagination (up to {self.max_records} records)...")
            tender_data = self.extract_tender_list_paginated()
            if not tender_data:
                logging.error("[ERROR] No tender data found")
                return False
            
            # Extract detailed AOC information
            logging.info(f"[SEARCH] [DETAILS] Extracting detailed AOC information for {len(tender_data)} tenders...")
            for i, tender in enumerate(tender_data):
                logging.info(f"Processing tender {i+1}/{len(tender_data)}: {tender['Tender ID']}")
                tender_data[i] = self.extract_aoc_details_enhanced(tender)
                time.sleep(self.config["delay_between_requests"])
            
            # Save to Excel in format-compliant structure
            logging.info("[SAVE] Saving data to Excel in FORMAT AUGUST 2025 compliance...")
            if self.save_to_excel_format_compliant(tender_data):
                logging.info("[SUCCESS] Scraping completed successfully!")
                logging.info(f"[EXTRACT] Total records: {len(tender_data)}")
                logging.info(f"[FOLDER] Excel file: {self.excel_file}")
                logging.info(f"[FOLDER] Downloads folder: {self.download_folder}")
                return True
            else:
                logging.error("[ERROR] Failed to save data")
                return False
            
        except KeyboardInterrupt:
            logging.info("Scraping interrupted by user")
            return False
        except Exception as e:
            logging.error(f"[ERROR] Unexpected error during scraping: {e}")
            return False
        finally:
            if self.driver:
                self.driver.quit()
                logging.info("[CLOSED] Browser closed")
    
    def run_scraper_paginated_with_gui_captcha(self) -> bool:
        """Main method with pagination support and GUI captcha handling"""
        try:
            logging.info(f"🚀 [START] Starting Enhanced Odisha Tender Scraper with GUI Captcha (Target: {self.max_records} records)...")
            
            # Setup driver
            if not self.setup_driver():
                logging.error("❌ Failed to setup browser driver")
                return False
            
            # Navigate to target URL
            logging.info("📡 [NAV] Navigating to tender website...")
            self.driver.get(self.target_url)
            
            # Wait for page to load
            if not self.wait_for_element(By.NAME, "tenderStatus"):
                logging.error("❌ Failed to load initial page")
                return False
            
            # Set tender status to AOC
            logging.info("⚙️ [CONFIG] Setting tender status to AOC...")
            if not self.set_tender_status_aoc():
                logging.error("❌ Failed to set tender status to AOC")
                return False
            
            # Search for tenders with GUI captcha
            logging.info("🔍 [SEARCH] Starting search with GUI captcha...")
            if not self.search_tenders_gui():
                logging.error("❌ Failed to search for tenders")
                return False
            
            # Extract tender list with pagination
            logging.info(f"📊 [EXTRACT] Extracting tender list with pagination (up to {self.max_records} records)...")
            tender_data = self.extract_tender_list_paginated()
            if not tender_data:
                logging.error("❌ No tender data found")
                return False
            
            # Extract detailed AOC information
            logging.info(f"🔍 [DETAILS] Extracting detailed AOC information for {len(tender_data)} tenders...")
            for i, tender in enumerate(tender_data):
                logging.info(f"Processing tender {i+1}/{len(tender_data)}: {tender['Tender ID']}")
                tender_data[i] = self.extract_aoc_details_enhanced(tender)
                time.sleep(self.config["delay_between_requests"])
            
            # Save to Excel in format-compliant structure
            logging.info("💾 [SAVE] Saving data to Excel in FORMAT AUGUST 2025 compliance...")
            if self.save_to_excel_format_compliant(tender_data):
                logging.info("✅ [SUCCESS] Scraping completed successfully!")
                logging.info(f"📊 Total records: {len(tender_data)}")
                logging.info(f"📁 Excel file: {self.excel_file}")
                logging.info(f"📁 Downloads folder: {self.download_folder}")
                return True
            else:
                logging.error("❌ Failed to save data")
                return False
            
        except KeyboardInterrupt:
            logging.info("⏹️ Scraping interrupted by user")
            return False
        except Exception as e:
            logging.error(f"❌ Unexpected error during scraping: {e}")
            return False
        finally:
            if self.driver:
                self.driver.quit()
                logging.info("🔒 Browser closed")
    
    def set_tender_status_aoc(self) -> bool:
        """Set tender status to AOC with retry logic"""
        for attempt in range(self.config["max_retries"]):
            try:
                dropdown = self.wait_for_element(By.NAME, "tenderStatus")
                if not dropdown:
                    continue
                
                select = Select(dropdown)
                
                # Try different possible values for AOC
                aoc_values = ["AOC", "aoc", "AOC_STATUS", "ACCEPTED"]
                
                for value in aoc_values:
                    try:
                        select.select_by_value(value)
                        logging.info(f"Tender status set to AOC (value: {value})")
                        return True
                    except:
                        try:
                            select.select_by_visible_text(value)
                            logging.info(f"Tender status set to AOC (text: {value})")
                            return True
                        except:
                            continue
                
                # If direct selection fails, try selecting by index or visible text
                options = select.options
                for option in options:
                    if "AOC" in option.text.upper():
                        select.select_by_visible_text(option.text)
                        logging.info(f"Tender status set to: {option.text}")
                        return True
                
                logging.warning(f"AOC selection attempt {attempt + 1} failed")
                time.sleep(2)
                
            except Exception as e:
                logging.error(f"Error setting tender status (attempt {attempt + 1}): {e}")
        
        return False
    
    def search_tenders(self) -> bool:
        """Submit search with enhanced error handling"""
        try:
            # Handle captcha
            if not self.handle_captcha_enhanced():
                return False
            
            # Small delay before clicking search
            time.sleep(2)
            
            # Find and click search button with multiple selectors
            search_selectors = [
                (By.XPATH, "//input[@value='Search']"),
                (By.XPATH, "//button[contains(text(), 'Search')]"),
                (By.XPATH, "//input[@type='submit'][contains(@value, 'Search')]"),
                (By.ID, "searchButton"),
                (By.NAME, "search")
            ]
            
            search_button = None
            for by, value in search_selectors:
                try:
                    search_button = self.driver.find_element(by, value)
                    if search_button and search_button.is_displayed():
                        break
                except:
                    continue
            
            if not search_button:
                logging.error("Search button not found")
                return False
            
            # Scroll to search button if needed
            self.driver.execute_script("arguments[0].scrollIntoView(true);", search_button)
            time.sleep(0.5)
            
            # Click search button
            try:
                search_button.click()
                logging.info("Search button clicked")
            except:
                # If normal click fails, try JavaScript click
                self.driver.execute_script("arguments[0].click();", search_button)
                logging.info("Search button clicked via JavaScript")
            
            # Wait for results with enhanced detection
            results_found = False
            for attempt in range(5):  # Increased attempts
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.any_of(
                            EC.presence_of_element_located((By.CLASS_NAME, "list-table")),
                            EC.presence_of_element_located((By.XPATH, "//table")),
                            EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'tender')]")),
                            EC.presence_of_element_located((By.XPATH, "//td[contains(text(), 'Tender ID')]")),
                            EC.presence_of_element_located((By.XPATH, "//th[contains(text(), 'S.No')]"))
                        )
                    )
                    results_found = True
                    break
                except:
                    logging.warning(f"Results loading attempt {attempt + 1} failed, retrying...")
                    time.sleep(3)
            
            if not results_found:
                # Check if there's an error message or no results
                try:
                    error_elements = self.driver.find_elements(By.XPATH, 
                        "//div[contains(@class, 'error')] | //span[contains(@class, 'error')] | "
                        "//div[contains(text(), 'error')] | //div[contains(text(), 'No records found')]")
                    if error_elements:
                        error_text = error_elements[0].text
                        logging.error(f"Website error/message: {error_text}")
                        return False
                except:
                    pass
                
                logging.error("No results found after search - possibly incorrect captcha or no data available")
                return False
            
            logging.info("Search completed successfully")
            return True
            
        except Exception as e:
            logging.error(f"Error during search: {e}")
            return False
    
    def extract_tender_list(self) -> List[Dict]:
        """Extract tender data with improved parsing"""
        tender_data = []
        
        try:
            # Try multiple table selectors
            table_selectors = [
                "//table[contains(@class, 'list-table')]",
                "//table[contains(@class, 'tender')]",
                "//table[.//th[contains(text(), 'Tender ID')]]",
                "//table[.//th[contains(text(), 'S.No')]]",
                "//table[.//td[contains(text(), 'Tender ID')]]"
            ]
            
            table = None
            for selector in table_selectors:
                try:
                    table = self.driver.find_element(By.XPATH, selector)
                    if table:
                        logging.info(f"Found results table using selector: {selector}")
                        break
                except:
                    continue
            
            if not table:
                logging.error("Could not find tender results table")
                return []
            
            # Get all rows except header
            rows = table.find_elements(By.TAG_NAME, "tr")
            if len(rows) <= 1:
                logging.warning("No data rows found in table")
                return []
            
            # Skip header row
            data_rows = rows[1:]
            
            for i, row in enumerate(data_rows):
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    if len(cells) < 5:  # Minimum required columns
                        continue
                    
                    tender_info = {
                        'S.No': self.safe_get_text(cells, 0),
                        'Tender ID': self.safe_get_text(cells, 1),
                        'Title and Ref.No.': self.safe_get_text(cells, 2),
                        'Organisation Chain': self.safe_get_text(cells, 3),
                        'Tender Stage': self.safe_get_text(cells, 4),
                        'Status': self.safe_get_text(cells, 5) if len(cells) > 5 else '<empty>',
                        'Status_Link': '<empty>',
                        'Stage_Summary_Data': '<empty>',
                        'PDF_Details': '<empty>'
                    }
                    
                    # Extract status link
                    try:
                        if len(cells) > 5:
                            status_cell = cells[5]
                            links = status_cell.find_elements(By.TAG_NAME, "a")
                            if links:
                                href = links[0].get_attribute('href')
                                if href:
                                    tender_info['Status_Link'] = href
                    except Exception as e:
                        logging.debug(f"Could not extract status link for row {i}: {e}")
                    
                    tender_data.append(tender_info)
                    
                except Exception as e:
                    logging.warning(f"Error processing row {i}: {e}")
                    continue
            
            logging.info(f"Extracted {len(tender_data)} tender records")
            return tender_data
            
        except Exception as e:
            logging.error(f"Error extracting tender list: {e}")
            return []
    
    def safe_get_text(self, cells: list, index: int) -> str:
        """Safely extract text from table cell"""
        try:
            if index < len(cells):
                text = cells[index].text.strip()
                return text if text else '<empty>'
            return '<empty>'
        except:
            return '<empty>'
    
    def extract_tender_details(self, tender_info: Dict) -> Dict:
        """Extract detailed information with enhanced error handling"""
        if tender_info['Status_Link'] == '<empty>' or not tender_info['Status_Link']:
            logging.info(f"No status link for tender {tender_info['Tender ID']}")
            return tender_info
        
        original_window = self.driver.current_window_handle
        
        try:
            # Navigate to details page
            self.driver.get(tender_info['Status_Link'])
            time.sleep(3)
            
            # Extract basic tender information
            self.extract_basic_tender_info(tender_info)
            
            # Extract stage summary data
            self.extract_stage_summary(tender_info)
            
            # Try to find and click stage summary details link
            self.extract_detailed_stage_summary(tender_info)
            
            # Download PDFs
            self.download_tender_pdfs(tender_info)
            
            logging.info(f"Successfully extracted details for tender {tender_info['Tender ID']}")
            
        except Exception as e:
            logging.error(f"Error extracting details for {tender_info['Tender ID']}: {e}")
        
        finally:
            # Ensure we're back to the original window
            try:
                self.driver.switch_to.window(original_window)
            except:
                pass
        
        return tender_info
    
    def extract_basic_tender_info(self, tender_info: Dict):
        """Extract basic tender information from details page"""
        try:
            # Look for additional tender details
            info_elements = self.driver.find_elements(By.XPATH, 
                "//td[contains(text(), 'Tender Title')]/../td[2] | "
                "//td[contains(text(), 'Organisation Chain')]/../td[2] | "
                "//td[contains(text(), 'Tender Ref No')]/../td[2]"
            )
            
            # Update existing information if found
            for element in info_elements:
                text = element.text.strip()
                if text and text != tender_info.get('Title and Ref.No.', ''):
                    # Additional processing can be added here
                    pass
                    
        except Exception as e:
            logging.debug(f"Could not extract basic info: {e}")
    
    def extract_stage_summary(self, tender_info: Dict):
        """Extract stage summary information"""
        try:
            stage_data = []
            
            # Look for stage tables
            stage_selectors = [
                "//table[.//th[contains(text(), 'Stage')] or .//th[contains(text(), 'Process')]]",
                "//table[.//td[contains(text(), 'Bid Opening')] or .//td[contains(text(), 'Technical Evaluation')]]"
            ]
            
            for selector in stage_selectors:
                try:
                    tables = self.driver.find_elements(By.XPATH, selector)
                    for table in tables:
                        rows = table.find_elements(By.TAG_NAME, "tr")
                        for row in rows:
                            cells = row.find_elements(By.TAG_NAME, "td")
                            if len(cells) >= 2:
                                col1 = cells[0].text.strip()
                                col2 = cells[1].text.strip()
                                if col1 and col2 and col1 != col2:
                                    stage_data.append(f"{col1}: {col2}")
                    break
                except:
                    continue
            
            if stage_data:
                tender_info['Stage_Summary_Data'] = " | ".join(stage_data[:10])  # Limit to 10 entries
            
        except Exception as e:
            logging.debug(f"Could not extract stage summary: {e}")
    
    def extract_detailed_stage_summary(self, tender_info: Dict):
        """Extract detailed stage summary by clicking the details link"""
        try:
            # Look for stage summary details link
            details_selectors = [
                "//a[contains(text(), 'stage summary Details')]",
                "//a[contains(text(), 'View Details')]",
                "//a[contains(text(), 'More Details')]",
                "//a[contains(@href, 'stage') and contains(@href, 'summary')]"
            ]
            
            details_link = None
            for selector in details_selectors:
                try:
                    details_link = self.driver.find_element(By.XPATH, selector)
                    if details_link.is_displayed():
                        break
                except:
                    continue
            
            if details_link:
                # Store current window handles
                original_windows = self.driver.window_handles
                
                # Click the link
                self.driver.execute_script("arguments[0].click();", details_link)
                time.sleep(3)
                
                # Check if new window/tab opened
                new_windows = self.driver.window_handles
                if len(new_windows) > len(original_windows):
                    # Switch to new window
                    new_window = [w for w in new_windows if w not in original_windows][0]
                    self.driver.switch_to.window(new_window)
                
                # Extract additional details
                additional_data = []
                try:
                    tables = self.driver.find_elements(By.TAG_NAME, "table")
                    for table in tables:
                        rows = table.find_elements(By.TAG_NAME, "tr")
                        for row in rows:
                            cells = row.find_elements(By.TAG_NAME, "td")
                            if len(cells) >= 2:
                                col1 = cells[0].text.strip()
                                col2 = cells[1].text.strip()
                                if col1 and col2:
                                    additional_data.append(f"{col1}: {col2}")
                
                    if additional_data:
                        current_data = tender_info['Stage_Summary_Data']
                        if current_data != '<empty>':
                            tender_info['Stage_Summary_Data'] = current_data + " | " + " | ".join(additional_data[:5])
                        else:
                            tender_info['Stage_Summary_Data'] = " | ".join(additional_data[:5])
                
                except Exception as e:
                    logging.debug(f"Error extracting detailed stage data: {e}")
                
                # Close new window if opened
                if len(new_windows) > len(original_windows):
                    self.driver.close()
                    self.driver.switch_to.window(original_windows[0])
        
        except Exception as e:
            logging.debug(f"Could not extract detailed stage summary: {e}")
    
    def download_tender_pdfs(self, tender_info: Dict):
        """Download PDF files associated with the tender"""
        try:
            # Look for PDF links
            pdf_selectors = [
                "//a[contains(@href, '.pdf')]",
                "//a[contains(text(), 'PDF')]",
                "//a[contains(text(), 'Download')]",
                "//a[contains(text(), 'Document')]",
                "//a[contains(@href, 'download')]"
            ]
            
            pdf_links = []
            for selector in pdf_selectors:
                try:
                    links = self.driver.find_elements(By.XPATH, selector)
                    pdf_links.extend(links)
                except:
                    continue
            
            # Remove duplicates
            unique_links = []
            seen_hrefs = set()
            for link in pdf_links:
                href = link.get_attribute('href')
                if href and href not in seen_hrefs:
                    unique_links.append(href)
                    seen_hrefs.add(href)
            
            if unique_links:
                downloaded_files = []
                for i, pdf_url in enumerate(unique_links[:3]):  # Limit to 3 PDFs
                    filename = self.download_pdf_file(pdf_url, tender_info['Tender ID'], i+1)
                    if filename:
                        downloaded_files.append(filename)
                
                if downloaded_files:
                    tender_info['PDF_Details'] = " | ".join(downloaded_files)
                else:
                    tender_info['PDF_Details'] = '<download_failed>'
            
        except Exception as e:
            logging.debug(f"Error downloading PDFs for {tender_info['Tender ID']}: {e}")
    
    def download_pdf_file(self, pdf_url: str, tender_id: str, file_number: int) -> Optional[str]:
        """Download individual PDF file"""
        try:
            if not pdf_url.startswith('http'):
                pdf_url = urljoin(self.base_url, pdf_url)
            
            # Get session cookies from selenium
            cookies = self.driver.get_cookies()
            session = requests.Session()
            for cookie in cookies:
                session.cookies.set(cookie['name'], cookie['value'])
            
            # Download with timeout
            response = session.get(pdf_url, timeout=30)
            response.raise_for_status()
            
            # Generate filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{tender_id}_doc{file_number}_{timestamp}.pdf"
            filepath = os.path.join(self.download_folder, filename)
            
            # Save file
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            logging.info(f"Downloaded PDF: {filename}")
            return filename
            
        except Exception as e:
            logging.warning(f"Failed to download PDF {pdf_url}: {e}")
            return None
    
    def save_to_excel_enhanced(self, tender_data: List[Dict]) -> bool:
        """Save data to Excel with enhanced formatting"""
        try:
            if not tender_data:
                logging.error("No data to save")
                return False
            
            df = pd.DataFrame(tender_data)
            
            # Clean and format data
            for col in df.columns:
                df[col] = df[col].astype(str).replace('nan', '<empty>')
            
            # Reorder columns
            column_order = [
                'S.No', 'Tender ID', 'Title and Ref.No.', 'Organisation Chain', 
                'Tender Stage', 'Status', 'Stage_Summary_Data', 'PDF_Details'
            ]
            
            # Ensure all columns exist
            for col in column_order:
                if col not in df.columns:
                    df[col] = '<empty>'
            
            df = df[column_order]
            
            # Save to Excel with formatting
            with pd.ExcelWriter(self.excel_file, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Tender_Data', index=False)
                
                # Get workbook and worksheet
                workbook = writer.book
                worksheet = writer.sheets['Tender_Data']
                
                # Auto-adjust column widths
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)  # Cap at 50 characters
                    worksheet.column_dimensions[column_letter].width = adjusted_width
            
            # Save summary
            summary = {
                'timestamp': datetime.now().isoformat(),
                'total_records': len(tender_data),
                'records_with_pdfs': len([t for t in tender_data if t['PDF_Details'] != '<empty>']),
                'records_with_stage_data': len([t for t in tender_data if t['Stage_Summary_Data'] != '<empty>'])
            }
            
            with open(f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w') as f:
                json.dump(summary, f, indent=2)
            
            logging.info(f"Data saved to {self.excel_file}")
            logging.info(f"Summary: {summary}")
            return True
            
        except Exception as e:
            logging.error(f"Error saving to Excel: {e}")
            return False
    
    def run_scraper(self) -> bool:
        """Main method to run the complete scraping process"""
        try:
            logging.info("[START] Starting Enhanced Odisha Tender Scraper...")
            
            # Setup driver
            if not self.setup_driver():
                logging.error("Failed to setup browser driver")
                return False
            
            # Navigate to target URL
            logging.info("[NAV] Navigating to tender website...")
            self.driver.get(self.target_url)
            
            # Wait for page to load
            if not self.wait_for_element(By.NAME, "tenderStatus"):
                logging.error("Failed to load initial page")
                return False
            
            # Set tender status to AOC
            logging.info("[CONFIG] Setting tender status to AOC...")
            if not self.set_tender_status_aoc():
                logging.error("Failed to set tender status to AOC")
                return False
            
            # Search for tenders
            logging.info("[SEARCH] Searching for tenders...")
            if not self.search_tenders():
                logging.error("Failed to search for tenders")
                return False
            
            # Extract tender list
            logging.info("[EXTRACT] Extracting tender list...")
            tender_data = self.extract_tender_list()
            if not tender_data:
                logging.error("No tender data found")
                return False
            
            # Extract detailed information
            logging.info(f"[DETAILS] Extracting detailed information for {len(tender_data)} tenders...")
            for i, tender in enumerate(tender_data):
                logging.info(f"Processing tender {i+1}/{len(tender_data)}: {tender['Tender ID']}")
                tender_data[i] = self.extract_tender_details(tender)
                time.sleep(self.config["delay_between_requests"])
            
            # Save to Excel
            logging.info("[SAVE] Saving data to Excel...")
            if self.save_to_excel_enhanced(tender_data):
                logging.info("[SUCCESS] Scraping completed successfully!")
                logging.info(f"Total records: {len(tender_data)}")
                logging.info(f"Excel file: {self.excel_file}")
                logging.info(f"Downloads folder: {self.download_folder}")
                return True
            else:
                logging.error("Failed to save data")
                return False
            
        except KeyboardInterrupt:
            logging.info("Scraping interrupted by user")
            return False
        except Exception as e:
            logging.error(f"Unexpected error during scraping: {e}")
            return False
        finally:
            if self.driver:
                self.driver.quit()
                logging.info("Browser closed")

    def run_scraper_paginated_with_auto_captcha(self) -> bool:
        """Main method with pagination and automatic captcha"""
        try:
            logging.info(f"[ROCKET] [START] Starting Enhanced Odisha Tender Scraper with Auto Captcha (Target: {self.max_records} records)...")
            
            # Setup driver
            if not self.setup_driver():
                logging.error("[ERROR] Failed to setup browser driver")
                return False
            
            # Navigate to target URL
            logging.info("[NAV] Navigating to tender website...")
            self.driver.get(self.target_url)
            
            # Wait for page to load
            if not self.wait_for_element(By.NAME, "tenderStatus"):
                logging.error("[ERROR] Failed to load initial page")
                return False
            
            # Set tender status to AOC
            logging.info("[CONFIG] Setting tender status to AOC...")
            if not self.set_tender_status_aoc():
                logging.error("[ERROR] Failed to set tender status to AOC")
                return False
            
            # Search for tenders with automatic captcha
            logging.info("[SEARCH] Starting search with automatic captcha...")
            if not self.search_tenders():
                logging.error("[ERROR] Failed to search for tenders")
                return False
            
            # Extract tender list with pagination
            logging.info(f"[EXTRACT] Extracting tender list with pagination (up to {self.max_records} records)...")
            tender_data = self.extract_tender_list_paginated()
            if not tender_data:
                logging.error("[ERROR] No tender data found")
                return False
            
            # Extract detailed AOC information
            logging.info(f"[SEARCH] [DETAILS] Extracting detailed AOC information for {len(tender_data)} tenders...")
            for i, tender in enumerate(tender_data):
                logging.info(f"Processing tender {i+1}/{len(tender_data)}: {tender['Tender ID']}")
                tender_data[i] = self.extract_aoc_details_enhanced(tender)
                time.sleep(self.config["delay_between_requests"])
            
            # Save to Excel in format-compliant structure
            logging.info("[SAVE] Saving data to Excel in FORMAT AUGUST 2025 compliance...")
            if self.save_to_excel_format_compliant(tender_data):
                logging.info("[SUCCESS] Scraping completed successfully!")
                logging.info(f"[EXTRACT] Total records: {len(tender_data)}")
                logging.info(f"[FOLDER] Excel file: {self.excel_file}")
                logging.info(f"[FOLDER] Downloads: {self.download_folder}")
                return True
            else:
                logging.error("[ERROR] Failed to save data to Excel")
                return False
                
        except Exception as e:
            logging.error(f"[ERROR] Scraper error: {e}")
            return False
        finally:
            if self.driver:
                self.driver.quit()
                logging.info("Browser closed")

    def run_scraper_paginated_with_gui_captcha(self) -> bool:
        """Main method with pagination and GUI captcha"""
        try:
            logging.info(f"[START] Starting Enhanced Odisha Tender Scraper with GUI Captcha (Target: {self.max_records} records)...")
            
            # Setup driver
            if not self.setup_driver():
                logging.error("[ERROR] Failed to setup browser driver")
                return False
            
            # Navigate to target URL
            logging.info("[NAV] Navigating to tender website...")
            self.driver.get(self.target_url)
            
            # Wait for page to load
            if not self.wait_for_element(By.NAME, "tenderStatus"):
                logging.error("[ERROR] Failed to load initial page")
                return False
            
            # Set tender status to AOC
            logging.info("[CONFIG] Setting tender status to AOC...")
            if not self.set_tender_status_aoc():
                logging.error("[ERROR] Failed to set tender status to AOC")
                return False
            
            # Search for tenders with GUI captcha
            logging.info("[SEARCH] Starting search with GUI captcha...")
            if not self.search_tenders_gui():
                logging.error("[ERROR] Failed to search for tenders")
                return False
            
            # Extract tender list with pagination
            logging.info(f"[EXTRACT] Extracting tender list with pagination (up to {self.max_records} records)...")
            tender_data = self.extract_tender_list_paginated()
            if not tender_data:
                logging.error("[ERROR] No tender data found")
                return False
            
            # Extract detailed AOC information
            logging.info(f"[SEARCH] [DETAILS] Extracting detailed AOC information for {len(tender_data)} tenders...")
            for i, tender in enumerate(tender_data):
                logging.info(f"Processing tender {i+1}/{len(tender_data)}: {tender['Tender ID']}")
                tender_data[i] = self.extract_aoc_details_enhanced(tender)
                time.sleep(self.config["delay_between_requests"])
            
            # Save to Excel in format-compliant structure
            logging.info("[SAVE] Saving data to Excel in FORMAT AUGUST 2025 compliance...")
            if self.save_to_excel_format_compliant(tender_data):
                logging.info("[SUCCESS] Scraping completed successfully!")
                logging.info(f"[EXTRACT] Total records: {len(tender_data)}")
                logging.info(f"[FOLDER] Excel file: {self.excel_file}")
                logging.info(f"[FOLDER] Downloads: {self.download_folder}")
                return True
            else:
                logging.error("[ERROR] Failed to save data to Excel")
                return False
                
        except Exception as e:
            logging.error(f"[ERROR] Scraper error: {e}")
            return False
        finally:
            if self.driver:
                self.driver.quit()
                logging.info("Browser closed")

def main():
    """Main function with command line interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhanced Odisha Tender Scraper')
    parser.add_argument('--config', default='scraper_config.json', 
                       help='Configuration file path')
    parser.add_argument('--headless', action='store_true', 
                       help='Run in headless mode')
    parser.add_argument('--records', type=int, 
                       help='Number of records to scrape')
    
    args = parser.parse_args()
    
    # Update config for headless mode if specified
    if args.headless:
        if os.path.exists(args.config):
            with open(args.config, 'r') as f:
                config = json.load(f)
            config['headless_mode'] = True
            with open(args.config, 'w') as f:
                json.dump(config, f, indent=4)
    
    scraper = OdishaTenderScraperEnhanced(args.config)
    
    # Get number of records to scrape
    if args.records:
        max_records = args.records
    else:
        # Default to 25 records if not specified
        max_records = 25
        print(f"Using default record count: {max_records}")
        print("To specify a different number, use: --records N")
    
    # Set max records in scraper
    scraper.set_max_records(max_records)
    print(f"\nTarget records: {max_records}")
    
    # Ask user which captcha method to use
    print("\nChoose captcha handling method:")
    print("1. Automatic captcha (user enters text in dialog)")
    print("2. Manual captcha (user types directly in browser) - RECOMMENDED")
    print("3. GUI captcha (use with GUI application)")
    
    while True:
        choice = input("Enter choice (1, 2, or 3): ").strip()
        if choice in ['1', '2', '3']:
            break
        print("Invalid choice. Please enter 1, 2, or 3.")
    
    # Always use paginated scraper for better results
    print(f"\nUsing enhanced paginated scraper with format compliance...")
    print("This will scrape multiple pages until target records are reached.")
    
    if choice == '1':
        print("Using automatic captcha method...")
        success = scraper.run_scraper_paginated_with_auto_captcha()
    elif choice == '2':
        print("Using manual captcha method (RECOMMENDED)...")
        success = scraper.run_scraper_paginated()
    else:
        print("Using GUI captcha method...")
        success = scraper.run_scraper_paginated_with_gui_captcha()
    
    if success:
        print("\nScraping completed successfully!")
        print(f"Check the Excel file: {scraper.excel_file}")
        print(f"Check downloads in: {scraper.download_folder}")
        print(f"Target records: {max_records}")
    else:
        print("\nScraping failed. Check the logs for details.")

if __name__ == "__main__":
    main()