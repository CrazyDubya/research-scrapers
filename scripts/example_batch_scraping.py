#!/usr/bin/env python3
"""Batch scraping example with rate limiting and error handling.

This script demonstrates how to scrape multiple URLs efficiently with proper
rate limiting, error handling, and progress tracking.
"""

import sys
from pathlib import Path
from typing import List, Dict, Any

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from research_scrapers import WebScraper, Config
from research_scrapers.utils import (
    setup_logging, save_to_json, create_output_directory,
    batch_process, validate_url
)


def load_urls_from_file(file_path: Path) -> List[str]:
    """Load URLs from a text file (one URL per line).
    
    Args:
        file_path: Path to file containing URLs
    
    Returns:
        List of valid URLs
    """
    urls = []
    
    if not file_path.exists():
        # Create example file if it doesn't exist
        example_urls = [
            'https://httpbin.org/html',
            'https://httpbin.org/json',
            'https://example.com',
            'https://httpbin.org/user-agent',
            'https://httpbin.org/headers'
        ]
        
        with open(file_path, 'w') as f:
            for url in example_urls:
                f.write(f"{url}\n")
        
        print(f"Created example URL file: {file_path}")
        return example_urls
    
    with open(file_path, 'r') as f:
        for line_num, line in enumerate(f, 1):
            url = line.strip()
            if url and not url.startswith('#'):  # Skip empty lines and comments
                if validate_url(url):
                    urls.append(url)
                else:
                    print(f"Warning: Invalid URL on line {line_num}: {url}")
    
    return urls


def scrape_batch(scraper: WebScraper, urls: List[str], output_dir: Path) -> List[Dict[str, Any]]:
    """Scrape a batch of URLs with error handling.
    
    Args:
        scraper: WebScraper instance
        urls: List of URLs to scrape
        output_dir: Directory to save results
    
    Returns:
        List of successful scraping results
    """
    logger = setup_logging()
    results = []
    errors = []
    
    for i, url in enumerate(urls, 1):
        logger.info(f"Scraping {i}/{len(urls)}: {url}")
        
        try:
            # Scrape the URL
            result = scraper.scrape(url)
            
            # Add metadata
            result['batch_index'] = i
            result['success'] = True
            
            results.append(result)
            
            # Log success
            title = result.get('title', 'No title')[:50]
            logger.info(f"✓ Success: {title}...")
            
            # Save individual result
            filename = f"batch_result_{i:03d}.json"
            save_to_json(result, output_dir / filename)
            
        except Exception as e:
            error_info = {
                'url': url,
                'batch_index': i,
                'error': str(e),
                'error_type': type(e).__name__
            }
            errors.append(error_info)
            logger.error(f"✗ Failed: {e}")
    
    # Save error log
    if errors:
        save_to_json(errors, output_dir / 'errors.json')
        logger.warning(f"Encountered {len(errors)} errors. See errors.json for details.")
    
    return results


def main():
    """Main function for batch scraping."""
    # Setup logging
    logger = setup_logging(level='INFO')
    logger.info("Starting batch scraping example")
    
    # Create output directory
    output_dir = create_output_directory('output', 'batch_scraping')
    logger.info(f"Output directory: {output_dir}")
    
    # Load URLs
    urls_file = Path('scripts/urls.txt')
    urls = load_urls_from_file(urls_file)
    logger.info(f"Loaded {len(urls)} URLs from {urls_file}")
    
    if not urls:
        logger.error("No URLs to scrape")
        return
    
    # Configure scraper for batch processing
    config = Config()
    config.RATE_LIMIT = 2.0  # 2 requests per second
    config.REQUEST_TIMEOUT = 30
    config.MAX_RETRIES = 2  # Fewer retries for batch processing
    
    # Create scraper
    scraper = WebScraper(config)
    
    try:
        # Process URLs in batches
        batch_size = 5
        url_batches = batch_process(urls, batch_size)
        
        logger.info(f"Processing {len(url_batches)} batches of up to {batch_size} URLs each")
        
        all_results = []
        
        for batch_num, batch_urls in enumerate(url_batches, 1):
            logger.info(f"Processing batch {batch_num}/{len(url_batches)}")
            
            # Create batch output directory
            batch_dir = output_dir / f"batch_{batch_num:02d}"
            batch_dir.mkdir(exist_ok=True)
            
            # Scrape batch
            batch_results = scrape_batch(scraper, batch_urls, batch_dir)
            all_results.extend(batch_results)
            
            logger.info(f"Batch {batch_num} complete: {len(batch_results)}/{len(batch_urls)} successful")
    
    finally:
        # Clean up
        scraper.close()
    
    # Save summary
    if all_results:
        save_to_json(all_results, output_dir / 'all_results.json')
        
        # Generate summary statistics
        summary = {
            'total_urls': len(urls),
            'successful_scrapes': len(all_results),
            'success_rate': len(all_results) / len(urls) * 100,
            'output_directory': str(output_dir),
            'configuration': config.to_dict()
        }
        
        save_to_json(summary, output_dir / 'summary.json')
        
        logger.info(f"Batch scraping complete!")
        logger.info(f"Success rate: {summary['success_rate']:.1f}% ({len(all_results)}/{len(urls)})")
        logger.info(f"Results saved to: {output_dir}")
    else:
        logger.error("No successful scrapes")


if __name__ == '__main__':
    main()
