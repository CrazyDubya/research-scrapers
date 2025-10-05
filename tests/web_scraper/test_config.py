"""Tests for configuration management."""

import pytest
import tempfile
import yaml
import json
from pathlib import Path
from research_scrapers.web_scraper.config import (
    ScraperConfig, ExtractionConfig, RateLimitConfig, 
    AuthConfig, PaginationConfig, BrowserConfig, get_preset
)


class TestScraperConfig:
    """Test ScraperConfig class."""
    
    def test_default_config(self):
        """Test default configuration."""
        config = ScraperConfig()
        
        assert config.user_agent == "ResearchBot/1.0 (Educational Purpose)"
        assert config.timeout == 30
        assert config.verify_ssl is True
        assert config.respect_robots_txt is True
        
        # Check nested configs
        assert isinstance(config.rate_limit, RateLimitConfig)
        assert isinstance(config.auth, AuthConfig)
        assert isinstance(config.extraction, ExtractionConfig)
        assert isinstance(config.pagination, PaginationConfig)
        assert isinstance(config.browser, BrowserConfig)
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = ScraperConfig(
            user_agent="CustomBot/1.0",
            timeout=60,
            rate_limit=RateLimitConfig(requests_per_second=2.0),
            extraction=ExtractionConfig(method="targeted")
        )
        
        assert config.user_agent == "CustomBot/1.0"
        assert config.timeout == 60
        assert config.rate_limit.requests_per_second == 2.0
        assert config.extraction.method == "targeted"
    
    def test_yaml_serialization(self):
        """Test YAML serialization and deserialization."""
        config = ScraperConfig(
            user_agent="TestBot/1.0",
            rate_limit=RateLimitConfig(requests_per_second=3.0)
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config.to_yaml(Path(f.name))
            yaml_path = Path(f.name)
        
        try:
            # Load back from YAML
            loaded_config = ScraperConfig.from_yaml(yaml_path)
            
            assert loaded_config.user_agent == "TestBot/1.0"
            assert loaded_config.rate_limit.requests_per_second == 3.0
        finally:
            yaml_path.unlink()
    
    def test_json_serialization(self):
        """Test JSON serialization and deserialization."""
        config = ScraperConfig(
            user_agent="TestBot/1.0",
            extraction=ExtractionConfig(method="auto")
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config.to_json(Path(f.name))
            json_path = Path(f.name)
        
        try:
            # Load back from JSON
            loaded_config = ScraperConfig.from_json(json_path)
            
            assert loaded_config.user_agent == "TestBot/1.0"
            assert loaded_config.extraction.method == "auto"
        finally:
            json_path.unlink()
    
    def test_dict_conversion(self):
        """Test dictionary conversion."""
        config = ScraperConfig(user_agent="TestBot/1.0")
        config_dict = config.to_dict()
        
        assert isinstance(config_dict, dict)
        assert config_dict['user_agent'] == "TestBot/1.0"
        assert 'rate_limit' in config_dict
        assert isinstance(config_dict['rate_limit'], dict)
        
        # Test from_dict
        new_config = ScraperConfig.from_dict(config_dict)
        assert new_config.user_agent == "TestBot/1.0"


class TestPresets:
    """Test configuration presets."""
    
    def test_article_preset(self):
        """Test article preset."""
        config = get_preset("article")
        
        assert config.extraction.content_type == "article"
        assert config.extraction.extract_metadata is True
        assert ".advertisement" in config.extraction.remove_elements
    
    def test_documentation_preset(self):
        """Test documentation preset."""
        config = get_preset("documentation")
        
        assert config.extraction.content_type == "documentation"
        assert config.extraction.extract_links is True
        assert config.pagination.enabled is True
        assert config.pagination.max_pages == 50
    
    def test_blog_preset(self):
        """Test blog preset."""
        config = get_preset("blog")
        
        assert config.extraction.content_type == "blog"
        assert config.pagination.enabled is True
        assert config.pagination.method == "numbered"
    
    def test_spa_preset(self):
        """Test SPA preset."""
        config = get_preset("spa")
        
        assert config.browser.enabled is True
        assert config.browser.wait_for_load_state == "networkidle"
        assert config.browser.stealth_mode is True
    
    def test_invalid_preset(self):
        """Test invalid preset name."""
        with pytest.raises(ValueError, match="Unknown preset"):
            get_preset("invalid_preset")


class TestNestedConfigs:
    """Test nested configuration classes."""
    
    def test_rate_limit_config(self):
        """Test RateLimitConfig."""
        config = RateLimitConfig(
            requests_per_second=5.0,
            burst_size=10,
            max_retries=5
        )
        
        assert config.requests_per_second == 5.0
        assert config.burst_size == 10
        assert config.max_retries == 5
    
    def test_auth_config(self):
        """Test AuthConfig."""
        config = AuthConfig(
            auth_type="bearer",
            token="test_token",
            headers={"X-API-Key": "key"}
        )
        
        assert config.auth_type == "bearer"
        assert config.token == "test_token"
        assert config.headers["X-API-Key"] == "key"
    
    def test_extraction_config(self):
        """Test ExtractionConfig."""
        config = ExtractionConfig(
            method="targeted",
            selectors={"title": "h1"},
            extract_metadata=False
        )
        
        assert config.method == "targeted"
        assert config.selectors["title"] == "h1"
        assert config.extract_metadata is False
    
    def test_pagination_config(self):
        """Test PaginationConfig."""
        config = PaginationConfig(
            enabled=True,
            method="next_button",
            max_pages=20
        )
        
        assert config.enabled is True
        assert config.method == "next_button"
        assert config.max_pages == 20
    
    def test_browser_config(self):
        """Test BrowserConfig."""
        config = BrowserConfig(
            enabled=True,
            browser_type="firefox",
            headless=False
        )
        
        assert config.enabled is True
        assert config.browser_type == "firefox"
        assert config.headless is False
