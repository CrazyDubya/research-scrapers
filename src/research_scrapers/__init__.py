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

# New infrastructure classes
from .batch_processor import BatchProcessor, BatchResult, BatchStats, process_batch_simple
from .memory_manager import MemoryManager, MemoryMonitor, MemoryStats, memory_efficient_context
from .structured_logging import StructuredLogger, create_logger, log_execution_time
from .circuit_breaker import CircuitBreaker, CircuitState, with_circuit_breaker, retry_with_backoff

__all__ = [
    # Core scrapers
    "BaseScraper",
    "WebScraper",
    "GitHubScraper",
    "StackOverflowScraper",
    "PatentScraper",
    "Patent",
    "PatentSearchOptions",
    "Config",
    # Utils
    "setup_logging",
    "rate_limit",
    "retry_on_failure",
    "clean_text",
    "save_to_json",
    "load_from_json",
    # Batch processing
    "BatchProcessor",
    "BatchResult",
    "BatchStats",
    "process_batch_simple",
    # Memory management
    "MemoryManager",
    "MemoryMonitor",
    "MemoryStats",
    "memory_efficient_context",
    # Structured logging
    "StructuredLogger",
    "create_logger",
    "log_execution_time",
    # Circuit breaker
    "CircuitBreaker",
    "CircuitState",
    "with_circuit_breaker",
    "retry_with_backoff"
]
