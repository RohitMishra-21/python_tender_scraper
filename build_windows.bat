@echo off
echo ================================================
echo    Odisha Tender Scraper - Windows Build Script
echo ================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo Step 1: Installing requirements...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install requirements
    pause
    exit /b 1
)

echo.
echo Step 2: Building executable...
python build_executable.py
if errorlevel 1 (
    echo ERROR: Failed to build executable
    pause
    exit /b 1
)

echo.
echo Step 3: Creating distribution package...
if exist "dist_package" rmdir /s /q "dist_package"
mkdir "dist_package"
xcopy "dist\*" "dist_package\" /s /e /y
copy "README.md" "dist_package\"
copy "User_Guide.pdf" "dist_package\" 2>nul

echo.
echo ================================================
echo BUILD COMPLETED SUCCESSFULLY!
echo ================================================
echo.
echo Executable location: dist_package\OdishaTenderScraper.exe
echo.
echo To distribute:
echo 1. Zip the 'dist_package' folder
echo 2. Share with end users
echo 3. No Python installation required on target machines
echo.
pause