#!/usr/bin/env python3
"""Standalone Stack Overflow scraper script.

This is a convenience wrapper that imports and uses the main Stack Overflow scraper
from the research_scrapers package.

For full documentation and features, see src/research_scrapers/stackoverflow_scraper.py

Author: Stephen Thompson
"""

import sys
from pathlib import Path

# Add src to path to import the package
src_path = Path(__file__).parent / 'src'
sys.path.insert(0, str(src_path))

try:
    from research_scrapers.stackoverflow_scraper import (
        StackOverflowScraper,
        ScrapingOptions,
        main
    )
except ImportError as e:
    print(f"Error importing Stack Overflow scraper: {e}")
    print("Please ensure the research_scrapers package is installed.")
    print("Run: pip install -e .")
    sys.exit(1)


if __name__ == '__main__':
    # Run the main CLI interface
    main()
