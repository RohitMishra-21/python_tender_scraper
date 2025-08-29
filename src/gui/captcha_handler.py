import tkinter as tk
from tkinter import ttk
import logging

class CaptchaHandler:
    """Standalone captcha handling GUI"""
    
    def __init__(self):
        self.result = None
        self.window = None
    
    def get_captcha_input(self, attempt=1, max_attempts=3):
        """Get captcha input from user"""
        self.result = {"submitted": False, "text": ""}
        
        # Create window
        self.window = tk.Tk()
        self.window.title("Captcha Input Required")
        self.window.geometry("400x250")
        self.window.resizable(False, False)
        
        # Center the window
        self.window.eval('tk::PlaceWindow . center')
        
        # Make it stay on top
        self.window.lift()
        self.window.focus_force()
        
        # Create GUI elements
        main_frame = ttk.Frame(self.window, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, 
                               text=f"Captcha Required (Attempt {attempt}/{max_attempts})", 
                               font=("Arial", 12, "bold"))
        title_label.pack(pady=(0, 10))
        
        # Instructions
        inst1 = ttk.Label(main_frame, text="Please solve the captcha in the browser window")
        inst1.pack(pady=2)
        
        inst2 = ttk.Label(main_frame, text="and enter the text below:")
        inst2.pack(pady=2)
        
        inst3 = ttk.Label(main_frame, text="Type the captcha text and click Submit", 
                         font=("Arial", 9))
        inst3.pack(pady=5)
        
        # Input field
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(pady=15)
        
        ttk.Label(input_frame, text="Captcha Text:").pack()
        
        self.captcha_var = tk.StringVar()
        self.entry = ttk.Entry(input_frame, textvariable=self.captcha_var, 
                              font=("Arial", 12), width=20)
        self.entry.pack(pady=5)
        self.entry.focus()
        
        # Test the entry field by adding some debugging
        def on_key_press(event):
            logging.info(f"Key pressed: {event.char}, current text: '{self.entry.get()}'")
        
        self.entry.bind('<KeyPress>', on_key_press)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=15)
        
        submit_btn = ttk.Button(button_frame, text="Submit", 
                               command=self._submit_captcha)
        submit_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = ttk.Button(button_frame, text="Cancel", 
                               command=self._cancel_captcha)
        cancel_btn.pack(side=tk.LEFT, padx=5)
        
        # Bind Enter key
        self.entry.bind('<Return>', lambda e: self._submit_captcha())
        
        # Run modal dialog
        try:
            self.window.mainloop()
        except tk.TclError as e:
            logging.warning(f"Window error during captcha input: {e}")
            # If window was destroyed, assume cancellation
            if not self.result or not self.result.get("submitted"):
                self.result = {"submitted": False, "text": ""}
        
        return self.result
    
    def _submit_captcha(self):
        """Handle submit button"""
        try:
            # Try multiple ways to get the text
            var_text = self.captcha_var.get().strip()
            entry_text = self.entry.get().strip()
            
            logging.info(f"Submit clicked - StringVar: '{var_text}', Entry.get(): '{entry_text}'")
            
            # Use whichever method returns text
            text = entry_text if entry_text else var_text
            
            # Always accept the submission, even if empty (let the calling code handle validation)
            self.result = {"submitted": True, "text": text}
            if text:
                logging.info(f"Captcha text entered by user: '{text}'")
            else:
                logging.warning("Empty captcha text submitted")
            
            # Safely destroy window
            if self.window:
                self.window.quit()  # Exit mainloop
                self.window.destroy()
        except Exception as e:
            logging.error(f"Error in submit_captcha: {e}")
            self.result = {"submitted": True, "text": ""}
    
    def _cancel_captcha(self):
        """Handle cancel button"""
        try:
            self.result = {"submitted": False, "text": ""}
            logging.info("Captcha input cancelled by user")
            
            # Safely destroy window
            if self.window:
                self.window.quit()  # Exit mainloop
                self.window.destroy()
        except Exception as e:
            logging.error(f"Error in cancel_captcha: {e}")