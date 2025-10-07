"""Tests for rate limiter."""

import pytest
import time
import asyncio
from research_scrapers.web_scraper.rate_limiter import RateLimiter


class TestRateLimiter:
    """Test RateLimiter class."""
    
    @pytest.fixture
    def rate_limiter(self):
        """Create test rate limiter."""
        return RateLimiter(
            requests_per_second=2.0,
            burst_size=3,
            max_retries=2
        )
    
    def test_initialization(self, rate_limiter):
        """Test rate limiter initialization."""
        assert rate_limiter.requests_per_second == 2.0
        assert rate_limiter.burst_size == 3
        assert rate_limiter.max_retries == 2
        assert rate_limiter.tokens == 3  # Should start with full bucket
    
    def test_wait_if_needed_sync(self, rate_limiter):
        """Test synchronous rate limiting."""
        url = "https://example.com"
        
        # First few requests should be fast (using burst)
        start_time = time.time()
        for _ in range(3):
            rate_limiter.wait_if_needed(url)
        elapsed = time.time() - start_time
        
        # Should be very fast (burst)
        assert elapsed < 0.1
        
        # Next request should be rate limited
        start_time = time.time()
        rate_limiter.wait_if_needed(url)
        elapsed = time.time() - start_time
        
        # Should wait for token refill
        assert elapsed >= 0.4  # At least 0.5s for 2 req/s rate
    
    @pytest.mark.asyncio
    async def test_wait_if_needed_async(self, rate_limiter):
        """Test asynchronous rate limiting."""
        url = "https://example.com"
        
        # Use up burst tokens
        for _ in range(3):
            await rate_limiter.async_wait_if_needed(url)
        
        # Next request should be rate limited
        start_time = time.time()
        await rate_limiter.async_wait_if_needed(url)
        elapsed = time.time() - start_time
        
        # Should wait for token refill
        assert elapsed >= 0.4
    
    def test_handle_retry_after(self, rate_limiter):
        """Test Retry-After header handling."""
        # Test seconds format
        delay = rate_limiter.handle_retry_after("5")
        assert delay == 5.0
        
        # Test invalid format
        delay = rate_limiter.handle_retry_after("invalid")
        assert delay == 0.0
        
        # Test None
        delay = rate_limiter.handle_retry_after(None)
        assert delay == 0.0
    
    def test_calculate_backoff(self, rate_limiter):
        """Test exponential backoff calculation."""
        assert rate_limiter.calculate_backoff(0) == 1.0  # 2^0
        assert rate_limiter.calculate_backoff(1) == 2.0  # 2^1
        assert rate_limiter.calculate_backoff(2) == 4.0  # 2^2
        
        # Should cap at 300 seconds
        large_delay = rate_limiter.calculate_backoff(10)
        assert large_delay <= 300
    
    def test_get_stats(self, rate_limiter):
        """Test statistics retrieval."""
        url = "https://example.com"
        
        # Make some requests
        rate_limiter.wait_if_needed(url)
        rate_limiter.wait_if_needed(url)
        
        # Get overall stats
        stats = rate_limiter.get_stats()
        assert 'total_requests' in stats
        assert 'domains' in stats
        assert 'current_tokens' in stats
        assert stats['total_requests'] == 2
        
        # Get domain-specific stats
        domain_stats = rate_limiter.get_stats("example.com")
        assert 'domain' in domain_stats
        assert 'requests' in domain_stats
        assert domain_stats['requests'] == 2
