#!/usr/bin/env python3
"""Selenium scraping example for JavaScript-heavy sites.

This script demonstrates how to use Selenium for scraping dynamic content.
"""

import sys
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from research_scrapers.scraper import SeleniumScraper
from research_scrapers import Config
from research_scrapers.utils import setup_logging, save_to_json, create_output_directory


def main():
    """Main function to demonstrate Selenium scraping."""
    # Setup logging
    logger = setup_logging(level='INFO')
    logger.info("Starting Selenium scraping example")
    
    # Create output directory
    output_dir = create_output_directory('output', 'selenium_scraping')
    logger.info(f"Output directory: {output_dir}")
    
    # Configure scraper
    config = Config()
    config.RATE_LIMIT = 0.5  # Slower for Selenium
    config.SELENIUM_HEADLESS = True  # Set to False to see browser
    config.SELENIUM_BROWSER = 'chrome'
    
    # Create Selenium scraper
    scraper = SeleniumScraper(config, browser='chrome', headless=True)
    
    # Example sites with dynamic content
    sites = [
        {
            'url': 'https://quotes.toscrape.com/js/',
            'wait_for': '.quote',
            'selector': '.quote',
            'description': 'JavaScript-loaded quotes'
        },
        {
            'url': 'https://httpbin.org/delay/2',
            'wait_for': None,
            'selector': 'pre',
            'description': 'Delayed response test'
        }
    ]
    
    results = []
    
    try:
        for i, site in enumerate(sites, 1):
            logger.info(f"Scraping {i}/{len(sites)}: {site['description']}")
            logger.info(f"URL: {site['url']}")
            
            try:
                # Scrape with Selenium
                result = scraper.scrape(
                    url=site['url'],
                    selector=site['selector'],
                    wait_for_element=site['wait_for']
                )
                
                # Add metadata
                result['description'] = site['description']
                results.append(result)
                
                # Log results
                logger.info(f"Title: {result.get('title', 'No title')}")
                if 'selected_content' in result:
                    logger.info(f"Selected elements: {len(result['selected_content'])}")
                
                # Save individual result
                filename = f"selenium_result_{i:02d}.json"
                save_to_json(result, output_dir / filename)
                
            except Exception as e:
                logger.error(f"Failed to scrape {site['url']}: {e}")
                continue
    
    finally:
        # Clean up
        scraper.close()
    
    # Save all results
    if results:
        save_to_json(results, output_dir / 'selenium_results.json')
        logger.info(f"Scraped {len(results)} sites successfully")
        logger.info(f"Results saved to: {output_dir}")
    else:
        logger.warning("No results to save")


if __name__ == '__main__':
    main()
