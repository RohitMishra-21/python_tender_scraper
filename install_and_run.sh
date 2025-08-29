#!/bin/bash

echo "================================================"
echo "      Odisha Tender Scraper v1.0"
echo "      Automated Tender Data Extraction"
echo "================================================"
echo

# Check if executable exists
if [ ! -f "OdishaTenderScraper" ]; then
    echo "ERROR: OdishaTenderScraper executable not found!"
    echo "Please ensure this script is in the same folder as the executable."
    exit 1
fi

# Create necessary directories
mkdir -p output/excel_files
mkdir -p output/pdf_downloads
mkdir -p logs

echo "Setting up environment..."
echo "Creating output directories..."
echo

# Make executable if not already
chmod +x OdishaTenderScraper

echo "Starting Odisha Tender Scraper..."
echo
echo "IMPORTANT NOTES:"
echo "- Chrome browser will open automatically"
echo "- You will need to solve the captcha manually"
echo "- Do not close the application during scraping"
echo "- Results will be saved in the 'output' folder"
echo

read -p "Press Enter to continue..."
