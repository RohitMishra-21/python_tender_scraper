#!/bin/bash

echo "================================================"
echo "   Odisha Tender Scraper - Linux Build Script"
echo "================================================"
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8+ first"
    exit 1
fi

echo "Step 1: Installing requirements..."
pip3 install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install requirements"
    exit 1
fi

echo
echo "Step 2: Building executable..."
python3 build_executable.py
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to build executable"
    exit 1
fi

echo
echo "Step 3: Creating distribution package..."
rm -rf dist_package
mkdir dist_package
cp -r dist/* dist_package/
cp README.md dist_package/ 2>/dev/null || true
cp User_Guide.pdf dist_package/ 2>/dev/null || true

# Make executable
chmod +x dist_package/OdishaTenderScraper

echo
echo "================================================"
echo "BUILD COMPLETED SUCCESSFULLY!"
echo "================================================"
echo
echo "Executable location: dist_package/OdishaTenderScraper"
echo
echo "To distribute:"
echo "1. Tar the 'dist_package' folder: tar -czf odisha-tender-scraper.tar.gz dist_package"
echo "2. Share with end users"
echo "3. No Python installation required on target machines"
echo

# =====================================

# install_and_run.bat (For end users)
@echo off
title Odisha Tender Scraper - Installer
echo ================================================
echo       Odisha Tender Scraper v1.0
echo       Automated Tender Data Extraction
echo ================================================
echo.

REM Check if executable exists
if not exist "OdishaTenderScraper.exe" (
    echo ERROR: OdishaTenderScraper.exe not found!
    echo Please ensure this script is in the same directory as the executable in linux.
    pause
    exit /b 1
)

REM Create necessary directories
if not exist "output" mkdir "output"
if not exist "output\excel_files" mkdir "output\excel_files"
if not exist "output\pdf_downloads" mkdir "output\pdf_downloads"
if not exist "logs" mkdir "logs"

echo Setting up environment...
echo Creating output directories...
echo.

echo Starting Odisha Tender Scraper...
echo.
echo IMPORTANT NOTES:
echo - Default chosen browser will open automatically
echo - You will need to solve the captcha manually
echo - Do not close the application during scraping
echo - Results will be saved in the 'output' folder
echo.
pause

REM Run the application
start "" "OdishaTenderScraper.exe"

echo Application started successfully!
echo Check the application window for progress updates.
echo.
pause