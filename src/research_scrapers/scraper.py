"""Base scraper classes and web scraping functionality."""

import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions

from .config import Config
from .utils import rate_limit, retry_on_failure, clean_text


class BaseScraper(ABC):
    """Abstract base class for all scrapers."""
    
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.session = requests.Session()
        self._setup_session()
    
    def _setup_session(self):
        """Configure the requests session with headers and settings."""
        self.session.headers.update({
            'User-Agent': self.config.USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
        if self.config.PROXY:
            self.session.proxies.update({
                'http': self.config.PROXY,
                'https': self.config.PROXY
            })
    
    @abstractmethod
    def scrape(self, *args, **kwargs) -> Any:
        """Main scraping method to be implemented by subclasses."""
        pass
    
    def close(self):
        """Clean up resources."""
        self.session.close()


class WebScraper(BaseScraper):
    """Web scraper using requests and BeautifulSoup."""
    
    @rate_limit
    @retry_on_failure
    def get_page(self, url: str, **kwargs) -> requests.Response:
        """Fetch a web page with rate limiting and retry logic."""
        self.logger.info(f"Fetching: {url}")
        response = self.session.get(url, timeout=self.config.REQUEST_TIMEOUT, **kwargs)
        response.raise_for_status()
        return response
    
    def parse_html(self, html: str, parser: str = 'html.parser') -> BeautifulSoup:
        """Parse HTML content using BeautifulSoup."""
        return BeautifulSoup(html, parser)
    
    def extract_links(self, soup: BeautifulSoup, base_url: str = None) -> List[str]:
        """Extract all links from a BeautifulSoup object."""
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if base_url:
                href = urljoin(base_url, href)
            links.append(href)
        return links
    
    def scrape(self, url: str, selector: Optional[str] = None) -> Dict[str, Any]:
        """Scrape a web page and return structured data."""
        response = self.get_page(url)
        soup = self.parse_html(response.text)
        
        data = {
            'url': url,
            'title': soup.title.string if soup.title else None,
            'content': clean_text(soup.get_text()) if not selector else None,
            'links': self.extract_links(soup, url),
            'scraped_at': time.time()
        }
        
        if selector:
            elements = soup.select(selector)
            data['selected_content'] = [clean_text(elem.get_text()) for elem in elements]
        
        return data


class SeleniumScraper(BaseScraper):
    """Web scraper using Selenium for JavaScript-heavy sites."""
    
    def __init__(self, config: Optional[Config] = None, browser: str = 'chrome', headless: bool = True):
        super().__init__(config)
        self.browser = browser
        self.headless = headless
        self.driver = None
        self._setup_driver()
    
    def _setup_driver(self):
        """Initialize the Selenium WebDriver."""
        if self.browser.lower() == 'chrome':
            options = ChromeOptions()
            if self.headless:
                options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument(f'--user-agent={self.config.USER_AGENT}')
            self.driver = webdriver.Chrome(options=options)
        elif self.browser.lower() == 'firefox':
            options = FirefoxOptions()
            if self.headless:
                options.add_argument('--headless')
            options.set_preference('general.useragent.override', self.config.USER_AGENT)
            self.driver = webdriver.Firefox(options=options)
        else:
            raise ValueError(f"Unsupported browser: {self.browser}")
        
        self.driver.set_page_load_timeout(self.config.REQUEST_TIMEOUT)
    
    @rate_limit
    def get_page(self, url: str, wait_for_element: Optional[str] = None, timeout: int = 10):
        """Navigate to a page and optionally wait for an element."""
        self.logger.info(f"Navigating to: {url}")
        self.driver.get(url)
        
        if wait_for_element:
            wait = WebDriverWait(self.driver, timeout)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, wait_for_element)))
    
    def scrape(self, url: str, selector: Optional[str] = None, wait_for_element: Optional[str] = None) -> Dict[str, Any]:
        """Scrape a web page using Selenium."""
        self.get_page(url, wait_for_element)
        
        data = {
            'url': url,
            'title': self.driver.title,
            'content': clean_text(self.driver.page_source) if not selector else None,
            'scraped_at': time.time()
        }
        
        if selector:
            elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
            data['selected_content'] = [clean_text(elem.text) for elem in elements]
        
        return data
    
    def close(self):
        """Clean up resources."""
        if self.driver:
            self.driver.quit()
        super().close()
