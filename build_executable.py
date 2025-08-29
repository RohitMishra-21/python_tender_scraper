import PyInstaller.__main__
import os
import sys
import shutil
from pathlib import Path

def build_executable():
    """Build executable using PyInstaller"""
    
    # Define paths
    project_root = Path(__file__).parent
    src_dir = project_root / "src"
    dist_dir = project_root / "dist"
    build_dir = project_root / "build"
    
    # Clean previous builds
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    if build_dir.exists():
        shutil.rmtree(build_dir)
    
    # PyInstaller arguments
    args = [
        str(src_dir / "main.py"),
        "--name=OdishaTenderScraper",
        "--onefile",
        "--windowed",
        f"--distpath={dist_dir}",
        f"--workpath={build_dir}",
        "--add-data=config;config",
        "--add-data=assets;assets",
        "--hidden-import=selenium",
        "--hidden-import=pandas",
        "--hidden-import=openpyxl",
        "--hidden-import=requests",
        "--hidden-import=PIL",
        "--hidden-import=webdriver_manager",
        "--collect-all=selenium",
        "--collect-all=webdriver_manager",
    ]
    
    # Add icon if available
    icon_path = project_root / "assets" / "icons" / "app_icon.ico"
    if icon_path.exists():
        args.append(f"--icon={icon_path}")
    
    print("Building executable...")
    print(f"Arguments: {' '.join(args)}")
    
    # Run PyInstaller
    PyInstaller.__main__.run(args)
    
    # Copy additional files to dist
    if dist_dir.exists():
        # Copy config folder
        config_src = project_root / "config"
        config_dest = dist_dir / "config"
        if config_src.exists():
            shutil.copytree(config_src, config_dest, dirs_exist_ok=True)
        
        # Create output directories
        (dist_dir / "output" / "excel_files").mkdir(parents=True, exist_ok=True)
        (dist_dir / "output" / "pdf_downloads").mkdir(parents=True, exist_ok=True)
        (dist_dir / "logs").mkdir(exist_ok=True)
        
        # Copy README and other docs
        for file in ["README.md", "requirements.txt"]:
            src_file = project_root / file
            if src_file.exists():
                shutil.copy2(src_file, dist_dir / file)
    
    print("Build completed!")
    print(f"Executable location: {dist_dir}")

if __name__ == "__main__":
    build_executable()