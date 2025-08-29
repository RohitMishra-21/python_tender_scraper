import json
import os
import logging
from typing import Dict, Any

DEFAULT_CONFIG = {
    "base_url": "https://tendersodisha.gov.in",
    "target_url": "https://tendersodisha.gov.in/nicgep/app?page=WebTenderStatusLists&service=page",
    "download_folder": "output/pdf_downloads",
    "excel_file_prefix": "odisha_tenders",
    "timeout_seconds": 15,
    "delay_between_requests": 2,
    "max_retries": 3,
    "headless_mode": False
}

def get_config_path():
    """Get configuration file path"""
    return os.path.join(os.path.dirname(__file__), "..", "..", "config", "scraper_config.json")

def load_config() -> Dict[str, Any]:
    """Load configuration from file"""
    config_path = get_config_path()
    
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Merge with defaults to ensure all keys exist
            merged_config = DEFAULT_CONFIG.copy()
            merged_config.update(config)
            
            logging.info(f"Configuration loaded from {config_path}")
            return merged_config
        else:
            # Create default config file
            save_config(DEFAULT_CONFIG)
            logging.info(f"Created default configuration at {config_path}")
            return DEFAULT_CONFIG.copy()
            
    except Exception as e:
        logging.error(f"Error loading configuration: {e}")
        return DEFAULT_CONFIG.copy()

def save_config(config: Dict[str, Any]) -> bool:
    """Save configuration to file"""
    config_path = get_config_path()
    
    try:
        # Ensure config directory exists
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
        
        logging.info(f"Configuration saved to {config_path}")
        return True
        
    except Exception as e:
        logging.error(f"Error saving configuration: {e}")
        return False

def reset_config() -> Dict[str, Any]:
    """Reset configuration to defaults"""
    save_config(DEFAULT_CONFIG)
    return DEFAULT_CONFIG.copy()