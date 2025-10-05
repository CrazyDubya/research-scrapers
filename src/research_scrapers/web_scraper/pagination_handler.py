"""Pagination handling for web scraping."""

import re
import time
from typing import Optional, List, Dict, Any, Generator
from urllib.parse import urljoin, urlparse, parse_qs, urlencode, urlunparse
from bs4 import BeautifulSoup
from loguru import logger


class PaginationHandler:
    """Handle different types of pagination."""
    
    def __init__(
        self,
        method: str = "next_button",
        next_selector: Optional[str] = None,
        page_number_pattern: Optional[str] = None,
        max_pages: int = 10,
        wait_between_pages: float = 2.0,
    ):
        """
        Initialize pagination handler.
        
        Args:
            method: Pagination method (next_button, numbered, infinite_scroll, url_pattern)
            next_selector: CSS selector for next page button
            page_number_pattern: URL pattern with {page} placeholder
            max_pages: Maximum pages to scrape
            wait_between_pages: Delay between page requests
        """
        self.method = method.lower()
        self.next_selector = next_selector or self._get_default_next_selector()
        self.page_number_pattern = page_number_pattern
        self.max_pages = max_pages
        self.wait_between_pages = wait_between_pages
        
        self.current_page = 1
        self.visited_urls = set()
        
        logger.info(
            f"Initialized PaginationHandler: method={method}, "
            f"max_pages={max_pages}, wait={wait_between_pages}s"
        )
    
    def _get_default_next_selector(self) -> str:
        """Get default next page selector."""
        return (
            "a[rel='next'], "
            ".next-page, "
            ".pagination-next, "
            "a:contains('Next'), "
            "a:contains('→'), "
            "a:contains('»')"
        )
    
    def get_page_urls(self, start_url: str, html: Optional[str] = None) -> Generator[str, None, None]:
        """Generate URLs for all pages."""
        if self.method == "next_button":
            yield from self._handle_next_button_pagination(start_url, html)
        elif self.method == "numbered":
            yield from self._handle_numbered_pagination(start_url)
        elif self.method == "url_pattern":
            yield from self._handle_url_pattern_pagination()
        else:
            logger.warning(f"Unknown pagination method: {self.method}")
            yield start_url
    
    def _handle_next_button_pagination(self, start_url: str, html: Optional[str] = None) -> Generator[str, None, None]:
        """Handle next button pagination."""
        current_url = start_url
        page_count = 0
        
        while current_url and page_count < self.max_pages:
            if current_url in self.visited_urls:
                logger.warning(f"Already visited URL: {current_url}")
                break
            
            self.visited_urls.add(current_url)
            yield current_url
            
            page_count += 1
            self.current_page = page_count + 1
            
            if page_count >= self.max_pages:
                break
            
            # Find next page URL
            if html:
                next_url = self._find_next_url(html, current_url)
                if next_url:
                    current_url = next_url
                    if self.wait_between_pages > 0:
                        time.sleep(self.wait_between_pages)
                else:
                    break
            else:
                break
    
    def _handle_numbered_pagination(self, start_url: str) -> Generator[str, None, None]:
        """Handle numbered pagination."""
        base_url = self._extract_base_url(start_url)
        
        for page_num in range(1, self.max_pages + 1):
            url = self._build_numbered_url(base_url, page_num)
            if url not in self.visited_urls:
                self.visited_urls.add(url)
                yield url
                
                if self.wait_between_pages > 0 and page_num < self.max_pages:
                    time.sleep(self.wait_between_pages)
    
    def _handle_url_pattern_pagination(self) -> Generator[str, None, None]:
        """Handle URL pattern pagination."""
        if not self.page_number_pattern:
            logger.error("Page number pattern required for url_pattern method")
            return
        
        for page_num in range(1, self.max_pages + 1):
            url = self.page_number_pattern.format(page=page_num)
            if url not in self.visited_urls:
                self.visited_urls.add(url)
                yield url
                
                if self.wait_between_pages > 0 and page_num < self.max_pages:
                    time.sleep(self.wait_between_pages)
    
    def _find_next_url(self, html: str, current_url: str) -> Optional[str]:
        """Find next page URL from HTML."""
        soup = BeautifulSoup(html, "lxml")
        
        # Try configured selector
        if self.next_selector:
            next_link = soup.select_one(self.next_selector)
            if next_link and next_link.get("href"):
                next_url = urljoin(current_url, next_link["href"])
                logger.debug(f"Found next page: {next_url}")
                return next_url
        
        # Try common patterns
        next_patterns = [
            "a[rel='next']",
            "a.next",
            "a.next-page",
            "a.pagination-next",
            ".pagination a:last-child",
        ]
        
        for pattern in next_patterns:
            next_link = soup.select_one(pattern)
            if next_link and next_link.get("href"):
                next_url = urljoin(current_url, next_link["href"])
                logger.debug(f"Found next page with pattern '{pattern}': {next_url}")
                return next_url
        
        # Try text-based search
        for link in soup.find_all("a", href=True):
            text = link.get_text(strip=True).lower()
            if any(keyword in text for keyword in ["next", "→", "»", "more"]):
                next_url = urljoin(current_url, link["href"])
                logger.debug(f"Found next page by text '{text}': {next_url}")
                return next_url
        
        logger.debug("No next page found")
        return None
    
    def _extract_base_url(self, url: str) -> str:
        """Extract base URL for numbered pagination."""
        parsed = urlparse(url)
        
        # Remove page parameter if present
        query_params = parse_qs(parsed.query)
        page_params = ["page", "p", "offset", "start"]
        
        for param in page_params:
            if param in query_params:
                del query_params[param]
        
        # Rebuild URL
        new_query = urlencode(query_params, doseq=True)
        return urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            ""
        ))
    
    def _build_numbered_url(self, base_url: str, page_num: int) -> str:
        """Build URL for specific page number."""
        parsed = urlparse(base_url)
        query_params = parse_qs(parsed.query)
        
        # Add page parameter
        query_params["page"] = [str(page_num)]
        
        new_query = urlencode(query_params, doseq=True)
        return urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            ""
        ))
    
    def detect_pagination_type(self, html: str, url: str) -> Dict[str, Any]:
        """Detect pagination type and configuration."""
        soup = BeautifulSoup(html, "lxml")
        
        result = {
            "has_pagination": False,
            "type": None,
            "next_selector": None,
            "total_pages": None,
            "current_page": None,
        }
        
        # Check for next button
        next_selectors = [
            "a[rel='next']",
            "a.next",
            "a.next-page",
            "a.pagination-next",
        ]
        
        for selector in next_selectors:
            if soup.select_one(selector):
                result["has_pagination"] = True
                result["type"] = "next_button"
                result["next_selector"] = selector
                break
        
        # Check for numbered pagination
        pagination_containers = soup.select(".pagination, .pager, .page-numbers")
        for container in pagination_containers:
            page_links = container.find_all("a", href=True)
            if len(page_links) > 1:
                result["has_pagination"] = True
                if not result["type"]:
                    result["type"] = "numbered"
                
                # Try to extract total pages
                page_numbers = []
                for link in page_links:
                    text = link.get_text(strip=True)
                    if text.isdigit():
                        page_numbers.append(int(text))
                
                if page_numbers:
                    result["total_pages"] = max(page_numbers)
                
                break
        
        # Check URL for page parameter
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        
        for param in ["page", "p", "offset"]:
            if param in query_params:
                try:
                    current_page = int(query_params[param][0])
                    result["current_page"] = current_page
                    if not result["has_pagination"]:
                        result["has_pagination"] = True
                        result["type"] = "url_parameter"
                except ValueError:
                    pass
        
        return result
    
    def reset(self) -> None:
        """Reset pagination state."""
        self.current_page = 1
        self.visited_urls.clear()
        logger.debug("Reset pagination state")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pagination statistics."""
        return {
            "method": self.method,
            "current_page": self.current_page,
            "visited_urls": len(self.visited_urls),
            "max_pages": self.max_pages,
        }
