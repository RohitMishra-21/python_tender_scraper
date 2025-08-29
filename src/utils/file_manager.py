import os
import sys
import subprocess
import platform
import shutil
from datetime import datetime
import logging

class FileManager:
    """File management utilities"""
    
    def __init__(self):
        self.platform = platform.system()
    
    def open_folder(self, path):
        """Open folder in file explorer"""
        try:
            if self.platform == "Windows":
                os.startfile(path)
            elif self.platform == "Darwin":  # macOS
                subprocess.run(["open", path])
            else:  # Linux
                subprocess.run(["xdg-open", path])
        except Exception as e:
            logging.error(f"Failed to open folder {path}: {e}")
    
    def create_backup(self, file_path):
        """Create backup of a file"""
        try:
            if os.path.exists(file_path):
                backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.copy2(file_path, backup_path)
                return backup_path
        except Exception as e:
            logging.error(f"Failed to create backup of {file_path}: {e}")
        return None
    
    def clean_old_logs(self, log_dir, max_age_days=7):
        """Clean old log files"""
        try:
            cutoff_time = datetime.now().timestamp() - (max_age_days * 24 * 3600)
            
            for filename in os.listdir(log_dir):
                file_path = os.path.join(log_dir, filename)
                if os.path.isfile(file_path) and filename.endswith('.log'):
                    if os.path.getmtime(file_path) < cutoff_time:
                        os.remove(file_path)
                        logging.info(f"Removed old log file: {filename}")
        except Exception as e:
            logging.error(f"Failed to clean old logs: {e}")