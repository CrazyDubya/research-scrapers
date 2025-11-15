"""Tests for pagination handler."""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from research_scrapers.web_scraper.pagination_handler import PaginationHandler


class TestPaginationHandler:
    """Test PaginationHandler class."""
    
    @pytest.fixture
    def handler(self):
        """Create test pagination handler."""
        return PaginationHandler(
            method="next_button",
            max_pages=5,
            wait_between_pages=0.0  # No delay for testing
        )
    
    @pytest.fixture
    def handler_numbered(self):
        """Create pagination handler for numbered pages."""
        return PaginationHandler(
            method="numbered",
            max_pages=3,
            wait_between_pages=0.0
        )
    
    @pytest.fixture
    def handler_url_pattern(self):
        """Create pagination handler for URL pattern."""
        return PaginationHandler(
            method="url_pattern",
            page_number_pattern="https://example.com/page/{page}",
            max_pages=3,
            wait_between_pages=0.0
        )
    
    @pytest.fixture
    def sample_html_with_next(self):
        """Sample HTML with next button."""
        return """
        <html>
            <body>
                <div class="content">Page content</div>
                <div class="pagination">
                    <a href="/page/1">1</a>
                    <a href="/page/2" class="current">2</a>
                    <a href="/page/3" rel="next">Next</a>
                </div>
            </body>
        </html>
        """
    
    @pytest.fixture
    def sample_html_no_next(self):
        """Sample HTML without next button."""
        return """
        <html>
            <body>
                <div class="content">Last page content</div>
                <div class="pagination">
                    <a href="/page/1">1</a>
                    <a href="/page/2">2</a>
                    <a href="/page/3" class="current">3</a>
                </div>
            </body>
        </html>
        """
    
    @pytest.fixture
    def sample_html_with_numbered(self):
        """Sample HTML with numbered pagination."""
        return """
        <html>
            <body>
                <div class="content">Page content</div>
                <div class="pagination">
                    <a href="/page/1">1</a>
                    <a href="/page/2">2</a>
                    <a href="/page/3">3</a>
                    <a href="/page/4">4</a>
                    <a href="/page/5">5</a>
                </div>
            </body>
        </html>
        """
    
    # ========== Initialization Tests ==========
    
    def test_initialization_default(self):
        """Test default initialization."""
        handler = PaginationHandler()
        assert handler.method == "next_button"
        assert handler.max_pages == 10
        assert handler.wait_between_pages == 2.0
        assert handler.current_page == 1
        assert len(handler.visited_urls) == 0
    
    def test_initialization_custom(self):
        """Test custom initialization."""
        handler = PaginationHandler(
            method="numbered",
            next_selector=".custom-next",
            page_number_pattern="https://test.com/{page}",
            max_pages=20,
            wait_between_pages=1.5
        )
        assert handler.method == "numbered"
        assert handler.next_selector == ".custom-next"
        assert handler.page_number_pattern == "https://test.com/{page}"
        assert handler.max_pages == 20
        assert handler.wait_between_pages == 1.5
    
    def test_initialization_method_lowercase(self):
        """Test that method is converted to lowercase."""
        handler = PaginationHandler(method="NEXT_BUTTON")
        assert handler.method == "next_button"
    
    def test_get_default_next_selector(self, handler):
        """Test default next selector."""
        selector = handler._get_default_next_selector()
        assert "a[rel='next']" in selector
        assert ".next-page" in selector
        assert ".pagination-next" in selector
        assert "a:contains('Next')" in selector
    
    # ========== URL Generation Tests ==========
    
    def test_get_page_urls_next_button(self, handler, sample_html_with_next):
        """Test URL generation with next button pagination."""
        start_url = "https://example.com/page/1"
        urls = list(handler.get_page_urls(start_url, sample_html_with_next))
        
        assert len(urls) >= 1
        assert urls[0] == start_url
    
    def test_get_page_urls_numbered(self, handler_numbered):
        """Test URL generation with numbered pagination."""
        start_url = "https://example.com/articles"
        urls = list(handler_numbered.get_page_urls(start_url))
        
        assert len(urls) == 3
        assert "page=1" in urls[0]
        assert "page=2" in urls[1]
        assert "page=3" in urls[2]
    
    def test_get_page_urls_url_pattern(self, handler_url_pattern):
        """Test URL generation with URL pattern."""
        start_url = "https://example.com"
        urls = list(handler_url_pattern.get_page_urls(start_url))
        
        assert len(urls) == 3
        assert urls[0] == "https://example.com/page/1"
        assert urls[1] == "https://example.com/page/2"
        assert urls[2] == "https://example.com/page/3"
    
    def test_get_page_urls_unknown_method(self):
        """Test URL generation with unknown method."""
        handler = PaginationHandler(method="unknown", wait_between_pages=0.0)
        start_url = "https://example.com"
        urls = list(handler.get_page_urls(start_url))
        
        # Should fallback to returning only start URL
        assert len(urls) == 1
        assert urls[0] == start_url
    
    # ========== Next Button Pagination Tests ==========
    
    def test_handle_next_button_pagination_single_page(self, handler):
        """Test next button pagination with single page."""
        start_url = "https://example.com/page/1"
        html = "<html><body>Content</body></html>"
        
        urls = list(handler._handle_next_button_pagination(start_url, html))
        
        assert len(urls) == 1
        assert urls[0] == start_url
        assert start_url in handler.visited_urls
    
    def test_handle_next_button_pagination_max_pages(self, handler):
        """Test next button pagination respects max_pages."""
        handler.max_pages = 2
        start_url = "https://example.com/page/1"
        html = """
        <html>
            <body>
                <a href="/page/2" rel="next">Next</a>
            </body>
        </html>
        """
        
        urls = list(handler._handle_next_button_pagination(start_url, html))
        
        # Should stop at max_pages
        assert len(urls) <= handler.max_pages
    
    def test_handle_next_button_pagination_no_duplicates(self, handler):
        """Test that visited URLs are not revisited."""
        start_url = "https://example.com/page/1"
        handler.visited_urls.add(start_url)
        
        urls = list(handler._handle_next_button_pagination(start_url, None))
        
        assert len(urls) == 0
    
    def test_handle_next_button_pagination_updates_current_page(self, handler):
        """Test that current_page is updated."""
        start_url = "https://example.com/page/1"
        html = "<html><body>Content</body></html>"
        
        list(handler._handle_next_button_pagination(start_url, html))
        
        assert handler.current_page > 1
    
    # ========== Numbered Pagination Tests ==========
    
    def test_handle_numbered_pagination(self, handler_numbered):
        """Test numbered pagination."""
        start_url = "https://example.com/articles"
        urls = list(handler_numbered._handle_numbered_pagination(start_url))
        
        assert len(urls) == 3
        for i, url in enumerate(urls, start=1):
            assert f"page={i}" in url
    
    def test_handle_numbered_pagination_with_existing_params(self, handler_numbered):
        """Test numbered pagination preserves existing query parameters."""
        start_url = "https://example.com/articles?category=tech&sort=date"
        urls = list(handler_numbered._handle_numbered_pagination(start_url))
        
        assert len(urls) == 3
        for url in urls:
            assert "category=tech" in url
            assert "sort=date" in url
    
    def test_handle_numbered_pagination_no_duplicates(self, handler_numbered):
        """Test numbered pagination avoids duplicates."""
        start_url = "https://example.com/articles"
        
        # First iteration
        urls1 = list(handler_numbered._handle_numbered_pagination(start_url))
        
        # Second iteration should return no URLs (all already visited)
        urls2 = list(handler_numbered._handle_numbered_pagination(start_url))
        
        assert len(urls1) == 3
        assert len(urls2) == 0
    
    # ========== URL Pattern Pagination Tests ==========
    
    def test_handle_url_pattern_pagination(self, handler_url_pattern):
        """Test URL pattern pagination."""
        urls = list(handler_url_pattern._handle_url_pattern_pagination())
        
        assert len(urls) == 3
        assert urls[0] == "https://example.com/page/1"
        assert urls[1] == "https://example.com/page/2"
        assert urls[2] == "https://example.com/page/3"
    
    def test_handle_url_pattern_pagination_no_pattern(self):
        """Test URL pattern pagination without pattern."""
        handler = PaginationHandler(
            method="url_pattern",
            max_pages=3,
            wait_between_pages=0.0
        )
        
        urls = list(handler._handle_url_pattern_pagination())
        
        # Should return no URLs when pattern is missing
        assert len(urls) == 0
    
    def test_handle_url_pattern_pagination_complex_pattern(self):
        """Test URL pattern with complex placeholder."""
        handler = PaginationHandler(
            method="url_pattern",
            page_number_pattern="https://api.example.com/v1/items?offset={page}0&limit=10",
            max_pages=3,
            wait_between_pages=0.0
        )
        
        urls = list(handler._handle_url_pattern_pagination())
        
        assert len(urls) == 3
        assert "offset=10" in urls[0]
        assert "offset=20" in urls[1]
        assert "offset=30" in urls[2]
    
    # ========== Find Next URL Tests ==========
    
    def test_find_next_url_with_rel_next(self, handler):
        """Test finding next URL with rel='next' attribute."""
        html = """
        <html>
            <body>
                <a href="/page/2" rel="next">Next</a>
            </body>
        </html>
        """
        current_url = "https://example.com/page/1"
        
        next_url = handler._find_next_url(html, current_url)
        
        assert next_url == "https://example.com/page/2"
    
    def test_find_next_url_with_class_next(self, handler):
        """Test finding next URL with class='next'."""
        html = """
        <html>
            <body>
                <a href="/page/2" class="next">Next Page</a>
            </body>
        </html>
        """
        current_url = "https://example.com/page/1"
        
        next_url = handler._find_next_url(html, current_url)
        
        assert next_url == "https://example.com/page/2"
    
    def test_find_next_url_with_text_next(self, handler):
        """Test finding next URL by text content."""
        html = """
        <html>
            <body>
                <div class="pagination">
                    <a href="/page/2">next</a>
                </div>
            </body>
        </html>
        """
        current_url = "https://example.com/page/1"
        
        next_url = handler._find_next_url(html, current_url)
        
        assert next_url == "https://example.com/page/2"
    
    def test_find_next_url_with_arrow_symbol(self, handler):
        """Test finding next URL with arrow symbol."""
        html = """
        <html>
            <body>
                <a href="/page/2">→</a>
            </body>
        </html>
        """
        current_url = "https://example.com/page/1"
        
        next_url = handler._find_next_url(html, current_url)
        
        assert next_url == "https://example.com/page/2"
    
    def test_find_next_url_relative_url(self, handler):
        """Test finding next URL converts relative to absolute."""
        html = """
        <html>
            <body>
                <a href="page/2" rel="next">Next</a>
            </body>
        </html>
        """
        current_url = "https://example.com/page/1"
        
        next_url = handler._find_next_url(html, current_url)
        
        assert next_url.startswith("https://")
        assert "page/2" in next_url
    
    def test_find_next_url_not_found(self, handler):
        """Test finding next URL when none exists."""
        html = """
        <html>
            <body>
                <div class="content">Last page</div>
            </body>
        </html>
        """
        current_url = "https://example.com/page/10"
        
        next_url = handler._find_next_url(html, current_url)
        
        assert next_url is None
    
    def test_find_next_url_custom_selector(self):
        """Test finding next URL with custom selector."""
        handler = PaginationHandler(
            next_selector=".custom-next-button",
            wait_between_pages=0.0
        )
        html = """
        <html>
            <body>
                <a href="/page/2" class="custom-next-button">Next</a>
            </body>
        </html>
        """
        current_url = "https://example.com/page/1"
        
        next_url = handler._find_next_url(html, current_url)
        
        assert next_url == "https://example.com/page/2"
    
    # ========== URL Extraction and Building Tests ==========
    
    def test_extract_base_url_simple(self, handler):
        """Test extracting base URL from simple URL."""
        url = "https://example.com/articles"
        base_url = handler._extract_base_url(url)
        
        assert base_url == "https://example.com/articles"
    
    def test_extract_base_url_with_page_param(self, handler):
        """Test extracting base URL removes page parameter."""
        url = "https://example.com/articles?page=2"
        base_url = handler._extract_base_url(url)
        
        assert base_url == "https://example.com/articles"
        assert "page" not in base_url
    
    def test_extract_base_url_with_multiple_params(self, handler):
        """Test extracting base URL preserves non-page parameters."""
        url = "https://example.com/articles?category=tech&page=2&sort=date"
        base_url = handler._extract_base_url(url)
        
        assert "category=tech" in base_url
        assert "sort=date" in base_url
        assert "page=" not in base_url
    
    def test_extract_base_url_with_p_param(self, handler):
        """Test extracting base URL removes 'p' parameter."""
        url = "https://example.com/articles?p=3"
        base_url = handler._extract_base_url(url)
        
        assert "p=" not in base_url
    
    def test_build_numbered_url_simple(self, handler):
        """Test building numbered URL."""
        base_url = "https://example.com/articles"
        url = handler._build_numbered_url(base_url, 3)
        
        assert "page=3" in url
        assert url.startswith("https://example.com/articles")
    
    def test_build_numbered_url_with_existing_params(self, handler):
        """Test building numbered URL preserves existing parameters."""
        base_url = "https://example.com/articles?category=tech"
        url = handler._build_numbered_url(base_url, 2)
        
        assert "page=2" in url
        assert "category=tech" in url
    
    def test_build_numbered_url_multiple_pages(self, handler):
        """Test building multiple numbered URLs."""
        base_url = "https://example.com/articles"
        
        url1 = handler._build_numbered_url(base_url, 1)
        url2 = handler._build_numbered_url(base_url, 2)
        url3 = handler._build_numbered_url(base_url, 3)
        
        assert "page=1" in url1
        assert "page=2" in url2
        assert "page=3" in url3
    
    # ========== Pagination Detection Tests ==========
    
    def test_detect_pagination_type_next_button(self, handler, sample_html_with_next):
        """Test detecting next button pagination."""
        url = "https://example.com/page/1"
        result = handler.detect_pagination_type(sample_html_with_next, url)
        
        assert result["has_pagination"] is True
        assert result["type"] == "next_button"
        assert result["next_selector"] is not None
    
    def test_detect_pagination_type_numbered(self, handler, sample_html_with_numbered):
        """Test detecting numbered pagination."""
        url = "https://example.com/page/1"
        result = handler.detect_pagination_type(sample_html_with_numbered, url)
        
        assert result["has_pagination"] is True
        assert result["type"] is not None
        assert result["total_pages"] == 5
    
    def test_detect_pagination_type_no_pagination(self, handler):
        """Test detecting no pagination."""
        html = """
        <html>
            <body>
                <div class="content">Single page content</div>
            </body>
        </html>
        """
        url = "https://example.com"
        result = handler.detect_pagination_type(html, url)
        
        assert result["has_pagination"] is False
        assert result["type"] is None
    
    def test_detect_pagination_type_url_parameter(self, handler):
        """Test detecting URL parameter pagination."""
        html = "<html><body>Content</body></html>"
        url = "https://example.com/articles?page=2"
        result = handler.detect_pagination_type(html, url)
        
        assert result["has_pagination"] is True
        assert result["type"] == "url_parameter"
        assert result["current_page"] == 2
    
    def test_detect_pagination_type_with_multiple_indicators(self, handler):
        """Test detecting pagination with multiple indicators."""
        html = """
        <html>
            <body>
                <div class="pagination">
                    <a href="/page/1">1</a>
                    <a href="/page/2">2</a>
                    <a href="/page/3">3</a>
                    <a href="/page/4" rel="next">Next</a>
                </div>
            </body>
        </html>
        """
        url = "https://example.com/page/2"
        result = handler.detect_pagination_type(html, url)
        
        assert result["has_pagination"] is True
        # Should detect next button first
        assert result["type"] == "next_button"
    
    def test_detect_pagination_type_invalid_page_number(self, handler):
        """Test detecting pagination with invalid page number in URL."""
        html = "<html><body>Content</body></html>"
        url = "https://example.com/articles?page=invalid"
        result = handler.detect_pagination_type(html, url)
        
        # Should not crash on invalid page number
        assert result["current_page"] is None
    
    # ========== State Management Tests ==========
    
    def test_reset(self, handler):
        """Test resetting pagination state."""
        handler.current_page = 5
        handler.visited_urls.add("https://example.com/page/1")
        handler.visited_urls.add("https://example.com/page/2")
        
        handler.reset()
        
        assert handler.current_page == 1
        assert len(handler.visited_urls) == 0
    
    def test_get_stats(self, handler):
        """Test getting pagination statistics."""
        handler.current_page = 3
        handler.visited_urls.add("https://example.com/page/1")
        handler.visited_urls.add("https://example.com/page/2")
        
        stats = handler.get_stats()
        
        assert stats["method"] == "next_button"
        assert stats["current_page"] == 3
        assert stats["visited_urls"] == 2
        assert stats["max_pages"] == 5
    
    def test_get_stats_initial_state(self, handler):
        """Test getting statistics in initial state."""
        stats = handler.get_stats()
        
        assert stats["method"] == "next_button"
        assert stats["current_page"] == 1
        assert stats["visited_urls"] == 0
        assert stats["max_pages"] == 5
    
    # ========== Wait Between Pages Tests ==========
    
    def test_wait_between_pages_enabled(self):
        """Test that wait between pages is respected."""
        handler = PaginationHandler(
            method="numbered",
            max_pages=2,
            wait_between_pages=0.1  # Small delay for testing
        )
        
        start_url = "https://example.com/articles"
        start_time = time.time()
        
        list(handler._handle_numbered_pagination(start_url))
        
        elapsed = time.time() - start_time
        
        # Should wait at least once (between page 1 and 2)
        # Allow some tolerance for timing variations
        assert elapsed >= 0.05
    
    def test_wait_between_pages_disabled(self, handler_numbered):
        """Test that no wait occurs when disabled."""
        # handler_numbered has wait_between_pages=0.0
        start_url = "https://example.com/articles"
        start_time = time.time()
        
        list(handler_numbered._handle_numbered_pagination(start_url))
        
        elapsed = time.time() - start_time
        
        # Should be very fast with no delays
        assert elapsed < 0.5
    
    def test_wait_not_called_on_last_page(self):
        """Test that wait is not called after the last page."""
        handler = PaginationHandler(
            method="url_pattern",
            page_number_pattern="https://example.com/page/{page}",
            max_pages=2,
            wait_between_pages=0.1
        )
        
        with patch('time.sleep') as mock_sleep:
            list(handler._handle_url_pattern_pagination())
            
            # Should only sleep once (between page 1 and 2, not after page 2)
            assert mock_sleep.call_count == 1
    
    # ========== Edge Cases and Error Handling Tests ==========
    
    def test_handle_malformed_html(self, handler):
        """Test handling malformed HTML."""
        html = "<html><body><a href='/next'>Next"  # Missing closing tags
        current_url = "https://example.com/page/1"
        
        # Should not crash on malformed HTML
        next_url = handler._find_next_url(html, current_url)
        
        # BeautifulSoup is forgiving, so this might still work
        assert next_url is None or isinstance(next_url, str)
    
    def test_handle_empty_html(self, handler):
        """Test handling empty HTML."""
        html = ""
        current_url = "https://example.com/page/1"
        
        next_url = handler._find_next_url(html, current_url)
        
        assert next_url is None
    
    def test_handle_url_with_fragment(self, handler):
        """Test handling URLs with fragments."""
        url = "https://example.com/articles?page=2#section"
        base_url = handler._extract_base_url(url)
        
        # Fragment should be removed
        assert "#section" not in base_url
    
    def test_pagination_with_zero_max_pages(self):
        """Test pagination with max_pages=0."""
        handler = PaginationHandler(method="numbered", max_pages=0, wait_between_pages=0.0)
        start_url = "https://example.com/articles"
        
        urls = list(handler._handle_numbered_pagination(start_url))
        
        assert len(urls) == 0
    
    def test_pagination_with_negative_max_pages(self):
        """Test pagination with negative max_pages."""
        handler = PaginationHandler(method="numbered", max_pages=-1, wait_between_pages=0.0)
        start_url = "https://example.com/articles"
        
        urls = list(handler._handle_numbered_pagination(start_url))
        
        # Should handle gracefully (no URLs generated)
        assert len(urls) == 0
    
    def test_next_url_without_href(self, handler):
        """Test finding next URL when link has no href attribute."""
        html = """
        <html>
            <body>
                <a rel="next">Next</a>
            </body>
        </html>
        """
        current_url = "https://example.com/page/1"
        
        next_url = handler._find_next_url(html, current_url)
        
        assert next_url is None
    
    def test_multiple_next_buttons(self, handler):
        """Test handling multiple next buttons (should use first found)."""
        html = """
        <html>
            <body>
                <a href="/page/2" rel="next">Next</a>
                <a href="/page/3" rel="next">Next</a>
            </body>
        </html>
        """
        current_url = "https://example.com/page/1"
        
        next_url = handler._find_next_url(html, current_url)
        
        # Should find the first next button
        assert next_url == "https://example.com/page/2"
    
    # ========== Integration Tests ==========
    
    def test_full_pagination_workflow_next_button(self, handler):
        """Test complete pagination workflow with next button."""
        start_url = "https://example.com/page/1"
        html = """
        <html>
            <body>
                <div class="content">Page 1</div>
                <a href="/page/2" rel="next">Next</a>
            </body>
        </html>
        """
        
        urls = list(handler.get_page_urls(start_url, html))
        stats = handler.get_stats()
        
        assert len(urls) >= 1
        assert stats["visited_urls"] >= 1
        assert start_url in handler.visited_urls
    
    def test_full_pagination_workflow_numbered(self, handler_numbered):
        """Test complete pagination workflow with numbered pages."""
        start_url = "https://example.com/articles?category=tech"
        
        # Get initial stats
        initial_stats = handler_numbered.get_stats()
        assert initial_stats["visited_urls"] == 0
        
        # Generate URLs
        urls = list(handler_numbered.get_page_urls(start_url))
        
        # Verify results
        assert len(urls) == 3
        assert all("category=tech" in url for url in urls)
        
        # Check final stats
        final_stats = handler_numbered.get_stats()
        assert final_stats["visited_urls"] == 3
        
        # Reset and verify
        handler_numbered.reset()
        reset_stats = handler_numbered.get_stats()
        assert reset_stats["visited_urls"] == 0
        assert reset_stats["current_page"] == 1
    
    def test_full_pagination_workflow_url_pattern(self, handler_url_pattern):
        """Test complete pagination workflow with URL pattern."""
        start_url = "https://example.com"
        
        urls = list(handler_url_pattern.get_page_urls(start_url))
        
        assert len(urls) == 3
        assert all(url.startswith("https://example.com/page/") for url in urls)
        
        stats = handler_url_pattern.get_stats()
        assert stats["visited_urls"] == 3
        assert stats["method"] == "url_pattern"
