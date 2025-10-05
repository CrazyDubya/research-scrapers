#!/usr/bin/env python3
"""Advanced web scraping examples."""

import asyncio
from pathlib import Path
from research_scrapers.web_scraper import (
    WebScraper, ScraperConfig, ExtractionConfig, 
    PaginationConfig, BrowserConfig, AuthConfig
)


async def targeted_extraction_example():
    """Targeted content extraction using CSS selectors."""
    print("=== Targeted Extraction Example ===")
    
    config = ScraperConfig(
        extraction=ExtractionConfig(
            method="targeted",
            selectors={
                "title": "title",
                "headings": "h1, h2, h3",
                "paragraphs": "p",
                "links": "a[href]"
            },
            extract_metadata=True
        )
    )
    
    scraper = WebScraper(config)
    
    try:
        url = "https://httpbin.org/html"
        result = await scraper.scrape_url(url)
        
        print(f"Targeted extraction from: {url}")
        extracted = result.get('extracted', {})
        
        for key, value in extracted.items():
            if isinstance(value, list):
                print(f"{key}: {len(value)} items")
            else:
                print(f"{key}: {str(value)[:100]}...")
        
    finally:
        await scraper.close()


async def browser_scraping_example():
    """Scraping with browser (Playwright) for JavaScript sites."""
    print("\n=== Browser Scraping Example ===")
    
    config = ScraperConfig(
        browser=BrowserConfig(
            enabled=True,
            headless=True,
            browser_type="chromium",
            wait_for_load_state="networkidle",
            timeout=30000
        ),
        extraction=ExtractionConfig(
            method="auto",
            extract_metadata=True
        )
    )
    
    scraper = WebScraper(config)
    
    try:
        # This example uses a simple page, but would work with SPA/JavaScript sites
        url = "https://httpbin.org/html"
        result = await scraper.scrape_url(url)
        
        print(f"Browser scraping: {url}")
        print(f"Success: {result['success']}")
        print(f"Content extracted: {len(result.get('content', ''))} characters")
        
    finally:
        await scraper.close()


async def pagination_example():
    """Scraping with pagination support."""
    print("\n=== Pagination Example ===")
    
    config = ScraperConfig(
        pagination=PaginationConfig(
            enabled=True,
            method="next_button",
            next_selector="a[rel='next']",
            max_pages=3,
            wait_between_pages=1.0
        ),
        extraction=ExtractionConfig(
            method="auto",
            extract_metadata=True
        )
    )
    
    scraper = WebScraper(config)
    
    try:
        # Note: This example URL doesn't have pagination,
        # but demonstrates the configuration
        url = "https://httpbin.org/html"
        results = await scraper.scrape_with_pagination(url)
        
        print(f"Pagination scraping from: {url}")
        print(f"Total pages scraped: {len(results)}")
        
        for i, result in enumerate(results):
            print(f"Page {i+1}: {result['url']} - Success: {result['success']}")
        
    finally:
        await scraper.close()


async def authenticated_scraping_example():
    """Scraping with authentication."""
    print("\n=== Authenticated Scraping Example ===")
    
    # Example with custom headers (simulating authentication)
    config = ScraperConfig(
        auth=AuthConfig(
            auth_type="none",  # Using custom headers instead
            headers={
                "Authorization": "Bearer fake-token",
                "X-API-Key": "fake-api-key",
                "User-Agent": "MyResearchBot/1.0"
            }
        ),
        extraction=ExtractionConfig(
            method="auto",
            extract_metadata=True
        )
    )
    
    scraper = WebScraper(config)
    
    try:
        # httpbin.org/headers will show the headers we sent
        url = "https://httpbin.org/headers"
        result = await scraper.scrape_url(url)
        
        print(f"Authenticated scraping: {url}")
        print(f"Success: {result['success']}")
        
        # The response should contain our custom headers
        content = result.get('content', '')
        if 'Authorization' in content:
            print("✓ Custom headers were sent successfully")
        
    finally:
        await scraper.close()


async def error_handling_example():
    """Demonstrating error handling and retry logic."""
    print("\n=== Error Handling Example ===")
    
    from research_scrapers.web_scraper import RateLimitConfig
    
    config = ScraperConfig(
        rate_limit=RateLimitConfig(
            max_retries=2,
            backoff_factor=1.5
        ),
        timeout=5  # Short timeout to trigger errors
    )
    
    scraper = WebScraper(config)
    
    try:
        # Try scraping a non-existent URL
        url = "https://httpbin.org/delay/10"  # This will timeout
        result = await scraper.scrape_url(url)
        
        print(f"Scraping with short timeout: {url}")
        print(f"Success: {result['success']}")
        
        if not result['success']:
            print(f"Error: {result.get('error', 'Unknown error')}")
        
        # Try a working URL
        url2 = "https://httpbin.org/html"
        result2 = await scraper.scrape_url(url2)
        print(f"\nWorking URL: {url2}")
        print(f"Success: {result2['success']}")
        
    finally:
        await scraper.close()


async def content_cleaning_example():
    """Demonstrating content cleaning and processing."""
    print("\n=== Content Cleaning Example ===")
    
    config = ScraperConfig(
        extraction=ExtractionConfig(
            method="auto",
            remove_elements=[
                "script", "style", "nav", "header", "footer"
            ],
            clean_whitespace=True,
            remove_empty_paragraphs=True,
            preserve_formatting=True,
            extract_metadata=True
        )
    )
    
    scraper = WebScraper(config)
    
    try:
        url = "https://httpbin.org/html"
        result = await scraper.scrape_url(url)
        
        print(f"Content cleaning example: {url}")
        print(f"Cleaned content length: {len(result.get('content', ''))}")
        print(f"Metadata extracted: {result.get('metadata', {})}")
        
        # Show first part of cleaned content
        content = result.get('content', '')
        if content:
            print(f"Content preview: {content[:200]}...")
        
    finally:
        await scraper.close()


if __name__ == "__main__":
    async def main():
        await targeted_extraction_example()
        # await browser_scraping_example()  # Uncomment if Playwright is installed
        await pagination_example()
        await authenticated_scraping_example()
        await error_handling_example()
        await content_cleaning_example()
    
    asyncio.run(main())
