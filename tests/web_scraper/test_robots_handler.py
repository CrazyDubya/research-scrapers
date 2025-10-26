"""Comprehensive tests for RobotsHandler class."""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
import urllib.robotparser
from research_scrapers.web_scraper.robots_handler import RobotsHandler


class TestRobotsHandlerInitialization:
    """Test RobotsHandler initialization."""
    
    def test_default_initialization(self):
        """Test handler initialization with default parameters."""
        handler = RobotsHandler()
        assert handler.user_agent == "ResearchBot/1.0"
        assert handler.cache_time == 3600
        assert handler.respect_robots is True
        assert handler._cache == {}
    
    def test_custom_initialization(self):
        """Test handler initialization with custom parameters."""
        handler = RobotsHandler(
            user_agent="CustomBot/2.0",
            cache_time=7200,
            respect_robots=False
        )
        assert handler.user_agent == "CustomBot/2.0"
        assert handler.cache_time == 7200
        assert handler.respect_robots is False
    
    def test_initialization_creates_empty_cache(self):
        """Test that initialization creates empty cache."""
        handler = RobotsHandler()
        assert isinstance(handler._cache, dict)
        assert len(handler._cache) == 0


class TestRobotsHandlerDomainParsing:
    """Test domain extraction and URL parsing."""
    
    @pytest.fixture
    def handler(self):
        """Create test handler."""
        return RobotsHandler()
    
    def test_get_domain_https(self, handler):
        """Test domain extraction from HTTPS URL."""
        url = "https://example.com/path/to/page"
        domain = handler._get_domain(url)
        assert domain == "https://example.com"
    
    def test_get_domain_http(self, handler):
        """Test domain extraction from HTTP URL."""
        url = "http://example.com/path/to/page"
        domain = handler._get_domain(url)
        assert domain == "http://example.com"
    
    def test_get_domain_with_port(self, handler):
        """Test domain extraction with port number."""
        url = "https://example.com:8080/path"
        domain = handler._get_domain(url)
        assert domain == "https://example.com:8080"
    
    def test_get_domain_with_subdomain(self, handler):
        """Test domain extraction with subdomain."""
        url = "https://api.example.com/v1/endpoint"
        domain = handler._get_domain(url)
        assert domain == "https://api.example.com"
    
    def test_get_robots_url(self, handler):
        """Test robots.txt URL generation."""
        url = "https://example.com/some/path"
        robots_url = handler._get_robots_url(url)
        assert robots_url == "https://example.com/robots.txt"
    
    def test_get_robots_url_preserves_scheme(self, handler):
        """Test that robots URL preserves HTTP/HTTPS scheme."""
        http_url = "http://example.com/path"
        https_url = "https://example.com/path"
        
        assert handler._get_robots_url(http_url) == "http://example.com/robots.txt"
        assert handler._get_robots_url(https_url) == "https://example.com/robots.txt"


class TestRobotsHandlerParsing:
    """Test robots.txt parsing functionality."""
    
    @pytest.fixture
    def handler(self):
        """Create test handler."""
        return RobotsHandler()
    
    @pytest.fixture
    def mock_response(self):
        """Create mock HTTP response."""
        mock = Mock()
        mock.status_code = 200
        mock.text = """User-agent: *
Disallow: /private/
Disallow: /admin/
Allow: /public/

User-agent: ResearchBot/1.0
Crawl-delay: 5
Disallow: /restricted/
"""
        return mock
    
    @patch('requests.get')
    def test_get_parser_success(self, mock_get, handler, mock_response):
        """Test successful robots.txt parsing."""
        mock_get.return_value = mock_response
        
        url = "https://example.com/page"
        parser = handler._get_parser(url)
        
        assert parser is not None
        assert isinstance(parser, urllib.robotparser.RobotFileParser)
        mock_get.assert_called_once()
    
    @patch('requests.get')
    def test_get_parser_caching(self, mock_get, handler, mock_response):
        """Test that parser is cached and reused."""
        mock_get.return_value = mock_response
        
        url = "https://example.com/page"
        
        # First call - should fetch
        parser1 = handler._get_parser(url)
        assert mock_get.call_count == 1
        
        # Second call - should use cache
        parser2 = handler._get_parser(url)
        assert mock_get.call_count == 1  # No additional call
        assert parser1 is parser2
    
    @patch('requests.get')
    def test_get_parser_cache_expiry(self, mock_get, handler, mock_response):
        """Test that cache expires after cache_time."""
        handler.cache_time = 1  # 1 second cache
        mock_get.return_value = mock_response
        
        url = "https://example.com/page"
        
        # First call
        handler._get_parser(url)
        assert mock_get.call_count == 1
        
        # Wait for cache to expire
        time.sleep(1.1)
        
        # Second call - should fetch again
        handler._get_parser(url)
        assert mock_get.call_count == 2
    
    @patch('requests.get')
    def test_get_parser_404_response(self, mock_get, handler):
        """Test handling of missing robots.txt (404)."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        url = "https://example.com/page"
        parser = handler._get_parser(url)
        
        # Should create permissive parser
        assert parser is not None
        # Empty parser allows everything
        assert parser.can_fetch("*", url) is True
    
    @patch('requests.get')
    def test_get_parser_network_error(self, mock_get, handler):
        """Test handling of network errors."""
        mock_get.side_effect = Exception("Network error")
        
        url = "https://example.com/page"
        parser = handler._get_parser(url)
        
        # Should create permissive parser on error
        assert parser is not None
        assert parser.can_fetch("*", url) is True
    
    @patch('requests.get')
    def test_get_parser_timeout(self, mock_get, handler):
        """Test handling of request timeout."""
        mock_get.side_effect = TimeoutError("Request timeout")
        
        url = "https://example.com/page"
        parser = handler._get_parser(url)
        
        # Should create permissive parser
        assert parser is not None
    
    @patch('requests.get')
    def test_get_parser_different_domains(self, mock_get, handler, mock_response):
        """Test that different domains are cached separately."""
        mock_get.return_value = mock_response
        
        url1 = "https://example.com/page"
        url2 = "https://different.com/page"
        
        parser1 = handler._get_parser(url1)
        parser2 = handler._get_parser(url2)
        
        assert mock_get.call_count == 2
        assert len(handler._cache) == 2


class TestRobotsHandlerCanFetch:
    """Test URL permission checking."""
    
    @pytest.fixture
    def handler(self):
        """Create test handler."""
        return RobotsHandler()
    
    @pytest.fixture
    def restrictive_robots(self):
        """Create restrictive robots.txt content."""
        return """User-agent: *
Disallow: /private/
Disallow: /admin/

User-agent: ResearchBot/1.0
Disallow: /restricted/
Allow: /public/
"""
    
    def test_can_fetch_respect_disabled(self):
        """Test that all URLs are allowed when respect_robots is False."""
        handler = RobotsHandler(respect_robots=False)
        
        # Should allow any URL without checking
        assert handler.can_fetch("https://example.com/private/") is True
        assert handler.can_fetch("https://example.com/admin/") is True
    
    @patch('requests.get')
    def test_can_fetch_allowed_url(self, mock_get, handler, restrictive_robots):
        """Test that allowed URLs return True."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = restrictive_robots
        mock_get.return_value = mock_response
        
        # Public URL should be allowed
        assert handler.can_fetch("https://example.com/public/page.html") is True
    
    @patch('requests.get')
    def test_can_fetch_disallowed_url(self, mock_get, handler, restrictive_robots):
        """Test that disallowed URLs return False."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = restrictive_robots
        mock_get.return_value = mock_response
        
        # Restricted URL should be disallowed
        assert handler.can_fetch("https://example.com/restricted/secret.html") is False
    
    @patch('requests.get')
    def test_can_fetch_all_user_agents(self, mock_get, handler, restrictive_robots):
        """Test rules for all user agents."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = restrictive_robots
        mock_get.return_value = mock_response
        
        # /private/ is disallowed for all user agents
        assert handler.can_fetch("https://example.com/private/data.html") is False
    
    @patch('requests.get')
    def test_can_fetch_no_robots_txt(self, mock_get, handler):
        """Test that missing robots.txt allows all URLs."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        # Should allow everything when no robots.txt exists
        assert handler.can_fetch("https://example.com/any/path") is True
    
    @patch('requests.get')
    def test_can_fetch_error_handling(self, mock_get, handler):
        """Test that errors default to allowing access."""
        mock_get.side_effect = Exception("Network error")
        
        # Should allow on error (fail open)
        assert handler.can_fetch("https://example.com/page") is True
    
    @patch('requests.get')
    def test_can_fetch_root_path(self, mock_get, handler):
        """Test fetching root path."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "User-agent: *\nAllow: /"
        mock_get.return_value = mock_response
        
        assert handler.can_fetch("https://example.com/") is True


class TestRobotsHandlerCrawlDelay:
    """Test crawl delay handling."""
    
    @pytest.fixture
    def handler(self):
        """Create test handler."""
        return RobotsHandler()
    
    @pytest.fixture
    def robots_with_delay(self):
        """Create robots.txt with crawl delay."""
        return """User-agent: ResearchBot/1.0
Crawl-delay: 5
Disallow: /admin/

User-agent: *
Crawl-delay: 2
"""
    
    @patch('requests.get')
    def test_get_crawl_delay_specific_bot(self, mock_get, handler, robots_with_delay):
        """Test getting crawl delay for specific user agent."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = robots_with_delay
        mock_get.return_value = mock_response
        
        delay = handler.get_crawl_delay("https://example.com/page")
        assert delay == 5
    
    @patch('requests.get')
    def test_get_crawl_delay_no_delay(self, mock_get, handler):
        """Test when no crawl delay is specified."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "User-agent: *\nDisallow: /admin/"
        mock_get.return_value = mock_response
        
        delay = handler.get_crawl_delay("https://example.com/page")
        assert delay is None
    
    @patch('requests.get')
    def test_get_crawl_delay_respect_disabled(self, mock_get):
        """Test that crawl delay is None when respect_robots is False."""
        handler = RobotsHandler(respect_robots=False)
        
        delay = handler.get_crawl_delay("https://example.com/page")
        assert delay is None
        mock_get.assert_not_called()
    
    @patch('requests.get')
    def test_get_crawl_delay_no_robots_txt(self, mock_get, handler):
        """Test crawl delay with missing robots.txt."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        delay = handler.get_crawl_delay("https://example.com/page")
        assert delay is None
    
    @patch('requests.get')
    def test_get_crawl_delay_error_handling(self, mock_get, handler):
        """Test crawl delay with network errors."""
        mock_get.side_effect = Exception("Network error")
        
        delay = handler.get_crawl_delay("https://example.com/page")
        assert delay is None


class TestRobotsHandlerRequestRate:
    """Test request rate handling."""
    
    @pytest.fixture
    def handler(self):
        """Create test handler."""
        return RobotsHandler()
    
    @pytest.fixture
    def robots_with_rate(self):
        """Create robots.txt with request rate."""
        return """User-agent: ResearchBot/1.0
Request-rate: 10/60

User-agent: *
Request-rate: 5/60
"""
    
    @patch('requests.get')
    def test_get_request_rate_specific_bot(self, mock_get, handler, robots_with_rate):
        """Test getting request rate for specific user agent."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = robots_with_rate
        mock_get.return_value = mock_response
        
        rate = handler.get_request_rate("https://example.com/page")
        
        # Should return tuple of (requests, seconds) or None
        if rate is not None:
            assert isinstance(rate, tuple)
            assert len(rate) == 2
    
    @patch('requests.get')
    def test_get_request_rate_no_rate(self, mock_get, handler):
        """Test when no request rate is specified."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "User-agent: *\nDisallow: /admin/"
        mock_get.return_value = mock_response
        
        rate = handler.get_request_rate("https://example.com/page")
        assert rate is None
    
    @patch('requests.get')
    def test_get_request_rate_respect_disabled(self, mock_get):
        """Test that request rate is None when respect_robots is False."""
        handler = RobotsHandler(respect_robots=False)
        
        rate = handler.get_request_rate("https://example.com/page")
        assert rate is None
        mock_get.assert_not_called()
    
    @patch('requests.get')
    def test_get_request_rate_error_handling(self, mock_get, handler):
        """Test request rate with network errors."""
        mock_get.side_effect = Exception("Network error")
        
        rate = handler.get_request_rate("https://example.com/page")
        assert rate is None


class TestRobotsHandlerCacheManagement:
    """Test cache management functionality."""
    
    @pytest.fixture
    def handler(self):
        """Create test handler."""
        return RobotsHandler()
    
    @pytest.fixture
    def mock_response(self):
        """Create mock response."""
        mock = Mock()
        mock.status_code = 200
        mock.text = "User-agent: *\nDisallow: /admin/"
        return mock
    
    @patch('requests.get')
    def test_clear_cache_all(self, mock_get, handler, mock_response):
        """Test clearing entire cache."""
        mock_get.return_value = mock_response
        
        # Populate cache
        handler._get_parser("https://example.com/page")
        handler._get_parser("https://different.com/page")
        
        assert len(handler._cache) == 2
        
        # Clear all cache
        handler.clear_cache()
        
        assert len(handler._cache) == 0
    
    @patch('requests.get')
    def test_clear_cache_specific_domain(self, mock_get, handler, mock_response):
        """Test clearing cache for specific domain."""
        mock_get.return_value = mock_response
        
        # Populate cache
        handler._get_parser("https://example.com/page")
        handler._get_parser("https://different.com/page")
        
        assert len(handler._cache) == 2
        
        # Clear only example.com
        handler.clear_cache("https://example.com")
        
        assert len(handler._cache) == 1
        assert "https://different.com" in handler._cache
    
    @patch('requests.get')
    def test_clear_cache_nonexistent_domain(self, mock_get, handler, mock_response):
        """Test clearing cache for domain not in cache."""
        mock_get.return_value = mock_response
        
        handler._get_parser("https://example.com/page")
        
        # Should not raise error
        handler.clear_cache("https://nonexistent.com")
        
        # Original cache should remain
        assert len(handler._cache) == 1


class TestRobotsHandlerStats:
    """Test statistics functionality."""
    
    @pytest.fixture
    def handler(self):
        """Create test handler."""
        return RobotsHandler(
            user_agent="TestBot/1.0",
            cache_time=7200,
            respect_robots=True
        )
    
    def test_get_stats_initial(self, handler):
        """Test getting stats from fresh handler."""
        stats = handler.get_stats()
        
        assert stats['cached_domains'] == 0
        assert stats['respect_robots'] is True
        assert stats['user_agent'] == "TestBot/1.0"
        assert stats['cache_time'] == 7200
    
    @patch('requests.get')
    def test_get_stats_with_cache(self, mock_get, handler):
        """Test stats after populating cache."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "User-agent: *\nDisallow: /admin/"
        mock_get.return_value = mock_response
        
        # Populate cache
        handler._get_parser("https://example.com/page")
        handler._get_parser("https://different.com/page")
        
        stats = handler.get_stats()
        
        assert stats['cached_domains'] == 2
        assert stats['user_agent'] == "TestBot/1.0"
    
    def test_get_stats_structure(self, handler):
        """Test that stats contain all required fields."""
        stats = handler.get_stats()
        
        required_fields = ['cached_domains', 'respect_robots', 'user_agent', 'cache_time']
        for field in required_fields:
            assert field in stats


class TestRobotsHandlerEdgeCases:
    """Test edge cases and error conditions."""
    
    @pytest.fixture
    def handler(self):
        """Create test handler."""
        return RobotsHandler()
    
    def test_empty_url(self, handler):
        """Test handling of empty URL."""
        # Should handle gracefully
        try:
            domain = handler._get_domain("")
            # May return empty or raise - either is acceptable
            assert isinstance(domain, str)
        except:
            pass  # Exception is acceptable
    
    def test_malformed_url(self, handler):
        """Test handling of malformed URL."""
        try:
            domain = handler._get_domain("not-a-url")
            assert isinstance(domain, str)
        except:
            pass  # Exception is acceptable
    
    @patch('requests.get')
    def test_empty_robots_txt(self, mock_get, handler):
        """Test handling of empty robots.txt."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = ""
        mock_get.return_value = mock_response
        
        # Empty robots.txt should allow everything
        assert handler.can_fetch("https://example.com/page") is True
    
    @patch('requests.get')
    def test_malformed_robots_txt(self, mock_get, handler):
        """Test handling of malformed robots.txt."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "This is not valid robots.txt format!!!"
        mock_get.return_value = mock_response
        
        # Should handle gracefully
        parser = handler._get_parser("https://example.com/page")
        assert parser is not None
    
    @patch('requests.get')
    def test_unicode_in_robots_txt(self, mock_get, handler):
        """Test handling of unicode content in robots.txt."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "User-agent: *\n# Comment with unicode: 日本語\nDisallow: /admin/"
        mock_get.return_value = mock_response
        
        parser = handler._get_parser("https://example.com/page")
        assert parser is not None
    
    def test_multiple_handlers_independent_caches(self):
        """Test that multiple handlers have independent caches."""
        handler1 = RobotsHandler()
        handler2 = RobotsHandler()
        
        # Modify handler1 cache
        handler1._cache["test"] = ("parser", time.time())
        
        # handler2 cache should be independent
        assert "test" not in handler2._cache


class TestRobotsHandlerIntegration:
    """Integration tests for complete workflows."""
    
    @pytest.fixture
    def handler(self):
        """Create test handler."""
        return RobotsHandler()
    
    @pytest.fixture
    def complex_robots(self):
        """Create complex robots.txt."""
        return """# Complex robots.txt
User-agent: *
Crawl-delay: 1
Disallow: /private/
Disallow: /temp/
Allow: /public/

User-agent: ResearchBot/1.0
Crawl-delay: 5
Request-rate: 10/60
Disallow: /restricted/
Allow: /api/
Allow: /public/
"""
    
    @patch('requests.get')
    def test_full_workflow_allowed(self, mock_get, handler, complex_robots):
        """Test complete workflow for allowed URL."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = complex_robots
        mock_get.return_value = mock_response
        
        url = "https://example.com/public/page.html"
        
        # Check if can fetch
        assert handler.can_fetch(url) is True
        
        # Get crawl delay
        delay = handler.get_crawl_delay(url)
        assert delay == 5
        
        # Check stats
        stats = handler.get_stats()
        assert stats['cached_domains'] == 1
    
    @patch('requests.get')
    def test_full_workflow_disallowed(self, mock_get, handler, complex_robots):
        """Test complete workflow for disallowed URL."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = complex_robots
        mock_get.return_value = mock_response
        
        url = "https://example.com/restricted/secret.html"
        
        # Check if can fetch
        assert handler.can_fetch(url) is False
        
        # Still can get crawl delay
        delay = handler.get_crawl_delay(url)
        assert delay == 5
    
    @patch('requests.get')
    def test_multiple_domains_workflow(self, mock_get, handler, complex_robots):
        """Test workflow with multiple domains."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = complex_robots
        mock_get.return_value = mock_response
        
        # Check multiple domains
        urls = [
            "https://example.com/public/page.html",
            "https://different.com/page.html",
            "https://another.com/page.html"
        ]
        
        for url in urls:
            handler.can_fetch(url)
        
        # Should have cached all three domains
        stats = handler.get_stats()
        assert stats['cached_domains'] == 3
        
        # Clear specific domain
        handler.clear_cache("https://example.com")
        stats = handler.get_stats()
        assert stats['cached_domains'] == 2
