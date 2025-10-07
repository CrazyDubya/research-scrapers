"""Web Research Scraper Package.

A comprehensive web scraping solution for research purposes with support for:
- HTML parsing with BeautifulSoup and Playwright
- Smart content detection and extraction
- Rate limiting and robots.txt compliance
- Authentication and session management
- Pagination and multi-page navigation
- Content cleaning and processing
"""

from .scraper import WebScraper
from .content_extractor import ContentExtractor
from .rate_limiter import RateLimiter
from .auth_manager import AuthManager
from .pagination_handler import PaginationHandler
from .config import ScraperConfig

__version__ = "1.0.0"

__all__ = [
    "WebScraper",
    "ContentExtractor",
    "RateLimiter",
    "AuthManager",
    "PaginationHandler",
    "ScraperConfig",
]
