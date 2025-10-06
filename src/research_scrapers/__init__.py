"""Research Scrapers Package

A comprehensive toolkit for scraping and analyzing data from various research sources.
"""

__version__ = "0.1.0"
__author__ = "Stephen Thompson"
__email__ = "your.email@example.com"

from .scraper import BaseScraper, WebScraper
from .github_scraper import GitHubScraper
from .stackoverflow_scraper import StackOverflowScraper
from .patent_scraper import PatentScraper, Patent, PatentSearchOptions
from .utils import (
    setup_logging,
    rate_limit,
    retry_on_failure,
    clean_text,
    save_to_json,
    load_from_json
)
from .config import Config

__all__ = [
    "BaseScraper",
    "WebScraper",
    "GitHubScraper",
    "StackOverflowScraper",
    "PatentScraper",
    "Patent",
    "PatentSearchOptions",
    "Config",
    "setup_logging",
    "rate_limit",
    "retry_on_failure",
    "clean_text",
    "save_to_json",
    "load_from_json"
]
