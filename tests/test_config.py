"""Tests for config module."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from research_scrapers.config import Config


class TestConfig:
    """Test cases for Config class."""
    
    def test_default_initialization(self):
        """Test config initialization with defaults."""
        config = Config()
        
        # Test some default values
        assert config.REQUEST_TIMEOUT == 30
        assert config.MAX_RETRIES == 3
        assert config.RATE_LIMIT == 1.0
        assert config.LOG_LEVEL == 'INFO'
        assert config.SELENIUM_BROWSER == 'chrome'
        assert config.SELENIUM_HEADLESS is True
    
    def test_environment_variable_loading(self):
        """Test loading configuration from environment variables."""
        env_vars = {
            'SCRAPER_REQUEST_TIMEOUT': '60',
            'SCRAPER_MAX_RETRIES': '5',
            'SCRAPER_RATE_LIMIT': '2.5',
            'SCRAPER_USER_AGENT': 'Custom User Agent',
            'SCRAPER_LOG_LEVEL': 'DEBUG',
            'GITHUB_API_KEY': 'test_github_key',
            'TWITTER_API_KEY': 'test_twitter_key'
        }
        
        with patch.dict(os.environ, env_vars):
            config = Config()
            
            assert config.REQUEST_TIMEOUT == 60
            assert config.MAX_RETRIES == 5
            assert config.RATE_LIMIT == 2.5
            assert config.USER_AGENT == 'Custom User Agent'
            assert config.LOG_LEVEL == 'DEBUG'
            assert config.get_api_key('github') == 'test_github_key'
            assert config.get_api_key('twitter') == 'test_twitter_key'
    
    def test_json_config_file_loading(self):
        """Test loading configuration from JSON file."""
        config_data = {
            'request_timeout': 45,
            'max_retries': 4,
            'rate_limit': 1.5,
            'log_level': 'WARNING',
            'api_keys': {
                'github': 'json_github_key',
                'reddit': 'json_reddit_key'
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_path = f.name
        
        try:
            config = Config(config_file=temp_path)
            
            assert config.REQUEST_TIMEOUT == 45
            assert config.MAX_RETRIES == 4
            assert config.RATE_LIMIT == 1.5
            assert config.LOG_LEVEL == 'WARNING'
            assert config.API_KEYS['github'] == 'json_github_key'
            assert config.API_KEYS['reddit'] == 'json_reddit_key'
        
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_nonexistent_config_file(self):
        """Test error handling for nonexistent config file."""
        with pytest.raises(FileNotFoundError):
            Config(config_file='/nonexistent/path/config.json')
    
    def test_unsupported_config_file_format(self):
        """Test error handling for unsupported config file format."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            f.write('[section]\nkey=value\n')
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError, match="Unsupported configuration file format"):
                Config(config_file=temp_path)
        
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_api_key_methods(self):
        """Test API key getter and setter methods."""
        config = Config()
        
        # Test setting and getting API keys
        config.set_api_key('github', 'test_key_123')
        assert config.get_api_key('github') == 'test_key_123'
        assert config.get_api_key('GITHUB') == 'test_key_123'  # Case insensitive
        
        # Test getting nonexistent API key
        assert config.get_api_key('nonexistent') is None
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        config = Config()
        config_dict = config.to_dict()
        
        # Should contain all public attributes
        assert 'REQUEST_TIMEOUT' in config_dict
        assert 'MAX_RETRIES' in config_dict
        assert 'USER_AGENT' in config_dict
        
        # Should not contain private methods
        assert '_load_defaults' not in config_dict
        assert '_load_from_env' not in config_dict
    
    def test_repr(self):
        """Test string representation."""
        config = Config()
        repr_str = repr(config)
        
        assert repr_str.startswith('Config(')
        assert 'REQUEST_TIMEOUT' in repr_str
    
    @patch.dict(os.environ, {'SCRAPER_PROXY': 'http://proxy.example.com:8080'})
    def test_proxy_configuration(self):
        """Test proxy configuration from environment."""
        config = Config()
        assert config.PROXY == 'http://proxy.example.com:8080'
    
    def test_output_directory_configuration(self):
        """Test output directory configuration."""
        config = Config()
        assert isinstance(config.OUTPUT_DIR, Path)
        assert str(config.OUTPUT_DIR) == 'output'
        
        # Test with environment variable
        with patch.dict(os.environ, {'SCRAPER_OUTPUT_DIR': '/custom/output'}):
            config = Config()
            assert str(config.OUTPUT_DIR) == '/custom/output'
