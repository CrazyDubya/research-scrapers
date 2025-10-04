#!/usr/bin/env python3
"""Basic web scraping example.

This script demonstrates basic web scraping functionality using the research_scrapers package.
"""

import sys
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from research_scrapers import WebScraper, Config
from research_scrapers.utils import setup_logging, save_to_json, create_output_directory


def main():
    """Main function to demonstrate basic scraping."""
    # Setup logging
    logger = setup_logging(level='INFO')
    logger.info("Starting basic scraping example")
    
    # Create output directory
    output_dir = create_output_directory('output', 'basic_scraping')
    logger.info(f"Output directory: {output_dir}")
    
    # Configure scraper
    config = Config()
    config.RATE_LIMIT = 1.0  # 1 request per second
    config.REQUEST_TIMEOUT = 30
    
    # Create scraper
    scraper = WebScraper(config)
    
    # URLs to scrape
    urls = [
        'https://httpbin.org/html',
        'https://httpbin.org/json',
        'https://example.com'
    ]
    
    results = []
    
    try:
        for i, url in enumerate(urls, 1):
            logger.info(f"Scraping {i}/{len(urls)}: {url}")
            
            try:
                # Scrape the page
                result = scraper.scrape(url)
                results.append(result)
                
                # Log basic info
                logger.info(f"Title: {result.get('title', 'No title')}")
                logger.info(f"Links found: {len(result.get('links', []))}")
                
                # Save individual result
                filename = f"result_{i:02d}.json"
                save_to_json(result, output_dir / filename)
                
            except Exception as e:
                logger.error(f"Failed to scrape {url}: {e}")
                continue
    
    finally:
        # Clean up
        scraper.close()
    
    # Save all results
    if results:
        save_to_json(results, output_dir / 'all_results.json')
        logger.info(f"Scraped {len(results)} pages successfully")
        logger.info(f"Results saved to: {output_dir}")
    else:
        logger.warning("No results to save")


if __name__ == '__main__':
    main()
