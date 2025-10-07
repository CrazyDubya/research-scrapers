"""Tests for web scraper."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from research_scrapers.web_scraper import WebScraper, ScraperConfig
from research_scrapers.web_scraper.config import ExtractionConfig, RateLimitConfig


class TestWebScraper:
    """Test WebScraper class."""
    
    @pytest.fixture
    def scraper_config(self):
        """Create test configuration."""
        return ScraperConfig(
            rate_limit=RateLimitConfig(
                requests_per_second=10.0,  # Fast for tests
                max_retries=1
            ),
            extraction=ExtractionConfig(
                method="auto",
                extract_metadata=True
            )
        )
    
    @pytest.fixture
    def scraper(self, scraper_config):
        """Create test scraper."""
        return WebScraper(scraper_config)
    
    @pytest.mark.asyncio
    async def test_scraper_initialization(self, scraper):
        """Test scraper initialization."""
        assert scraper.config is not None
        assert scraper.rate_limiter is not None
        assert scraper.robots_handler is not None
        assert scraper.auth_manager is not None
        assert scraper.content_extractor is not None
        assert scraper.pagination_handler is not None
    
    @pytest.mark.asyncio
    async def test_scrape_url_success(self, scraper):
        """Test successful URL scraping."""
        mock_html = "<html><head><title>Test</title></head><body><p>Content</p></body></html>"
        
        with patch('requests.Session.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = mock_html
            mock_response.headers = {}
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            result = await scraper.scrape_url("https://example.com")
            
            assert result['success'] is True
            assert result['url'] == "https://example.com"
            assert 'content' in result
            assert 'metadata' in result
    
    @pytest.mark.asyncio
    async def test_scrape_url_robots_blocked(self, scraper):
        """Test URL blocked by robots.txt."""
        with patch.object(scraper.robots_handler, 'can_fetch', return_value=False):
            result = await scraper.scrape_url("https://example.com")
            
            assert result['success'] is False
            assert 'Blocked by robots.txt' in result['error']
    
    @pytest.mark.asyncio
    async def test_scrape_multiple_urls(self, scraper):
        """Test scraping multiple URLs."""
        mock_html = "<html><body><p>Content</p></body></html>"
        
        with patch('requests.Session.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = mock_html
            mock_response.headers = {}
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            urls = ["https://example1.com", "https://example2.com"]
            results = await scraper.scrape_multiple(urls)
            
            assert len(results) == 2
            assert all(result['success'] for result in results)
    
    @pytest.mark.asyncio
    async def test_get_stats(self, scraper):
        """Test getting scraper statistics."""
        stats = scraper.get_stats()
        
        assert 'rate_limiter' in stats
        assert 'robots_handler' in stats
        assert 'pagination_handler' in stats
        assert 'auth_authenticated' in stats
    
    @pytest.mark.asyncio
    async def test_close(self, scraper):
        """Test scraper cleanup."""
        await scraper.close()
        # Should not raise any exceptions
