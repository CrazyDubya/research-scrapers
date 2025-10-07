#!/usr/bin/env python3
"""Setup script for web scraper dependencies."""

import subprocess
import sys
from pathlib import Path


def install_dependencies():
    """Install web scraper dependencies."""
    print("Installing web scraper dependencies...")
    
    # Install Python dependencies
    requirements_file = Path(__file__).parent / "requirements-web-scraper.txt"
    
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ], check=True)
        print("✓ Python dependencies installed")
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install Python dependencies: {e}")
        return False
    
    # Install Playwright browsers
    try:
        subprocess.run([
            sys.executable, "-m", "playwright", "install"
        ], check=True)
        print("✓ Playwright browsers installed")
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install Playwright browsers: {e}")
        print("Note: Playwright is optional for basic scraping")
    
    return True


def run_tests():
    """Run web scraper tests."""
    print("\nRunning web scraper tests...")
    
    try:
        subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/web_scraper/", 
            "-v", "--tb=short"
        ], check=True)
        print("✓ All tests passed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Some tests failed: {e}")
        return False


def main():
    """Main setup function."""
    print("Web Research Scraper Setup")
    print("=" * 30)
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Run tests
    if "--test" in sys.argv:
        if not run_tests():
            sys.exit(1)
    
    print("\n✓ Web scraper setup complete!")
    print("\nUsage examples:")
    print("  python -m research_scrapers.web_scraper.cli scrape https://example.com")
    print("  python examples/web_scraper_usage/basic_scraping.py")
    print("\nDocumentation: docs/web_scraper/README.md")


if __name__ == "__main__":
    main()
