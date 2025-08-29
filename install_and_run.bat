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
    echo Please ensure this script is in the same folder as the executable.
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
echo - Chrome browser will open automatically
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