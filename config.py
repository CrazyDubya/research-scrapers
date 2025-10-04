"""
Configuration module for GitHub scrapers.

This module centralizes all configuration settings for the research scrapers,
including API credentials, default values, and operational parameters.

Author: Stephen Thompson
"""

import os
from pathlib import Path
from typing import Optional

# =============================================================================
# GITHUB API CONFIGURATION
# =============================================================================

# GitHub Personal Access Token
# Set via environment variable: export GITHUB_TOKEN="your_token_here"
GITHUB_TOKEN: Optional[str] = os.environ.get('GITHUB_TOKEN')

# GitHub API Base URL
GITHUB_API_BASE_URL: str = 'https://api.github.com'

# API Rate Limiting
DEFAULT_RATE_LIMIT: float = 1.0  # requests per second
AUTHENTICATED_RATE_LIMIT: float = 5.0  # requests per second with token

# Request Timeout
DEFAULT_TIMEOUT: int = 30  # seconds

# Retry Configuration
MAX_RETRIES: int = 3
RETRY_BACKOFF_FACTOR: float = 0.3


# =============================================================================
# OUTPUT CONFIGURATION
# =============================================================================

# Default output directory
OUTPUT_DIR: Path = Path('./output')

# Default file formats
DEFAULT_OUTPUT_FORMAT: str = 'json'  # json, csv, pickle
SUPPORTED_FORMATS: list = ['json', 'csv', 'pickle']

# JSON formatting
JSON_INDENT: int = 2
JSON_ENSURE_ASCII: bool = False


# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

# Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL: str = os.environ.get('LOG_LEVEL', 'INFO')

# Log directory
LOG_DIR: Path = Path('./logs')

# Log file naming
LOG_FILE_PREFIX: str = 'github_scraper'
LOG_FILE_EXTENSION: str = '.log'

# Log format
LOG_FORMAT: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT: str = '%Y-%m-%d %H:%M:%S'


# =============================================================================
# SCRAPING CONFIGURATION
# =============================================================================

# Repository Scraping Defaults
DEFAULT_MAX_COMMITS: int = 100
DEFAULT_MAX_ISSUES: int = 100
DEFAULT_MAX_PULL_REQUESTS: int = 100
DEFAULT_MAX_CONTRIBUTORS: int = 100
DEFAULT_MAX_RELEASES: int = 20

# Pagination
DEFAULT_PER_PAGE: int = 100
MAX_PER_PAGE: int = 100

# File tree depth
DEFAULT_FILE_TREE_DEPTH: int = 5
MAX_FILE_TREE_DEPTH: int = 10

# Include/Exclude patterns for file scraping
INCLUDE_FILE_PATTERNS: list = ['*.py', '*.js', '*.java', '*.md', '*.txt', '*.json', '*.yml', '*.yaml']
EXCLUDE_FILE_PATTERNS: list = ['*.pyc', '*.class', '*.o', '*.so', '*.dll', 'node_modules/*', '.git/*']


# =============================================================================
# CACHE CONFIGURATION
# =============================================================================

# Enable caching
ENABLE_CACHE: bool = True

# Cache directory
CACHE_DIR: Path = Path('./.cache')

# Cache expiration (seconds)
CACHE_EXPIRATION: int = 3600  # 1 hour

# Cache file naming
CACHE_FILE_EXTENSION: str = '.cache'


# =============================================================================
# DATA PROCESSING CONFIGURATION
# =============================================================================

# Text cleaning
CLEAN_TEXT: bool = True
REMOVE_CONTROL_CHARS: bool = True

# Data validation
VALIDATE_DATA: bool = True
STRICT_VALIDATION: bool = False

# Timestamp format
TIMESTAMP_FORMAT: str = '%Y-%m-%d %H:%M:%S'
ISO_TIMESTAMP_FORMAT: str = '%Y-%m-%dT%H:%M:%SZ'


# =============================================================================
# FEATURE FLAGS
# =============================================================================

# Enable experimental features
ENABLE_EXPERIMENTAL: bool = False

# Enable verbose output
VERBOSE_OUTPUT: bool = False

# Enable progress bars
SHOW_PROGRESS: bool = True

# Enable colored output (if supported)
COLORED_OUTPUT: bool = True


# =============================================================================
# REPOSITORY SCRAPER SPECIFIC
# =============================================================================

# What to scrape by default
SCRAPE_METADATA: bool = True
SCRAPE_STATISTICS: bool = True
SCRAPE_COMMITS: bool = False  # Can be large
SCRAPE_CONTRIBUTORS: bool = True
SCRAPE_LANGUAGES: bool = True
SCRAPE_TOPICS: bool = True
SCRAPE_RELEASES: bool = True
SCRAPE_ISSUES: bool = False  # Can be large
SCRAPE_PULL_REQUESTS: bool = False  # Can be large
SCRAPE_FILE_TREE: bool = True
SCRAPE_README: bool = True
SCRAPE_LICENSE: bool = True

# Detail levels
COMMIT_DETAIL_LEVEL: str = 'basic'  # basic, full
CONTRIBUTOR_DETAIL_LEVEL: str = 'basic'  # basic, full
ISSUE_DETAIL_LEVEL: str = 'basic'  # basic, full


# =============================================================================
# AUTHENTICATION
# =============================================================================

def get_github_token() -> Optional[str]:
    """
    Get GitHub token from environment or config.
    
    Returns:
        GitHub token or None if not set
    """
    return GITHUB_TOKEN


def is_authenticated() -> bool:
    """
    Check if GitHub token is configured.
    
    Returns:
        True if token is available, False otherwise
    """
    return GITHUB_TOKEN is not None and len(GITHUB_TOKEN) > 0


def get_rate_limit() -> float:
    """
    Get appropriate rate limit based on authentication status.
    
    Returns:
        Rate limit in requests per second
    """
    return AUTHENTICATED_RATE_LIMIT if is_authenticated() else DEFAULT_RATE_LIMIT


# =============================================================================
# PATH HELPERS
# =============================================================================

def ensure_directories() -> None:
    """Ensure all required directories exist."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    if ENABLE_CACHE:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)


def get_output_path(filename: str, format: str = DEFAULT_OUTPUT_FORMAT) -> Path:
    """
    Get full output file path.
    
    Args:
        filename: Base filename
        format: Output format (json, csv, pickle)
        
    Returns:
        Full path to output file
    """
    ensure_directories()
    
    if not filename.endswith(f'.{format}'):
        filename = f'{filename}.{format}'
    
    return OUTPUT_DIR / filename


def get_log_path(name: str = LOG_FILE_PREFIX) -> Path:
    """
    Get full log file path.
    
    Args:
        name: Log file name prefix
        
    Returns:
        Full path to log file
    """
    ensure_directories()
    
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y%m%d')
    filename = f'{name}_{timestamp}{LOG_FILE_EXTENSION}'
    
    return LOG_DIR / filename


# =============================================================================
# CONFIGURATION VALIDATION
# =============================================================================

def validate_config() -> bool:
    """
    Validate configuration settings.
    
    Returns:
        True if configuration is valid, False otherwise
    """
    issues = []
    
    # Check token if strict validation
    if STRICT_VALIDATION and not is_authenticated():
        issues.append("GitHub token not configured (GITHUB_TOKEN environment variable)")
    
    # Check rate limits
    if DEFAULT_RATE_LIMIT <= 0:
        issues.append("DEFAULT_RATE_LIMIT must be positive")
    
    # Check timeouts
    if DEFAULT_TIMEOUT <= 0:
        issues.append("DEFAULT_TIMEOUT must be positive")
    
    # Check pagination
    if DEFAULT_PER_PAGE < 1 or DEFAULT_PER_PAGE > MAX_PER_PAGE:
        issues.append(f"DEFAULT_PER_PAGE must be between 1 and {MAX_PER_PAGE}")
    
    if issues:
        print("Configuration validation issues:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    
    return True


# =============================================================================
# INITIALIZATION
# =============================================================================

# Create directories on import
ensure_directories()

# Validate configuration
if __name__ == '__main__':
    if validate_config():
        print("✓ Configuration is valid")
        print(f"  - Authenticated: {is_authenticated()}")
        print(f"  - Rate limit: {get_rate_limit()} req/s")
        print(f"  - Output dir: {OUTPUT_DIR}")
        print(f"  - Log dir: {LOG_DIR}")
    else:
        print("✗ Configuration has issues")
