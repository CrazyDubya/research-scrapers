"""Configuration settings for the research scrapers package."""

import os
from pathlib import Path
from typing import Optional, Dict, Any


class Config:
    """Configuration class for research scrapers."""
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize configuration.
        
        Args:
            config_file: Optional path to configuration file
        """
        # Default settings
        self._load_defaults()
        
        # Load from environment variables
        self._load_from_env()
        
        # Load from config file if provided
        if config_file:
            self._load_from_file(config_file)
    
    def _load_defaults(self):
        """Load default configuration values."""
        # HTTP Settings
        self.REQUEST_TIMEOUT = 30
        self.MAX_RETRIES = 3
        self.RETRY_DELAY = 1.0
        self.RETRY_BACKOFF = 2.0
        self.RATE_LIMIT = 1.0  # requests per second
        
        # User Agent
        self.USER_AGENT = (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        )
        
        # Proxy Settings
        self.PROXY = None
        self.PROXY_USERNAME = None
        self.PROXY_PASSWORD = None
        
        # Output Settings
        self.OUTPUT_DIR = Path('output')
        self.LOG_LEVEL = 'INFO'
        self.LOG_FILE = None
        
        # Database Settings (for future use)
        self.DATABASE_URL = None
        self.DATABASE_POOL_SIZE = 5
        
        # API Keys (for various services)
        self.API_KEYS = {}
        
        # Selenium Settings
        self.SELENIUM_BROWSER = 'chrome'
        self.SELENIUM_HEADLESS = True
        self.SELENIUM_IMPLICIT_WAIT = 10
        
        # Content Processing
        self.MAX_CONTENT_LENGTH = 1000000  # 1MB
        self.ALLOWED_CONTENT_TYPES = [
            'text/html',
            'application/json',
            'text/plain',
            'application/xml',
            'text/xml'
        ]
        
        # File Processing
        self.MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
        self.ALLOWED_FILE_EXTENSIONS = [
            '.txt', '.json', '.csv', '.xml', '.html',
            '.pdf', '.doc', '.docx', '.xls', '.xlsx'
        ]
    
    def _load_from_env(self):
        """Load configuration from environment variables."""
        # HTTP Settings
        if os.getenv('SCRAPER_REQUEST_TIMEOUT'):
            self.REQUEST_TIMEOUT = int(os.getenv('SCRAPER_REQUEST_TIMEOUT'))
        
        if os.getenv('SCRAPER_MAX_RETRIES'):
            self.MAX_RETRIES = int(os.getenv('SCRAPER_MAX_RETRIES'))
        
        if os.getenv('SCRAPER_RATE_LIMIT'):
            self.RATE_LIMIT = float(os.getenv('SCRAPER_RATE_LIMIT'))
        
        # User Agent
        if os.getenv('SCRAPER_USER_AGENT'):
            self.USER_AGENT = os.getenv('SCRAPER_USER_AGENT')
        
        # Proxy Settings
        if os.getenv('SCRAPER_PROXY'):
            self.PROXY = os.getenv('SCRAPER_PROXY')
        
        if os.getenv('SCRAPER_PROXY_USERNAME'):
            self.PROXY_USERNAME = os.getenv('SCRAPER_PROXY_USERNAME')
        
        if os.getenv('SCRAPER_PROXY_PASSWORD'):
            self.PROXY_PASSWORD = os.getenv('SCRAPER_PROXY_PASSWORD')
        
        # Output Settings
        if os.getenv('SCRAPER_OUTPUT_DIR'):
            self.OUTPUT_DIR = Path(os.getenv('SCRAPER_OUTPUT_DIR'))
        
        if os.getenv('SCRAPER_LOG_LEVEL'):
            self.LOG_LEVEL = os.getenv('SCRAPER_LOG_LEVEL')
        
        if os.getenv('SCRAPER_LOG_FILE'):
            self.LOG_FILE = os.getenv('SCRAPER_LOG_FILE')
        
        # Database Settings
        if os.getenv('DATABASE_URL'):
            self.DATABASE_URL = os.getenv('DATABASE_URL')
        
        # API Keys
        api_key_prefixes = ['GITHUB_', 'TWITTER_', 'REDDIT_', 'LINKEDIN_']
        for prefix in api_key_prefixes:
            for key, value in os.environ.items():
                if key.startswith(prefix) and key.endswith('_API_KEY'):
                    service_name = key.replace('_API_KEY', '').lower()
                    self.API_KEYS[service_name] = value
    
    def _load_from_file(self, config_file: str):
        """Load configuration from a file.
        
        Args:
            config_file: Path to configuration file (JSON or YAML)
        """
        config_path = Path(config_file)
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")
        
        if config_path.suffix.lower() == '.json':
            import json
            with open(config_path, 'r') as f:
                config_data = json.load(f)
        elif config_path.suffix.lower() in ['.yml', '.yaml']:
            try:
                import yaml
                with open(config_path, 'r') as f:
                    config_data = yaml.safe_load(f)
            except ImportError:
                raise ImportError("PyYAML is required to load YAML configuration files")
        else:
            raise ValueError(f"Unsupported configuration file format: {config_path.suffix}")
        
        # Update configuration with loaded data
        for key, value in config_data.items():
            if hasattr(self, key.upper()):
                setattr(self, key.upper(), value)
    
    def get_api_key(self, service: str) -> Optional[str]:
        """Get API key for a specific service.
        
        Args:
            service: Service name (e.g., 'github', 'twitter')
        
        Returns:
            API key if available, None otherwise
        """
        return self.API_KEYS.get(service.lower())
    
    def set_api_key(self, service: str, api_key: str):
        """Set API key for a specific service.
        
        Args:
            service: Service name
            api_key: API key value
        """
        self.API_KEYS[service.lower()] = api_key
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary.
        
        Returns:
            Configuration as dictionary
        """
        return {
            key: getattr(self, key)
            for key in dir(self)
            if not key.startswith('_') and not callable(getattr(self, key))
        }
    
    def __repr__(self) -> str:
        """String representation of configuration."""
        return f"Config({self.to_dict()})"
