"""Main web scraper implementation."""

import asyncio
import time
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import json
import requests
from loguru import logger
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from .config import ScraperConfig
from .rate_limiter import RateLimiter
from .robots_handler import RobotsHandler
from .auth_manager import AuthManager
from .content_extractor import ContentExtractor
from .pagination_handler import PaginationHandler


class WebScraper:
    """Comprehensive web scraper for research purposes."""
    
    def __init__(self, config: Optional[ScraperConfig] = None):
        """
        Initialize web scraper.
        
        Args:
            config: Scraper configuration
        """
        self.config = config or ScraperConfig()
        
        # Initialize components
        self.rate_limiter = RateLimiter(
            requests_per_second=self.config.rate_limit.requests_per_second,
            burst_size=self.config.rate_limit.burst_size,
            backoff_factor=self.config.rate_limit.backoff_factor,
            max_retries=self.config.rate_limit.max_retries,
        )
        
        self.robots_handler = RobotsHandler(
            user_agent=self.config.user_agent,
            cache_time=self.config.robots_txt_cache_time,
            respect_robots=self.config.respect_robots_txt,
        )
        
        self.auth_manager = AuthManager(
            auth_type=self.config.auth.auth_type,
            username=self.config.auth.username,
            password=self.config.auth.password,
            token=self.config.auth.token,
            cookies=self.config.auth.cookies,
            headers=self.config.auth.headers,
            form_login_url=self.config.auth.form_login_url,
            form_fields=self.config.auth.form_fields,
        )
        
        self.content_extractor = ContentExtractor(
            remove_elements=self.config.extraction.remove_elements,
            clean_whitespace=self.config.extraction.clean_whitespace,
            remove_empty_paragraphs=self.config.extraction.remove_empty_paragraphs,
            preserve_formatting=self.config.extraction.preserve_formatting,
            extract_metadata=self.config.extraction.extract_metadata,
            extract_links=self.config.extraction.extract_links,
        )
        
        self.pagination_handler = PaginationHandler(
            method=self.config.pagination.method,
            next_selector=self.config.pagination.next_selector,
            page_number_pattern=self.config.pagination.page_number_pattern,
            max_pages=self.config.pagination.max_pages,
            wait_between_pages=self.config.pagination.wait_between_pages,
        )
        
        # Browser context for Playwright
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        
        logger.info("Initialized WebScraper")
    
    async def scrape_url(self, url: str, **kwargs) -> Dict[str, Any]:
        """Scrape a single URL."""
        logger.info(f"Scraping URL: {url}")
        
        # Check robots.txt
        if not self.robots_handler.can_fetch(url):
            return {
                "url": url,
                "error": "Blocked by robots.txt",
                "success": False,
            }
        
        # Apply rate limiting
        await self.rate_limiter.async_wait_if_needed(url)
        
        # Get crawl delay from robots.txt
        crawl_delay = self.robots_handler.get_crawl_delay(url)
        if crawl_delay:
            logger.debug(f"Applying robots.txt crawl delay: {crawl_delay}s")
            await asyncio.sleep(crawl_delay)
        
        try:
            if self.config.browser.enabled:
                return await self._scrape_with_browser(url, **kwargs)
            else:
                return await self._scrape_with_requests(url, **kwargs)
        
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return {
                "url": url,
                "error": str(e),
                "success": False,
            }
    
    async def scrape_multiple(self, urls: List[str], **kwargs) -> List[Dict[str, Any]]:
        """Scrape multiple URLs."""
        logger.info(f"Scraping {len(urls)} URLs")
        
        results = []
        for url in urls:
            result = await self.scrape_url(url, **kwargs)
            results.append(result)
            
            # Small delay between requests
            if len(urls) > 1:
                await asyncio.sleep(0.5)
        
        return results
    
    async def scrape_with_pagination(self, start_url: str, **kwargs) -> List[Dict[str, Any]]:
        """Scrape with pagination support."""
        if not self.config.pagination.enabled:
            return [await self.scrape_url(start_url, **kwargs)]
        
        logger.info(f"Scraping with pagination from: {start_url}")
        
        results = []
        first_page_html = None
        
        # Get first page to analyze pagination
        first_result = await self.scrape_url(start_url, **kwargs)
        if first_result.get("success"):
            results.append(first_result)
            first_page_html = first_result.get("raw_html")
        
        # Generate page URLs
        page_urls = list(self.pagination_handler.get_page_urls(start_url, first_page_html))
        
        # Skip first URL if already scraped
        if page_urls and page_urls[0] == start_url:
            page_urls = page_urls[1:]
        
        # Scrape remaining pages
        for url in page_urls:
            result = await self.scrape_url(url, **kwargs)
            results.append(result)
        
        logger.info(f"Scraped {len(results)} pages")
        return results
    
    async def _scrape_with_requests(self, url: str, **kwargs) -> Dict[str, Any]:
        """Scrape using requests library."""
        session = self.auth_manager.get_session()
        
        # Prepare headers
        headers = {
            "User-Agent": self.config.user_agent,
        }
        headers.update(self.auth_manager.get_auth_headers())
        
        # Make request with retries
        for attempt in range(self.config.rate_limit.max_retries + 1):
            try:
                response = session.get(
                    url,
                    headers=headers,
                    timeout=self.config.timeout,
                    verify=self.config.verify_ssl,
                )
                
                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = self.rate_limiter.handle_retry_after(
                        response.headers.get("Retry-After")
                    )
                    if retry_after > 0:
                        logger.warning(f"Rate limited, waiting {retry_after}s")
                        await asyncio.sleep(retry_after)
                        continue
                
                response.raise_for_status()
                
                # Extract content
                return await self._process_response(url, response.text, response.headers)
            
            except Exception as e:
                if attempt < self.config.rate_limit.max_retries:
                    backoff = self.rate_limiter.calculate_backoff(attempt)
                    logger.warning(f"Attempt {attempt + 1} failed, retrying in {backoff}s: {e}")
                    await asyncio.sleep(backoff)
                else:
                    raise e
    
    async def _scrape_with_browser(self, url: str, **kwargs) -> Dict[str, Any]:
        """Scrape using Playwright browser."""
        if not self.browser:
            await self._init_browser()
        
        page = await self.context.new_page()
        
        try:
            # Set user agent
            if self.config.browser.user_agent:
                await page.set_extra_http_headers({
                    "User-Agent": self.config.browser.user_agent
                })
            
            # Set viewport
            await page.set_viewport_size(self.config.browser.viewport)
            
            # Navigate to page
            await page.goto(
                url,
                wait_until=self.config.browser.wait_for_load_state,
                timeout=self.config.browser.timeout,
            )
            
            # Wait for specific selector if configured
            if self.config.browser.wait_for_selector:
                await page.wait_for_selector(
                    self.config.browser.wait_for_selector,
                    timeout=self.config.browser.timeout,
                )
            
            # Get page content
            html = await page.content()
            
            # Extract content
            return await self._process_response(url, html)
        
        finally:
            await page.close()
    
    async def _process_response(self, url: str, html: str, headers: Optional[Dict] = None) -> Dict[str, Any]:
        """Process response and extract content."""
        result = {
            "url": url,
            "success": True,
            "timestamp": time.time(),
            "raw_html": html if self.config.extraction.method == "full_page" else None,
        }
        
        # Extract content based on method
        if self.config.extraction.method == "auto":
            # Auto-detect content type
            content_type = self.content_extractor.detect_content_type(html)
            if content_type:
                self.config.extraction.content_type = content_type
            
            extracted = self.content_extractor.extract(html, url)
        
        elif self.config.extraction.method == "targeted":
            extracted = self.content_extractor.extract_targeted(
                html, self.config.extraction.selectors, url
            )
        
        elif self.config.extraction.method == "full_page":
            extracted = {
                "url": url,
                "content": html,
                "metadata": self.content_extractor._extract_metadata(
                    BeautifulSoup(html, "lxml")
                ) if self.config.extraction.extract_metadata else {},
            }
        
        else:
            raise ValueError(f"Unknown extraction method: {self.config.extraction.method}")
        
        result.update(extracted)
        
        # Add response headers if available
        if headers:
            result["headers"] = dict(headers)
        
        return result
    
    async def _init_browser(self) -> None:
        """Initialize Playwright browser."""
        playwright = await async_playwright().start()
        
        # Launch browser
        if self.config.browser.browser_type == "chromium":
            self.browser = await playwright.chromium.launch(
                headless=self.config.browser.headless
            )
        elif self.config.browser.browser_type == "firefox":
            self.browser = await playwright.firefox.launch(
                headless=self.config.browser.headless
            )
        elif self.config.browser.browser_type == "webkit":
            self.browser = await playwright.webkit.launch(
                headless=self.config.browser.headless
            )
        else:
            raise ValueError(f"Unknown browser type: {self.config.browser.browser_type}")
        
        # Create context
        context_options = {}
        
        if self.config.browser.user_agent:
            context_options["user_agent"] = self.config.browser.user_agent
        
        # Add authentication cookies/headers
        if self.auth_manager.get_cookies():
            # Note: cookies need to be set per-page in Playwright
            pass
        
        self.context = await self.browser.new_context(**context_options)
        
        logger.info(f"Initialized {self.config.browser.browser_type} browser")
    
    def save_results(self, results: Union[Dict, List[Dict]], output_path: Optional[Path] = None) -> None:
        """Save scraping results to file."""
        if output_path is None:
            output_dir = Path(self.config.output_dir)
            output_dir.mkdir(exist_ok=True)
            timestamp = int(time.time())
            output_path = output_dir / f"scrape_results_{timestamp}.json"
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"Saved results to {output_path}")
    
    async def close(self) -> None:
        """Clean up resources."""
        if self.context:
            await self.context.close()
        
        if self.browser:
            await self.browser.close()
        
        self.auth_manager.close()
        
        logger.info("Closed WebScraper")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get scraper statistics."""
        return {
            "rate_limiter": self.rate_limiter.get_stats(),
            "robots_handler": self.robots_handler.get_stats(),
            "pagination_handler": self.pagination_handler.get_stats(),
            "auth_authenticated": self.auth_manager.is_authenticated(),
        }
