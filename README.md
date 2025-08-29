# Odisha Tender Scraper v1.0

## Overview
Professional desktop application for automated extraction of tender data from the Odisha Government e-Procurement Portal. Features a user-friendly GUI, automated PDF downloads, and Excel export capabilities.

## Features
- ✅ **GUI Application** - Easy-to-use desktop interface
- ✅ **Automated Browser Control** - Handles Chrome automation
- ✅ **Smart Captcha Handling** - Interactive captcha solving
- ✅ **Excel Export** - Professional formatted reports
- ✅ **PDF Downloads** - Automatic document retrieval
- ✅ **Configurable Settings** - Customizable scraping parameters
- ✅ **Progress Tracking** - Real-time status updates
- ✅ **Error Recovery** - Robust error handling and retries
- ✅ **Cross-Platform** - Windows, Linux, and macOS support

## Quick Start (For End Users)

### Windows
1. Download and extract the application package
2. Double-click `install_and_run.bat`
3. Follow the on-screen instructions

### Linux/macOS
1. Download and extract the application package
2. Run `chmod +x install_and_run.sh && ./install_and_run.sh`
3. Follow the on-screen instructions

## System Requirements
- **Operating System**: Windows 10+, Ubuntu 18.04+, macOS 10.14+
- **Memory**: 4GB RAM minimum (8GB recommended)
- **Storage**: 500MB free space
- **Internet**: Stable broadband connection
- **Browser**: Chrome will be installed automatically if not present

## Usage Instructions

### 1. Starting the Application
- Launch the application using the provided scripts
- The main window will open with configuration options

### 2. Configuration
- **Output Directory**: Choose where to save results
- **Headless Mode**: Run without browser window (advanced)
- **Delay Settings**: Adjust speed between requests

### 3. Running the Scraper
1. Click "Start Scraping"
2. Chrome browser will open automatically
3. AOC status will be selected automatically
4. **Solve the captcha** when prompted
5. Wait for the scraping to complete
6. Results will be saved to the output directory

### 4. Output Files
- **Excel File**: `odisha_tenders_YYYYMMDD_HHMMSS.xlsx`
- **PDF Files**: Downloaded to `output/pdf_downloads/`
- **Logs**: Detailed logs in `logs/` folder

## Data Fields Extracted

| Field | Description |
|-------|-------------|
| S.No | Serial number |
| Tender ID | Unique tender identifier |
| Title and Ref.No. | Tender title and reference |
| Organisation Chain | Issuing organization details |
| Tender Stage | Current processing stage |
| Status | Current status |
| Stage_Summary_Data | Detailed stage information |
| PDF_Details | Downloaded document filenames |

## Advanced Configuration

### Configuration File: `config/scraper_config.json`
```json
{
    "timeout_seconds": 15,
    "delay_between_requests": 2,
    "max_retries": 3,
    "headless_mode": false,
    "excel_file_prefix": "odisha_tenders"
}
```

### Customization Options
- **Timeout Settings**: Adjust for slow connections
- **Retry Logic**: Configure failure recovery
- **Output Formatting**: Customize Excel output
- **Performance Tuning**: Optimize for your system

## Troubleshooting

### Common Issues

1. **Chrome Driver Issues**
   - The application handles Chrome driver automatically
   - If issues persist, restart the application

2. **Captcha Problems**
   - Ensure the browser window is visible
   - Refresh if captcha is unclear
   - Try multiple times if needed

3. **Network Timeouts**
   - Check internet connection
   - Increase timeout in advanced settings
   - Try during off-peak hours

4. **Permission Errors**
   - Run as administrator (Windows)
   - Check folder permissions
   - Ensure antivirus isn't blocking

### Getting Help
- Check the log files in the `logs/` folder
- Look for error messages in the application window
- Ensure all requirements are met

## Technical Details

### Built With
- **Python 3.8+**: Core application language
- **Selenium**: Browser automation
- **Tkinter**: GUI framework
- **Pandas**: Data processing
- **OpenPyXL**: Excel file handling
- **PyInstaller**: Executable packaging

### Architecture
```
odisha_tender_scraper/
├── src/                    # Source code
│   ├── main.py            # Application entry point
│   ├── scraper/           # Core scraping logic
│   ├── gui/               # User interface
│   ├── utils/             # Utility functions
│   └── config/            # Configuration management
├── config/                 # Configuration files
├── output/                 # Generated files
├── logs/                   # Application logs
└── assets/                 # Icons and resources
```

## Development Setup

### For Developers

1. **Clone/Download** the project
2. **Install Python 3.8+**
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Run from source**:
   ```bash
   python src/main.py
   ```

### Building Executable

1. **Install PyInstaller**:
   ```bash
   pip install PyInstaller
   ```

2. **Build executable**:
   ```bash
   python build_executable.py
   ```

3. **Distribute**:
   - Package the `dist/` folder
   - Include user guide and scripts

## License
This project is licensed under the MIT License - see the LICENSE file for details.

## Legal Compliance
- Respects website rate limits
- Includes delays between requests
- Follows ethical scraping practices
- Use responsibly and in compliance with website terms

## Version History
- **v1.0.0**: Initial release with GUI and full automation
- Features complete tender extraction with PDF downloads

## Support
For technical support or feature requests, please refer to the documentation or contact the development team.

---

## File Structure Reference

```
.gitignore content:
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# PyInstaller
*.manifest
*.spec

# Logs
logs/
*.log

# Output
output/
*.xlsx
*.pdf

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Config (keep template)
config/scraper_config.json

# Build
dist_package/
```