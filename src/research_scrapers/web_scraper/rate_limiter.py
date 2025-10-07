"""Rate limiting and throttling for web scraping."""

import time
import asyncio
from typing import Optional
from collections import deque
from loguru import logger
import urllib.parse


class RateLimiter:
    """Token bucket rate limiter for controlling request rates."""
    
    def __init__(
        self,
        requests_per_second: float = 1.0,
        burst_size: int = 5,
        backoff_factor: float = 2.0,
        max_retries: int = 3,
    ):
        """
        Initialize rate limiter.
        
        Args:
            requests_per_second: Maximum requests per second
            burst_size: Maximum burst size (tokens in bucket)
            backoff_factor: Exponential backoff multiplier
            max_retries: Maximum retry attempts
        """
        self.requests_per_second = requests_per_second
        self.burst_size = burst_size
        self.backoff_factor = backoff_factor
        self.max_retries = max_retries
        
        # Token bucket implementation
        self.tokens = burst_size
        self.last_update = time.time()
        self.rate = requests_per_second
        
        # Track request history per domain
        self.request_history: dict = {}
        
        logger.info(
            f"Initialized RateLimiter: {requests_per_second} req/s, "
            f"burst: {burst_size}, backoff: {backoff_factor}x"
        )
    
    def _get_domain(self, url: str) -> str:
        """Extract domain from URL."""
        parsed = urllib.parse.urlparse(url)
        return parsed.netloc
    
    def _update_tokens(self) -> None:
        """Update available tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_update
        
        # Add tokens based on elapsed time
        self.tokens = min(
            self.burst_size,
            self.tokens + elapsed * self.rate
        )
        self.last_update = now
    
    def wait_if_needed(self, url: str) -> None:
        """Wait if rate limit is reached (synchronous)."""
        domain = self._get_domain(url)
        
        # Update token bucket
        self._update_tokens()
        
        # If no tokens available, wait
        if self.tokens < 1:
            wait_time = (1 - self.tokens) / self.rate
            logger.debug(f"Rate limit reached for {domain}, waiting {wait_time:.2f}s")
            time.sleep(wait_time)
            self._update_tokens()
        
        # Consume a token
        self.tokens -= 1
        
        # Track request
        if domain not in self.request_history:
            self.request_history[domain] = deque(maxlen=100)
        self.request_history[domain].append(time.time())
    
    async def async_wait_if_needed(self, url: str) -> None:
        """Wait if rate limit is reached (asynchronous)."""
        domain = self._get_domain(url)
        
        # Update token bucket
        self._update_tokens()
        
        # If no tokens available, wait
        if self.tokens < 1:
            wait_time = (1 - self.tokens) / self.rate
            logger.debug(f"Rate limit reached for {domain}, waiting {wait_time:.2f}s")
            await asyncio.sleep(wait_time)
            self._update_tokens()
        
        # Consume a token
        self.tokens -= 1
        
        # Track request
        if domain not in self.request_history:
            self.request_history[domain] = deque(maxlen=100)
        self.request_history[domain].append(time.time())
    
    def handle_retry_after(self, retry_after: Optional[str]) -> float:
        """Handle Retry-After header."""
        if not retry_after:
            return 0.0
        
        try:
            # Try parsing as seconds
            return float(retry_after)
        except ValueError:
            # Try parsing as HTTP date
            from email.utils import parsedate_to_datetime
            try:
                retry_date = parsedate_to_datetime(retry_after)
                return (retry_date.timestamp() - time.time())
            except Exception:
                logger.warning(f"Could not parse Retry-After: {retry_after}")
                return 0.0
    
    def calculate_backoff(self, attempt: int) -> float:
        """Calculate exponential backoff delay."""
        return min(
            300,  # Max 5 minutes
            (self.backoff_factor ** attempt)
        )
    
    def get_stats(self, domain: Optional[str] = None) -> dict:
        """Get rate limiting statistics."""
        if domain:
            if domain not in self.request_history:
                return {"domain": domain, "requests": 0, "window": 0}
            
            history = self.request_history[domain]
            if not history:
                return {"domain": domain, "requests": 0, "window": 0}
            
            now = time.time()
            window = now - history[0]
            return {
                "domain": domain,
                "requests": len(history),
                "window": window,
                "rate": len(history) / window if window > 0 else 0,
            }
        else:
            # Overall stats
            total_requests = sum(len(h) for h in self.request_history.values())
            return {
                "total_requests": total_requests,
                "domains": len(self.request_history),
                "current_tokens": self.tokens,
                "max_tokens": self.burst_size,
                "rate": self.rate,
            }
