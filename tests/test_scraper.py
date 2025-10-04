"""Tests for scraper module."""

import pytest
import requests_mock
from unittest.mock import Mock, patch

from research_scrapers.scraper import BaseScraper, WebScraper
from research_scrapers.config import Config


class TestBaseScraper:
    """Test cases for BaseScraper class."""
    
    def test_init_with_default_config(self):
        """Test initialization with default config."""
        
        class TestScraper(BaseScraper):
            def scrape(self):
                return "test"
        
        scraper = TestScraper()
        assert scraper.config is not None
        assert isinstance(scraper.config, Config)
    
    def test_init_with_custom_config(self):
        """Test initialization with custom config."""
        
        class TestScraper(BaseScraper):
            def scrape(self):
                return "test"
        
        config = Config()
        config.REQUEST_TIMEOUT = 60
        
        scraper = TestScraper(config)
        assert scraper.config.REQUEST_TIMEOUT == 60
    
    def test_session_setup(self):
        """Test that session is properly configured."""
        
        class TestScraper(BaseScraper):
            def scrape(self):
                return "test"
        
        scraper = TestScraper()
        assert 'User-Agent' in scraper.session.headers
        assert scraper.session.headers['User-Agent'] == scraper.config.USER_AGENT


class TestWebScraper:
    """Test cases for WebScraper class."""
    
    def test_init(self):
        """Test WebScraper initialization."""
        scraper = WebScraper()
        assert scraper.config is not None
        assert scraper.session is not None
    
    @requests_mock.Mocker()
    def test_get_page_success(self, m):
        """Test successful page retrieval."""
        test_url = "https://example.com"
        test_content = "<html><body>Test content</body></html>"
        
        m.get(test_url, text=test_content)
        
        scraper = WebScraper()
        response = scraper.get_page(test_url)
        
        assert response.status_code == 200
        assert response.text == test_content
    
    @requests_mock.Mocker()
    def test_get_page_failure(self, m):
        """Test page retrieval failure."""
        test_url = "https://example.com"
        
        m.get(test_url, status_code=404)
        
        scraper = WebScraper()
        
        with pytest.raises(requests.exceptions.HTTPError):
            scraper.get_page(test_url)
    
    def test_parse_html(self):
        """Test HTML parsing."""
        html = "<html><head><title>Test</title></head><body><p>Content</p></body></html>"
        
        scraper = WebScraper()
        soup = scraper.parse_html(html)
        
        assert soup.title.string == "Test"
        assert soup.find('p').string == "Content"
    
    def test_extract_links(self):
        """Test link extraction."""
        html = '''
        <html>
            <body>
                <a href="/page1">Link 1</a>
                <a href="https://example.com/page2">Link 2</a>
                <a href="#section">Link 3</a>
            </body>
        </html>
        '''
        
        scraper = WebScraper()
        soup = scraper.parse_html(html)
        links = scraper.extract_links(soup, "https://example.com")
        
        assert len(links) == 3
        assert "https://example.com/page1" in links
        assert "https://example.com/page2" in links
        assert "https://example.com#section" in links
    
    @requests_mock.Mocker()
    def test_scrape_basic(self, m):
        """Test basic scraping functionality."""
        test_url = "https://example.com"
        test_html = '''
        <html>
            <head><title>Test Page</title></head>
            <body>
                <h1>Main Title</h1>
                <p>Some content here.</p>
                <a href="/link1">Link 1</a>
            </body>
        </html>
        '''
        
        m.get(test_url, text=test_html)
        
        scraper = WebScraper()
        result = scraper.scrape(test_url)
        
        assert result['url'] == test_url
        assert result['title'] == "Test Page"
        assert 'content' in result
        assert 'links' in result
        assert 'scraped_at' in result
        assert len(result['links']) == 1
    
    @requests_mock.Mocker()
    def test_scrape_with_selector(self, m):
        """Test scraping with CSS selector."""
        test_url = "https://example.com"
        test_html = '''
        <html>
            <body>
                <div class="content">
                    <p>Paragraph 1</p>
                    <p>Paragraph 2</p>
                </div>
                <div class="sidebar">
                    <p>Sidebar content</p>
                </div>
            </body>
        </html>
        '''
        
        m.get(test_url, text=test_html)
        
        scraper = WebScraper()
        result = scraper.scrape(test_url, selector=".content p")
        
        assert 'selected_content' in result
        assert len(result['selected_content']) == 2
        assert "Paragraph 1" in result['selected_content'][0]
        assert "Paragraph 2" in result['selected_content'][1]
