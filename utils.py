"""
Comprehensive utility functions for GitHub scraping and research operations.

This module provides essential utilities for:
- Rate limiting and API management
- Data processing and validation
- File I/O operations
- Logging and error handling
- Response formatting and parsing

Author: Stephen Thompson
"""

import time
import json
import logging
import functools
import os
import csv
import pickle
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Callable
from pathlib import Path
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# =============================================================================
# RATE LIMITING DECORATORS
# =============================================================================

class RateLimiter:
    """Thread-safe rate limiter for API calls."""
    
    def __init__(self, calls_per_second: float = 1.0):
        self.calls_per_second = calls_per_second
        self.min_interval = 1.0 / calls_per_second
        self.last_called = 0.0
    
    def wait(self):
        """Wait if necessary to respect rate limit."""
        now = time.time()
        time_since_last = now - self.last_called
        
        if time_since_last < self.min_interval:
            sleep_time = self.min_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_called = time.time()
    
    def wait_if_needed(self):
        """Alias for wait() method for backward compatibility."""
        self.wait()
    
    def __call__(self, func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            self.wait()
            return func(*args, **kwargs)
        return wrapper


def rate_limit(calls_per_second: float = 1.0):
    """Decorator to rate limit function calls."""
    limiter = RateLimiter(calls_per_second)
    return limiter


def exponential_backoff(max_retries: int = 3, base_delay: float = 1.0):
    """Decorator for exponential backoff retry logic.
    
    Supports both synchronous and asynchronous functions.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries in seconds
    """
    def decorator(func: Callable) -> Callable:
        # Check if function is async
        if hasattr(func, '__code__') and func.__code__.co_flags & 0x100:
            # Async function
            import asyncio
            
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                for attempt in range(max_retries + 1):
                    try:
                        return await func(*args, **kwargs)
                    except Exception as e:
                        if attempt == max_retries:
                            raise e
                        
                        delay = base_delay * (2 ** attempt)
                        logging.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                        await asyncio.sleep(delay)
            return async_wrapper
        else:
            # Sync function
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                for attempt in range(max_retries + 1):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        if attempt == max_retries:
                            raise e
                        
                        delay = base_delay * (2 ** attempt)
                        logging.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
                        time.sleep(delay)
            return wrapper
    return decorator


# =============================================================================
# API RESPONSE PROCESSING
# =============================================================================

class APIResponseProcessor:
    """Process and validate API responses."""
    
    @staticmethod
    def validate_response(response: requests.Response) -> Dict[str, Any]:
        """Validate and parse API response."""
        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 403:
                raise APIError(f"Rate limit exceeded or forbidden: {e}")
            elif response.status_code == 404:
                raise APIError(f"Resource not found: {e}")
            else:
                raise APIError(f"HTTP error {response.status_code}: {e}")
        except json.JSONDecodeError as e:
            raise APIError(f"Invalid JSON response: {e}")
    
    @staticmethod
    def extract_pagination_info(response: requests.Response) -> Dict[str, Optional[str]]:
        """Extract pagination information from response headers."""
        links = response.headers.get('Link', '')
        pagination = {'next': None, 'prev': None, 'first': None, 'last': None}
        
        if links:
            for link in links.split(','):
                parts = link.strip().split(';')
                if len(parts) == 2:
                    url = parts[0].strip('<>')
                    rel = parts[1].strip().split('=')[1].strip('"')
                    pagination[rel] = url
        
        return pagination
    
    @staticmethod
    def get_rate_limit_info(response: requests.Response) -> Dict[str, int]:
        """Extract rate limit information from response headers."""
        return {
            'limit': int(response.headers.get('X-RateLimit-Limit', 0)),
            'remaining': int(response.headers.get('X-RateLimit-Remaining', 0)),
            'reset': int(response.headers.get('X-RateLimit-Reset', 0))
        }


# =============================================================================
# DATA FORMATTING HELPERS
# =============================================================================

class DataFormatter:
    """Format and transform data for various outputs."""
    
    @staticmethod
    def flatten_dict(data: Dict[str, Any], prefix: str = '', separator: str = '.') -> Dict[str, Any]:
        """Flatten nested dictionary structure."""
        flattened = {}
        
        for key, value in data.items():
            new_key = f"{prefix}{separator}{key}" if prefix else key
            
            if isinstance(value, dict):
                flattened.update(DataFormatter.flatten_dict(value, new_key, separator))
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        flattened.update(DataFormatter.flatten_dict(item, f"{new_key}[{i}]", separator))
                    else:
                        flattened[f"{new_key}[{i}]"] = item
            else:
                flattened[new_key] = value
        
        return flattened
    
    @staticmethod
    def normalize_github_data(repo_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize GitHub repository data for consistent processing."""
        normalized = {
            'id': repo_data.get('id'),
            'name': repo_data.get('name'),
            'full_name': repo_data.get('full_name'),
            'owner': repo_data.get('owner', {}).get('login'),
            'description': repo_data.get('description', ''),
            'url': repo_data.get('html_url'),
            'clone_url': repo_data.get('clone_url'),
            'language': repo_data.get('language'),
            'stars': repo_data.get('stargazers_count', 0),
            'forks': repo_data.get('forks_count', 0),
            'watchers': repo_data.get('watchers_count', 0),
            'issues': repo_data.get('open_issues_count', 0),
            'created_at': repo_data.get('created_at'),
            'updated_at': repo_data.get('updated_at'),
            'pushed_at': repo_data.get('pushed_at'),
            'size': repo_data.get('size', 0),
            'is_fork': repo_data.get('fork', False),
            'is_private': repo_data.get('private', False),
            'has_wiki': repo_data.get('has_wiki', False),
            'has_pages': repo_data.get('has_pages', False),
            'license': repo_data.get('license', {}).get('name') if repo_data.get('license') else None,
            'topics': repo_data.get('topics', [])
        }
        
        return normalized
    
    @staticmethod
    def format_timestamp(timestamp: str, format_str: str = '%Y-%m-%d %H:%M:%S') -> str:
        """Format ISO timestamp to readable string."""
        if not timestamp:
            return ''
        
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return dt.strftime(format_str)
        except (ValueError, AttributeError):
            return timestamp


# =============================================================================
# FILE I/O OPERATIONS
# =============================================================================

class FileManager:
    """Handle file operations for data persistence."""
    
    @staticmethod
    def ensure_directory(path: Union[str, Path]) -> Path:
        """Ensure directory exists, create if necessary."""
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    @staticmethod
    def save_json(data: Any, filepath: Union[str, Path], indent: int = 2) -> None:
        """Save data as JSON file."""
        filepath = Path(filepath)
        FileManager.ensure_directory(filepath.parent)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False, default=str)
    
    @staticmethod
    def load_json(filepath: Union[str, Path]) -> Any:
        """Load data from JSON file."""
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    @staticmethod
    def save_csv(data: List[Dict[str, Any]], filepath: Union[str, Path], 
                 fieldnames: Optional[List[str]] = None) -> None:
        """Save data as CSV file."""
        if not data:
            return
        
        filepath = Path(filepath)
        FileManager.ensure_directory(filepath.parent)
        
        if fieldnames is None:
            fieldnames = list(data[0].keys())
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
    
    @staticmethod
    def load_csv(filepath: Union[str, Path]) -> List[Dict[str, Any]]:
        """Load data from CSV file."""
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return list(csv.DictReader(f))
    
    @staticmethod
    def save_pickle(data: Any, filepath: Union[str, Path]) -> None:
        """Save data using pickle."""
        filepath = Path(filepath)
        FileManager.ensure_directory(filepath.parent)
        
        with open(filepath, 'wb') as f:
            pickle.dump(data, f)
    
    @staticmethod
    def load_pickle(filepath: Union[str, Path]) -> Any:
        """Load data from pickle file."""
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        with open(filepath, 'rb') as f:
            return pickle.load(f)


# =============================================================================
# LOGGING SETUP
# =============================================================================

def setup_logging(
    level: str = 'INFO',
    log_file: Optional[str] = None,
    format_string: Optional[str] = None
) -> logging.Logger:
    """Setup comprehensive logging configuration."""
    
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Create logger
    logger = logging.getLogger('github_scraper')
    logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, level.upper()))
    console_formatter = logging.Formatter(format_string)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        FileManager.ensure_directory(Path(log_file).parent)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, level.upper()))
        file_formatter = logging.Formatter(format_string)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


# =============================================================================
# ERROR HANDLING
# =============================================================================

class ScrapingError(Exception):
    """Base exception for scraping operations."""
    pass


class APIError(ScrapingError):
    """Exception for API-related errors."""
    pass


class ValidationError(ScrapingError):
    """Exception for data validation errors."""
    pass


class RateLimitError(APIError):
    """Exception for rate limit violations."""
    pass


def handle_api_errors(func: Callable) -> Callable:
    """Decorator to handle common API errors gracefully."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except requests.exceptions.ConnectionError as e:
            raise APIError(f"Connection error: {e}")
        except requests.exceptions.Timeout as e:
            raise APIError(f"Request timeout: {e}")
        except requests.exceptions.RequestException as e:
            raise APIError(f"Request error: {e}")
        except Exception as e:
            logging.error(f"Unexpected error in {func.__name__}: {e}")
            raise
    return wrapper


# =============================================================================
# DATA VALIDATION UTILITIES
# =============================================================================

class DataValidator:
    """Validate and sanitize scraped data."""
    
    @staticmethod
    def validate_github_repo(repo_data: Dict[str, Any]) -> bool:
        """Validate GitHub repository data structure."""
        required_fields = ['id', 'name', 'full_name', 'owner']
        
        for field in required_fields:
            if field not in repo_data:
                return False
            
            if field == 'owner' and not isinstance(repo_data[field], dict):
                return False
            elif field == 'owner' and 'login' not in repo_data[field]:
                return False
        
        return True
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for safe file system operations."""
        import re
        
        # Remove or replace invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        filename = re.sub(r'\s+', '_', filename)
        filename = filename.strip('._')
        
        # Limit length
        if len(filename) > 200:
            filename = filename[:200]
        
        return filename
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """Validate URL format."""
        import re
        
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        return url_pattern.match(url) is not None
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize text data."""
        if not isinstance(text, str):
            return str(text) if text is not None else ''
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove control characters
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
        
        return text.strip()


# =============================================================================
# HTTP SESSION MANAGEMENT
# =============================================================================

class GitHubAPIClient:
    """GitHub API client with rate limiting and error handling."""
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize GitHub API client.
        
        Args:
            token: GitHub personal access token (optional)
        """
        self.token = token
        self.base_url = "https://api.github.com"
        self.session = self._create_session()
        
    def _create_session(self) -> requests.Session:
        """Create configured session with security headers."""
        session = requests.Session()
        
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'research-scrapers/1.0'
        }
        
        if self.token:
            headers['Authorization'] = f'token {self.token}'
        
        session.headers.update(headers)
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=0.3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
        )
        
        # Mount adapter with retry strategy
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def get(self, url: str, params: Optional[Dict[str, Any]] = None, 
            headers: Optional[Dict[str, str]] = None) -> requests.Response:
        """
        Make GET request.
        
        Args:
            url: URL to request
            params: Query parameters
            headers: Additional headers
            
        Returns:
            Response object
        """
        request_headers = {}
        if headers:
            request_headers.update(headers)
            
        response = self.session.get(url, params=params, headers=request_headers)
        response.raise_for_status()
        return response
    
    def post(self, url: str, json: Optional[Dict[str, Any]] = None,
             data: Optional[Any] = None,
             headers: Optional[Dict[str, str]] = None) -> requests.Response:
        """
        Make POST request.
        
        Args:
            url: URL to request
            json: JSON payload
            data: Form data payload
            headers: Additional headers
            
        Returns:
            Response object
        """
        request_headers = {}
        if headers:
            request_headers.update(headers)
            
        response = self.session.post(url, json=json, data=data, headers=request_headers)
        response.raise_for_status()
        return response
    
    def close(self):
        """Close the session."""
        if hasattr(self, 'session'):
            self.session.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False


def create_session(
    max_retries: int = 3,
    backoff_factor: float = 0.3,
    timeout: int = 30
) -> requests.Session:
    """Create a configured requests session with retry logic."""
    
    session = requests.Session()
    
    # Configure retry strategy
    retry_strategy = Retry(
        total=max_retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    
    # Mount adapter with retry strategy
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # Set default timeout
    session.timeout = timeout
    
    return session


# =============================================================================
# CONFIGURATION MANAGEMENT
# =============================================================================

class Config:
    """Configuration management for scraping operations."""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config = {}
        
        if config_file and Path(config_file).exists():
            self.config = FileManager.load_json(config_file)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save(self, config_file: str) -> None:
        """Save configuration to file."""
        FileManager.save_json(self.config, config_file)


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_timestamp() -> str:
    """Get current timestamp in ISO format."""
    return datetime.now().isoformat()


def parse_github_url(url: str) -> Dict[str, str]:
    """Parse GitHub URL to extract owner and repository name."""
    import re
    
    pattern = r'github\.com/([^/]+)/([^/]+)'
    match = re.search(pattern, url)
    
    if match:
        return {
            'owner': match.group(1),
            'repo': match.group(2).rstrip('.git')
        }
    
    raise ValueError(f"Invalid GitHub URL: {url}")


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split list into chunks of specified size."""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """Merge multiple dictionaries, with later ones taking precedence."""
    result = {}
    for d in dicts:
        result.update(d)
    return result


def safe_get(data: Dict[str, Any], path: str, default: Any = None) -> Any:
    """Safely get nested dictionary value using dot notation.
    
    Args:
        data: Dictionary to extract value from
        path: Dot-notation path to value (e.g., 'user.name')
        default: Default value if path not found
        
    Returns:
        Value at path or default if not found
    """
    if data is None:
        return default
        
    keys = path.split('.')
    value = data
    
    try:
        for key in keys:
            if value is None:
                return default
            value = value[key]
        return value
    except (KeyError, TypeError, AttributeError):
        return default


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    # Setup logging
    logger = setup_logging(level='INFO', log_file='scraper.log')
    
    # Example rate limited function
    @rate_limit(calls_per_second=0.5)
    @exponential_backoff(max_retries=3)
    def example_api_call():
        logger.info("Making API call...")
        return {"status": "success"}
    
    # Example usage
    try:
        result = example_api_call()
        logger.info(f"API call result: {result}")
    except Exception as e:
        logger.error(f"API call failed: {e}")