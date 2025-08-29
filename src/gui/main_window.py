import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import os
from datetime import datetime
import json
import logging

from scraper.tender_scrapper import OdishaTenderScraperEnhanced
from utils.file_manager import FileManager

class MainApplication:
    """Main GUI Application"""
    
    def __init__(self, root, config):
        self.root = root
        self.config = config
        self.scraper = None
        self.is_running = False
        self.file_manager = FileManager()
        self.captcha_event = None  # Event to signal captcha completion
        
        self.setup_gui()
    
    def setup_gui(self):
        """Setup the main GUI"""
        # Create main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Odisha Tender Scraper", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Configuration Section
        config_frame = ttk.LabelFrame(main_frame, text="Configuration", padding="10")
        config_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        config_frame.columnconfigure(1, weight=1)
        
        # Output directory
        ttk.Label(config_frame, text="Output Directory:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.output_dir_var = tk.StringVar(value=self.config.get("download_folder", "output"))
        output_entry = ttk.Entry(config_frame, textvariable=self.output_dir_var, width=50)
        output_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 5), pady=2)
        ttk.Button(config_frame, text="Browse", 
                  command=self.browse_output_dir).grid(row=0, column=2, pady=2)
        
        # Headless mode
        self.headless_var = tk.BooleanVar(value=self.config.get("headless_mode", False))
        ttk.Checkbutton(config_frame, text="Run in headless mode (no browser window)",
                       variable=self.headless_var).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Number of records setting
        ttk.Label(config_frame, text="Number of records to scrape:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.records_var = tk.StringVar(value=str(self.config.get("max_records", 25)))
        records_spin = ttk.Spinbox(config_frame, from_=1, to=1000, textvariable=self.records_var, width=10)
        records_spin.grid(row=2, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        
        # Delay setting
        ttk.Label(config_frame, text="Delay between requests (seconds):").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.delay_var = tk.StringVar(value=str(self.config.get("delay_between_requests", 2)))
        delay_spin = ttk.Spinbox(config_frame, from_=1, to=10, textvariable=self.delay_var, width=10)
        delay_spin.grid(row=3, column=1, sticky=tk.W, padx=(5, 0), pady=2)
        
        # Control Section
        control_frame = ttk.LabelFrame(main_frame, text="Controls", padding="10")
        control_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Buttons
        self.start_button = ttk.Button(control_frame, text="Start Scraping", 
                                      command=self.start_scraping, style="Accent.TButton")
        self.start_button.grid(row=0, column=0, padx=(0, 10))
        
        self.stop_button = ttk.Button(control_frame, text="Stop Scraping", 
                                     command=self.stop_scraping, state="disabled")
        self.stop_button.grid(row=0, column=1, padx=(0, 10))
        
        self.open_output_button = ttk.Button(control_frame, text="Open Output Folder", 
                                           command=self.open_output_folder)
        self.open_output_button.grid(row=0, column=2, padx=(0, 10))
        
        self.settings_button = ttk.Button(control_frame, text="Advanced Settings", 
                                        command=self.open_settings)
        self.settings_button.grid(row=0, column=3)
        
        # Captcha completion button (initially hidden)
        self.captcha_done_button = ttk.Button(control_frame, text="✅ Captcha Done - Continue Scraping", 
                                            command=self.captcha_completed, 
                                            style="Accent.TButton")
        self.captcha_done_button.grid(row=1, column=0, columnspan=4, pady=(10, 0), sticky=(tk.W, tk.E))
        self.captcha_done_button.grid_remove()  # Hide initially
        
        # Progress Section
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding="10")
        progress_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        
        # Progress bar
        self.progress_var = tk.StringVar(value="Ready to start...")
        ttk.Label(progress_frame, textvariable=self.progress_var).grid(row=0, column=0, sticky=tk.W)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # Log Section
        log_frame = ttk.LabelFrame(main_frame, text="Log Output", padding="10")
        log_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # Log text area
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=80)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Setup logging handler for GUI
        self.setup_gui_logging()
    
    def setup_gui_logging(self):
        """Setup logging to display in GUI"""
        class GUILogHandler(logging.Handler):
            def __init__(self, text_widget):
                super().__init__()
                self.text_widget = text_widget
                
            def emit(self, record):
                try:
                    msg = self.format(record)
                    self.text_widget.insert(tk.END, msg + '\n')
                    self.text_widget.see(tk.END)
                except:
                    pass
        
        gui_handler = GUILogHandler(self.log_text)
        gui_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(gui_handler)
    
    def browse_output_dir(self):
        """Browse for output directory"""
        directory = filedialog.askdirectory(initialdir=self.output_dir_var.get())
        if directory:
            self.output_dir_var.set(directory)
    
    def start_scraping(self):
        """Start the scraping process"""
        if self.is_running:
            messagebox.showwarning("Warning", "Scraping is already running!")
            return
        
        # Update configuration
        self.config["download_folder"] = self.output_dir_var.get()
        self.config["headless_mode"] = self.headless_var.get()
        self.config["max_records"] = int(self.records_var.get())
        self.config["delay_between_requests"] = float(self.delay_var.get())
        
        # Clear log
        self.log_text.delete(1.0, tk.END)
        
        # Update UI
        self.is_running = True
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.progress_bar.start()
        self.progress_var.set("Starting scraper...")
        
        # Create event for captcha completion
        self.captcha_event = threading.Event()
        
        # Start scraping in separate thread
        threading.Thread(target=self.run_scraper, daemon=True).start()
    
    def stop_scraping(self):
        """Stop the scraping process"""
        if self.scraper:
            # Note: This is a basic stop - in a real implementation,
            # you'd need more sophisticated thread communication
            self.is_running = False
            logging.info("Stop requested by user")
        
        self.reset_ui()
    
    def show_captcha_button(self):
        """Show the captcha completion button"""
        self.root.after(0, lambda: self.captcha_done_button.grid())
        self.root.after(0, lambda: self.progress_var.set("⏳ Please solve the captcha in the browser, then click 'Captcha Done'"))
    
    def hide_captcha_button(self):
        """Hide the captcha completion button"""
        self.root.after(0, lambda: self.captcha_done_button.grid_remove())
    
    def captcha_completed(self):
        """Called when user clicks the captcha done button"""
        self.captcha_event.set()  # Signal that captcha is done
        self.hide_captcha_button()
        self.progress_var.set("✅ Captcha confirmed, continuing scraping...")
        logging.info("User confirmed captcha completion via GUI button")
    
    def run_scraper(self):
        """Run the scraper in a separate thread"""
        try:
            # Create and run scraper with proper configuration
            self.scraper = OdishaTenderScraperEnhanced(max_records=self.config.get("max_records", 25))
            
            # Update scraper config with GUI settings
            self.scraper.config.update({
                'download_folder': self.output_dir_var.get(),
                'headless_mode': self.headless_var.get(),
                'delay_between_requests': float(self.delay_var.get()),
                'timeout_seconds': self.config.get('timeout_seconds', 15),
                'max_retries': self.config.get('max_retries', 3)
            })
            
            # Pass GUI callbacks to scraper
            self.scraper.gui_show_captcha_button = self.show_captcha_button
            self.scraper.gui_captcha_event = self.captcha_event
            
            # Use paginated version with GUI captcha for better results
            success = self.scraper.run_scraper_paginated_with_gui_captcha()
            
            if success:
                self.progress_var.set("Scraping completed successfully!")
                logging.info("Scraping completed successfully!")
                self.root.after(0, lambda: messagebox.showinfo("Success", 
                    f"Scraping completed successfully!\nCheck: {self.output_dir_var.get()}"))
            else:
                self.progress_var.set("Scraping failed!")
                logging.error("Scraping failed!")
                self.root.after(0, lambda: messagebox.showerror("Error", 
                    "Scraping failed! Check the log for details."))
                    
        except Exception as e:
            error_msg = str(e)
            logging.error(f"Scraping error: {error_msg}")
            self.progress_var.set(f"Error: {error_msg}")
            self.root.after(0, lambda msg=error_msg: messagebox.showerror("Error", f"Scraping error: {msg}"))
        
        finally:
            self.root.after(0, self.reset_ui)
            self.root.after(0, self.hide_captcha_button)
    
    def reset_ui(self):
        """Reset UI after scraping"""
        self.is_running = False
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.progress_bar.stop()
        if self.progress_var.get().startswith("Starting") or "captcha" in self.progress_var.get().lower():
            self.progress_var.set("Ready to start...")
        self.hide_captcha_button()
    
    def open_output_folder(self):
        """Open the output folder"""
        output_dir = self.output_dir_var.get()
        if os.path.exists(output_dir):
            self.file_manager.open_folder(output_dir)
        else:
            messagebox.showwarning("Warning", f"Output directory does not exist: {output_dir}")
    
    def open_settings(self):
        """Open advanced settings window"""
        SettingsWindow(self.root, self.config)

class SettingsWindow:
    """Advanced settings window"""
    
    def __init__(self, parent, config):
        self.config = config
        self.window = tk.Toplevel(parent)
        self.window.title("Advanced Settings")
        self.window.geometry("500x400")
        self.window.resizable(False, False)
        
        # Make modal
        self.window.transient(parent)
        self.window.grab_set()
        
        self.setup_settings_gui()
    
    def setup_settings_gui(self):
        """Setup settings GUI"""
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # General tab
        general_frame = ttk.Frame(notebook, padding="10")
        notebook.add(general_frame, text="General")
        
        # Timeout setting
        ttk.Label(general_frame, text="Timeout (seconds):").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.timeout_var = tk.StringVar(value=str(self.config.get("timeout_seconds", 15)))
        ttk.Spinbox(general_frame, from_=5, to=60, textvariable=self.timeout_var, width=10).grid(row=0, column=1, sticky=tk.W, pady=2)
        
        # Max retries
        ttk.Label(general_frame, text="Max retries:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.retries_var = tk.StringVar(value=str(self.config.get("max_retries", 3)))
        ttk.Spinbox(general_frame, from_=1, to=10, textvariable=self.retries_var, width=10).grid(row=1, column=1, sticky=tk.W, pady=2)
        
        # Excel file prefix
        ttk.Label(general_frame, text="Excel file prefix:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.prefix_var = tk.StringVar(value=self.config.get("excel_file_prefix", "odisha_tenders"))
        ttk.Entry(general_frame, textvariable=self.prefix_var, width=30).grid(row=2, column=1, sticky=tk.W, pady=2)
        
        # Max records
        ttk.Label(general_frame, text="Max records to scrape:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.max_records_var = tk.StringVar(value=str(self.config.get("max_records", 25)))
        ttk.Spinbox(general_frame, from_=1, to=1000, textvariable=self.max_records_var, width=10).grid(row=3, column=1, sticky=tk.W, pady=2)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="Save", command=self.save_settings).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_frame, text="Cancel", command=self.window.destroy).pack(side=tk.RIGHT)
        ttk.Button(button_frame, text="Reset to Defaults", command=self.reset_settings).pack(side=tk.LEFT)
    
    def save_settings(self):
        """Save settings"""
        try:
            self.config["timeout_seconds"] = int(self.timeout_var.get())
            self.config["max_retries"] = int(self.retries_var.get())
            self.config["excel_file_prefix"] = self.prefix_var.get()
            self.config["max_records"] = int(self.max_records_var.get())
            
            messagebox.showinfo("Success", "Settings saved successfully!")
            self.window.destroy()
            
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid value: {e}")
    
    def reset_settings(self):
        """Reset to default settings"""
        if messagebox.askyesno("Confirm", "Reset all settings to defaults?"):
            self.timeout_var.set("15")
            self.retries_var.set("3")
            self.prefix_var.set("odisha_tenders")
            self.max_records_var.set("25")