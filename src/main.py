#!/usr/bin/env python3
"""
Odisha Tender Scraper - Main Application Entry Point
Author: Rohit Mishra
Version: 1.2.1
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import json
from datetime import datetime
import logging

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from scraper.tender_scrapper import OdishaTenderScraperEnhanced
from utils.logger import setup_logging
from config.setting import load_config, save_config
from gui.main_window import MainApplication

class TenderScraperApp:
    """Main application class"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.config = None
        self.scraper = None
        self.setup_application()
    
    def setup_application(self):
        """Setup the main application"""
        # Setup logging
        setup_logging()
        
        # Load configuration
        self.config = load_config()
        
        # Setup main window
        self.root.title("Odisha Tender Scraper v1.0")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Set icon if available
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "..", "assets", "icons", "app_icon.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except:
            pass
        
        # Create main application GUI
        self.app = MainApplication(self.root, self.config)
        
        # Bind close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def on_closing(self):
        """Handle application closing"""
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            # Save current configuration
            save_config(self.config)
            self.root.destroy()
    
    def run(self):
        """Run the application"""
        try:
            self.root.mainloop()
        except Exception as e:
            logging.error(f"Application error: {e}")
            messagebox.showerror("Error", f"Application error: {e}")

def main():
    """Main entry point"""
    try:
        app = TenderScraperApp()
        app.run()
    except Exception as e:
        print(f"Failed to start application: {e}")
        if tk._default_root:
            messagebox.showerror("Startup Error", f"Failed to start application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()