#!/usr/bin/env python3
"""Basic web scraping examples."""

import asyncio
from pathlib import Path
from research_scrapers.web_scraper import WebScraper, ScraperConfig, get_preset


async def basic_scraping_example():
    """Basic scraping with default configuration."""
    print("=== Basic Scraping Example ===")
    
    scraper = WebScraper()
    
    try:
        # Scrape a single URL
        url = "https://httpbin.org/html"
        result = await scraper.scrape_url(url)
        
        print(f"URL: {result['url']}")
        print(f"Success: {result['success']}")
        print(f"Content length: {len(result.get('content', ''))}")
        print(f"Metadata: {result.get('metadata', {})}")
        
    finally:
        await scraper.close()


async def preset_example():
    """Using preset configurations."""
    print("\n=== Preset Configuration Example ===")
    
    # Use article preset
    config = get_preset("article")
    scraper = WebScraper(config)
    
    try:
        # This would work better with a real article URL
        url = "https://httpbin.org/html"
        result = await scraper.scrape_url(url)
        
        print(f"Using article preset for: {url}")
        print(f"Extracted content: {result.get('content', '')[:200]}...")
        
    finally:
        await scraper.close()


async def multiple_urls_example():
    """Scraping multiple URLs."""
    print("\n=== Multiple URLs Example ===")
    
    scraper = WebScraper()
    
    urls = [
        "https://httpbin.org/html",
        "https://httpbin.org/json",
    ]
    
    try:
        results = await scraper.scrape_multiple(urls)
        
        for i, result in enumerate(results):
            print(f"Result {i+1}: {result['url']} - Success: {result['success']}")
        
    finally:
        await scraper.close()


async def custom_config_example():
    """Using custom configuration."""
    print("\n=== Custom Configuration Example ===")
    
    from research_scrapers.web_scraper import ExtractionConfig, RateLimitConfig
    
    config = ScraperConfig(
        user_agent="MyResearchBot/1.0",
        rate_limit=RateLimitConfig(
            requests_per_second=0.5,  # Slower rate
            burst_size=2
        ),
        extraction=ExtractionConfig(
            method="auto",
            extract_metadata=True,
            clean_whitespace=True
        )
    )
    
    scraper = WebScraper(config)
    
    try:
        url = "https://httpbin.org/html"
        result = await scraper.scrape_url(url)
        
        print(f"Custom config scraping: {url}")
        print(f"Rate limiter stats: {scraper.get_stats()['rate_limiter']}")
        
    finally:
        await scraper.close()


async def save_results_example():
    """Saving results to file."""
    print("\n=== Save Results Example ===")
    
    scraper = WebScraper()
    
    try:
        url = "https://httpbin.org/html"
        result = await scraper.scrape_url(url)
        
        # Save to file
        output_path = Path("./output/basic_scrape_result.json")
        output_path.parent.mkdir(exist_ok=True)
        scraper.save_results(result, output_path)
        
        print(f"Results saved to: {output_path}")
        
    finally:
        await scraper.close()


if __name__ == "__main__":
    async def main():
        await basic_scraping_example()
        await preset_example()
        await multiple_urls_example()
        await custom_config_example()
        await save_results_example()
    
    asyncio.run(main())
