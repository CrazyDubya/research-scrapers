"""Configuration management for web scraper."""

import yaml
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from pathlib import Path
import json


@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""
    requests_per_second: float = 1.0
    burst_size: int = 5
    respect_retry_after: bool = True
    backoff_factor: float = 2.0
    max_retries: int = 3


@dataclass
class AuthConfig:
    """Authentication configuration."""
    auth_type: str = "none"  # none, basic, bearer, cookie, form
    username: Optional[str] = None
    password: Optional[str] = None
    token: Optional[str] = None
    cookies: Dict[str, str] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    form_login_url: Optional[str] = None
    form_fields: Dict[str, str] = field(default_factory=dict)


@dataclass
class ExtractionConfig:
    """Content extraction configuration."""
    # Extraction method: 'auto', 'targeted', 'full_page'
    method: str = "auto"
    
    # Targeted extraction selectors
    selectors: Dict[str, str] = field(default_factory=dict)
    
    # Content cleaning options
    remove_elements: List[str] = field(default_factory=lambda: [
        "script", "style", "nav", "header", "footer", "aside",
        ".advertisement", ".ad", ".sidebar", ".comments"
    ])
    
    # Content type detection
    auto_detect_content_type: bool = True
    content_type: Optional[str] = None  # article, documentation, blog, forum
    
    # Text processing
    clean_whitespace: bool = True
    remove_empty_paragraphs: bool = True
    preserve_formatting: bool = True
    extract_metadata: bool = True
    
    # Link extraction
    extract_links: bool = False
    follow_links: bool = False
    link_patterns: List[str] = field(default_factory=list)


@dataclass
class PaginationConfig:
    """Pagination configuration."""
    enabled: bool = False
    method: str = "next_button"  # next_button, numbered, infinite_scroll, url_pattern
    next_selector: Optional[str] = None
    page_number_pattern: Optional[str] = None
    max_pages: int = 10
    wait_between_pages: float = 2.0


@dataclass
class BrowserConfig:
    """Browser/Playwright configuration."""
    enabled: bool = False
    headless: bool = True
    browser_type: str = "chromium"  # chromium, firefox, webkit
    user_agent: Optional[str] = None
    viewport: Dict[str, int] = field(default_factory=lambda: {"width": 1920, "height": 1080})
    timeout: int = 30000  # milliseconds
    wait_for_selector: Optional[str] = None
    wait_for_load_state: str = "networkidle"  # load, domcontentloaded, networkidle
    javascript_enabled: bool = True
    stealth_mode: bool = True


@dataclass
class ScraperConfig:
    """Main scraper configuration."""
    # Basic settings
    user_agent: str = "ResearchBot/1.0 (Educational Purpose)"
    timeout: int = 30
    verify_ssl: bool = True
    
    # Robots.txt compliance
    respect_robots_txt: bool = True
    robots_txt_cache_time: int = 3600  # seconds
    
    # Component configurations
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)
    auth: AuthConfig = field(default_factory=AuthConfig)
    extraction: ExtractionConfig = field(default_factory=ExtractionConfig)
    pagination: PaginationConfig = field(default_factory=PaginationConfig)
    browser: BrowserConfig = field(default_factory=BrowserConfig)
    
    # Output settings
    output_format: str = "json"  # json, markdown, html, text
    output_dir: str = "./output"
    
    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    @classmethod
    def from_yaml(cls, path: Path) -> "ScraperConfig":
        """Load configuration from YAML file."""
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)
    
    @classmethod
    def from_json(cls, path: Path) -> "ScraperConfig":
        """Load configuration from JSON file."""
        with open(path, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScraperConfig":
        """Create configuration from dictionary."""
        # Handle nested configurations
        if 'rate_limit' in data:
            data['rate_limit'] = RateLimitConfig(**data['rate_limit'])
        if 'auth' in data:
            data['auth'] = AuthConfig(**data['auth'])
        if 'extraction' in data:
            data['extraction'] = ExtractionConfig(**data['extraction'])
        if 'pagination' in data:
            data['pagination'] = PaginationConfig(**data['pagination'])
        if 'browser' in data:
            data['browser'] = BrowserConfig(**data['browser'])
        
        return cls(**data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return asdict(self)
    
    def to_yaml(self, path: Path) -> None:
        """Save configuration to YAML file."""
        with open(path, 'w') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False)
    
    def to_json(self, path: Path) -> None:
        """Save configuration to JSON file."""
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)


# Preset configurations for common use cases
PRESETS = {
    "article": ScraperConfig(
        extraction=ExtractionConfig(
            method="auto",
            content_type="article",
            remove_elements=[
                "script", "style", "nav", "header", "footer", "aside",
                ".advertisement", ".ad", ".sidebar", ".comments", ".related"
            ],
            extract_metadata=True,
        ),
        rate_limit=RateLimitConfig(requests_per_second=1.0),
    ),
    "documentation": ScraperConfig(
        extraction=ExtractionConfig(
            method="auto",
            content_type="documentation",
            remove_elements=["script", "style", "nav", "header", "footer"],
            extract_links=True,
            link_patterns=[r".*/docs/.*", r".*/api/.*"],
        ),
        pagination=PaginationConfig(
            enabled=True,
            method="next_button",
            next_selector=".next-page, a[rel='next']",
            max_pages=50,
        ),
    ),
    "blog": ScraperConfig(
        extraction=ExtractionConfig(
            method="auto",
            content_type="blog",
            extract_metadata=True,
        ),
        pagination=PaginationConfig(
            enabled=True,
            method="numbered",
            max_pages=20,
        ),
    ),
    "spa": ScraperConfig(
        browser=BrowserConfig(
            enabled=True,
            headless=True,
            wait_for_load_state="networkidle",
            stealth_mode=True,
        ),
        extraction=ExtractionConfig(
            method="auto",
        ),
    ),
}


def get_preset(name: str) -> ScraperConfig:
    """Get a preset configuration by name."""
    if name not in PRESETS:
        raise ValueError(f"Unknown preset: {name}. Available: {list(PRESETS.keys())}")
    return PRESETS[name]
