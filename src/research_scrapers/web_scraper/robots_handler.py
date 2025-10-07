"""Robots.txt parser and compliance checker."""

import time
import urllib.parse
import urllib.robotparser
from typing import Optional, Dict
from loguru import logger
import requests


class RobotsHandler:
    """Handle robots.txt parsing and compliance checking."""
    
    def __init__(
        self,
        user_agent: str = "ResearchBot/1.0",
        cache_time: int = 3600,
        respect_robots: bool = True,
    ):
        """
        Initialize robots.txt handler.
        
        Args:
            user_agent: User agent string to check rules for
            cache_time: Time to cache robots.txt in seconds
            respect_robots: Whether to respect robots.txt
        """
        self.user_agent = user_agent
        self.cache_time = cache_time
        self.respect_robots = respect_robots
        
        # Cache for robots.txt parsers
        self._cache: Dict[str, tuple] = {}  # domain -> (parser, timestamp)
        
        logger.info(
            f"Initialized RobotsHandler: user_agent={user_agent}, "
            f"respect={respect_robots}, cache_time={cache_time}s"
        )
    
    def _get_domain(self, url: str) -> str:
        """Extract domain from URL."""
        parsed = urllib.parse.urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"
    
    def _get_robots_url(self, url: str) -> str:
        """Get robots.txt URL for a given URL."""
        domain = self._get_domain(url)
        return f"{domain}/robots.txt"
    
    def _get_parser(self, url: str) -> Optional[urllib.robotparser.RobotFileParser]:
        """Get cached or fetch robots.txt parser."""
        domain = self._get_domain(url)
        
        # Check cache
        if domain in self._cache:
            parser, timestamp = self._cache[domain]
            if time.time() - timestamp < self.cache_time:
                return parser
        
        # Fetch and parse robots.txt
        robots_url = self._get_robots_url(url)
        parser = urllib.robotparser.RobotFileParser()
        
        try:
            logger.debug(f"Fetching robots.txt from {robots_url}")
            response = requests.get(robots_url, timeout=10)
            
            if response.status_code == 200:
                # Parse robots.txt content
                parser.parse(response.text.splitlines())
                logger.debug(f"Successfully parsed robots.txt for {domain}")
            else:
                logger.debug(
                    f"No robots.txt found for {domain} "
                    f"(status: {response.status_code})"
                )
                # Empty parser allows all
                parser.parse([])
        
        except Exception as e:
            logger.warning(f"Error fetching robots.txt for {domain}: {e}")
            # On error, create permissive parser
            parser.parse([])
        
        # Cache parser
        self._cache[domain] = (parser, time.time())
        return parser
    
    def can_fetch(self, url: str) -> bool:
        """Check if URL can be fetched according to robots.txt."""
        if not self.respect_robots:
            return True
        
        try:
            parser = self._get_parser(url)
            if parser is None:
                return True
            
            allowed = parser.can_fetch(self.user_agent, url)
            
            if not allowed:
                logger.warning(f"URL blocked by robots.txt: {url}")
            
            return allowed
        
        except Exception as e:
            logger.error(f"Error checking robots.txt for {url}: {e}")
            # On error, allow by default
            return True
    
    def get_crawl_delay(self, url: str) -> Optional[float]:
        """Get crawl delay for URL from robots.txt."""
        if not self.respect_robots:
            return None
        
        try:
            parser = self._get_parser(url)
            if parser is None:
                return None
            
            # Get crawl delay
            delay = parser.crawl_delay(self.user_agent)
            
            if delay:
                logger.debug(f"Crawl delay for {url}: {delay}s")
            
            return delay
        
        except Exception as e:
            logger.error(f"Error getting crawl delay for {url}: {e}")
            return None
    
    def get_request_rate(self, url: str) -> Optional[tuple]:
        """Get request rate from robots.txt."""
        if not self.respect_robots:
            return None
        
        try:
            parser = self._get_parser(url)
            if parser is None:
                return None
            
            # Get request rate (requests, seconds)
            rate = parser.request_rate(self.user_agent)
            
            if rate:
                logger.debug(f"Request rate for {url}: {rate.requests}/{rate.seconds}s")
                return (rate.requests, rate.seconds)
            
            return None
        
        except Exception as e:
            logger.error(f"Error getting request rate for {url}: {e}")
            return None
    
    def clear_cache(self, domain: Optional[str] = None) -> None:
        """Clear robots.txt cache."""
        if domain:
            if domain in self._cache:
                del self._cache[domain]
                logger.debug(f"Cleared robots.txt cache for {domain}")
        else:
            self._cache.clear()
            logger.debug("Cleared all robots.txt cache")
    
    def get_stats(self) -> dict:
        """Get cache statistics."""
        return {
            "cached_domains": len(self._cache),
            "respect_robots": self.respect_robots,
            "user_agent": self.user_agent,
            "cache_time": self.cache_time,
        }
