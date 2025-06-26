#!/usr/bin/env python3
"""
Setup script for Podcast Scraper

Installs dependencies and sets up the environment for podcast scraping.
"""

import subprocess
import sys
from pathlib import Path


def run_command(command: list, description: str):
    """Run a command and handle errors"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"Error: {e.stderr}")
        return False


def main():
    """Setup the podcast scraper environment"""
    print("🚀 Setting up Podcast Scraper")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    
    print(f"✅ Python {sys.version.split()[0]} detected")
    
    # Install requirements
    if not run_command([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      "Installing Python dependencies"):
        print("Please install dependencies manually:")
        print("  pip install -r requirements.txt")
        sys.exit(1)
    
    # Install Playwright browser
    if not run_command([sys.executable, "-m", "playwright", "install", "chromium"], 
                      "Installing Playwright browser"):
        print("Please install Playwright browser manually:")
        print("  playwright install chromium")
        sys.exit(1)
    
    # Create data directories
    data_dir = Path("data")
    directories = ["json", "markdown", "csv", "fixed_transcripts"]
    
    for dir_name in directories:
        dir_path = data_dir / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
    
    print("✅ Created data directories")
    
    print("\n🎉 Setup complete!")
    print("\nNext steps:")
    print("1. Test the scraper: python scripts/generic_scraper.py")
    print("2. Run examples: python examples/example_usage.py")
    print("3. Fix transcripts: python scripts/fix_transcripts.py --test")
    print("\nFor custom podcasts:")
    print("- Edit the configuration in scripts/generic_scraper.py")
    print("- Or use scripts/config/podcast_configs.py for templates")


if __name__ == "__main__":
    main()