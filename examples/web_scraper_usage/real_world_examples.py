#!/usr/bin/env python3
"""Real-world web scraping examples."""

import asyncio
from pathlib import Path
from research_scrapers.web_scraper import (
    WebScraper, ScraperConfig, ExtractionConfig, 
    PaginationConfig, RateLimitConfig, get_preset
)


async def news_article_scraping():
    """Example: Scraping news articles."""
    print("=== News Article Scraping Example ===")
    
    # Use article preset with customizations
    config = get_preset("article")
    config.extraction.selectors = {
        "headline": "h1, .headline, .article-title",
        "byline": ".byline, .author, [rel='author']",
        "date": "time, .date, .published-date",
        "content": "article, .article-body, .content",
        "tags": ".tags a, .categories a"
    }
    config.extraction.method = "targeted"
    
    scraper = WebScraper(config)
    
    try:
        # Example URLs (replace with real news sites)
        urls = [
            "https://httpbin.org/html",  # Placeholder
        ]
        
        for url in urls:
            result = await scraper.scrape_url(url)
            
            print(f"\nArticle: {url}")
            print(f"Success: {result['success']}")
            
            if result['success']:
                extracted = result.get('extracted', {})
                print(f"Headline: {extracted.get('headline', 'N/A')}")
                print(f"Author: {extracted.get('byline', 'N/A')}")
                print(f"Date: {extracted.get('date', 'N/A')}")
                
                content = extracted.get('content', '')
                if content:
                    print(f"Content preview: {content[:200]}...")
    
    finally:
        await scraper.close()


async def documentation_scraping():
    """Example: Scraping technical documentation with pagination."""
    print("\n=== Documentation Scraping Example ===")
    
    config = get_preset("documentation")
    config.pagination.max_pages = 5  # Limit for example
    
    scraper = WebScraper(config)
    
    try:
        # Example documentation URL
        url = "https://httpbin.org/html"
        
        results = await scraper.scrape_with_pagination(url)
        
        print(f"Documentation scraping: {url}")
        print(f"Total pages scraped: {len(results)}")
        
        for i, result in enumerate(results):
            if result['success']:
                content_length = len(result.get('content', ''))
                links_count = len(result.get('links', []))
                print(f"Page {i+1}: {content_length} chars, {links_count} links")
    
    finally:
        await scraper.close()


async def ecommerce_product_scraping():
    """Example: Scraping e-commerce product information."""
    print("\n=== E-commerce Product Scraping Example ===")
    
    config = ScraperConfig(
        rate_limit=RateLimitConfig(
            requests_per_second=0.5,  # Be respectful to e-commerce sites
            burst_size=2
        ),
        extraction=ExtractionConfig(
            method="targeted",
            selectors={
                "title": "h1, .product-title, [data-testid='product-title']",
                "price": ".price, .cost, [data-testid='price']",
                "description": ".description, .product-description",
                "images": "img.product-image, .gallery img",
                "rating": ".rating, .stars, [data-testid='rating']",
                "availability": ".stock, .availability, [data-testid='stock']"
            },
            extract_metadata=True
        )
    )
    
    scraper = WebScraper(config)
    
    try:
        # Placeholder URL (replace with real product pages)
        url = "https://httpbin.org/html"
        
        result = await scraper.scrape_url(url)
        
        print(f"Product scraping: {url}")
        print(f"Success: {result['success']}")
        
        if result['success']:
            extracted = result.get('extracted', {})
            print(f"Title: {extracted.get('title', 'N/A')}")
            print(f"Price: {extracted.get('price', 'N/A')}")
            print(f"Rating: {extracted.get('rating', 'N/A')}")
            print(f"Availability: {extracted.get('availability', 'N/A')}")
    
    finally:
        await scraper.close()


async def research_paper_scraping():
    """Example: Scraping academic research papers."""
    print("\n=== Research Paper Scraping Example ===")
    
    config = ScraperConfig(
        user_agent="AcademicResearchBot/1.0 (+https://university.edu/research)",
        rate_limit=RateLimitConfig(
            requests_per_second=0.3,  # Very respectful rate
            burst_size=1
        ),
        extraction=ExtractionConfig(
            method="targeted",
            selectors={
                "title": "h1, .article-title, .paper-title",
                "authors": ".authors, .author-list, [data-testid='authors']",
                "abstract": ".abstract, .summary",
                "keywords": ".keywords, .tags",
                "doi": "[data-testid='doi'], .doi",
                "publication_date": ".pub-date, .date",
                "journal": ".journal, .publication",
                "content": ".paper-body, .article-content"
            },
            extract_metadata=True,
            extract_links=True
        )
    )
    
    scraper = WebScraper(config)
    
    try:
        # Placeholder URL (replace with real paper URLs)
        url = "https://httpbin.org/html"
        
        result = await scraper.scrape_url(url)
        
        print(f"Research paper scraping: {url}")
        print(f"Success: {result['success']}")
        
        if result['success']:
            extracted = result.get('extracted', {})
            print(f"Title: {extracted.get('title', 'N/A')}")
            print(f"Authors: {extracted.get('authors', 'N/A')}")
            print(f"DOI: {extracted.get('doi', 'N/A')}")
            
            abstract = extracted.get('abstract', '')
            if abstract:
                print(f"Abstract preview: {abstract[:200]}...")
    
    finally:
        await scraper.close()


async def social_media_scraping():
    """Example: Scraping social media posts (public content only)."""
    print("\n=== Social Media Scraping Example ===")
    
    # Note: Always respect platform terms of service and rate limits
    config = ScraperConfig(
        rate_limit=RateLimitConfig(
            requests_per_second=0.2,  # Very conservative
            burst_size=1
        ),
        extraction=ExtractionConfig(
            method="targeted",
            selectors={
                "username": ".username, .handle, [data-testid='username']",
                "post_text": ".post-content, .tweet-text, .message",
                "timestamp": "time, .timestamp, .date",
                "likes": ".likes, .hearts, [data-testid='likes']",
                "shares": ".shares, .retweets, [data-testid='shares']",
                "hashtags": ".hashtag, [data-testid='hashtag']"
            },
            extract_metadata=True
        )
    )
    
    scraper = WebScraper(config)
    
    try:
        # Placeholder URL (replace with public social media URLs)
        url = "https://httpbin.org/html"
        
        result = await scraper.scrape_url(url)
        
        print(f"Social media scraping: {url}")
        print(f"Success: {result['success']}")
        
        if result['success']:
            extracted = result.get('extracted', {})
            print(f"Username: {extracted.get('username', 'N/A')}")
            print(f"Timestamp: {extracted.get('timestamp', 'N/A')}")
            
            post_text = extracted.get('post_text', '')
            if post_text:
                print(f"Post preview: {post_text[:100]}...")
    
    finally:
        await scraper.close()


async def forum_discussion_scraping():
    """Example: Scraping forum discussions and threads."""
    print("\n=== Forum Discussion Scraping Example ===")
    
    config = ScraperConfig(
        extraction=ExtractionConfig(
            method="targeted",
            selectors={
                "thread_title": "h1, .thread-title, .topic-title",
                "posts": ".post, .message, .comment",
                "usernames": ".username, .author, .poster",
                "timestamps": ".timestamp, .date, .post-date",
                "post_content": ".post-body, .message-content",
                "vote_counts": ".votes, .score, .points"
            },
            extract_metadata=True
        ),
        pagination=PaginationConfig(
            enabled=True,
            method="next_button",
            next_selector="a.next-page, .pagination-next",
            max_pages=10
        )
    )
    
    scraper = WebScraper(config)
    
    try:
        # Placeholder URL (replace with real forum URLs)
        url = "https://httpbin.org/html"
        
        results = await scraper.scrape_with_pagination(url)
        
        print(f"Forum scraping: {url}")
        print(f"Total pages scraped: {len(results)}")
        
        for i, result in enumerate(results):
            if result['success']:
                extracted = result.get('extracted', {})
                posts = extracted.get('posts', [])
                if isinstance(posts, list):
                    print(f"Page {i+1}: {len(posts)} posts found")
                else:
                    print(f"Page {i+1}: Post content extracted")
    
    finally:
        await scraper.close()


if __name__ == "__main__":
    async def main():
        print("Running real-world scraping examples...")
        print("Note: These examples use placeholder URLs.")
        print("Replace with real URLs and respect website terms of service.\n")
        
        await news_article_scraping()
        await documentation_scraping()
        await ecommerce_product_scraping()
        await research_paper_scraping()
        await social_media_scraping()
        await forum_discussion_scraping()
        
        print("\n=== Important Reminders ===")
        print("1. Always check robots.txt and respect rate limits")
        print("2. Review website terms of service before scraping")
        print("3. Consider the legal and ethical implications")
        print("4. Use scraped data responsibly")
        print("5. Provide proper attribution when required")
    
    asyncio.run(main())
