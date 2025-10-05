"""Tests for content extractor."""

import pytest
from research_scrapers.web_scraper.content_extractor import ContentExtractor


class TestContentExtractor:
    """Test ContentExtractor class."""
    
    @pytest.fixture
    def extractor(self):
        """Create test extractor."""
        return ContentExtractor(
            extract_metadata=True,
            clean_whitespace=True
        )
    
    @pytest.fixture
    def sample_html(self):
        """Sample HTML for testing."""
        return """
        <html>
        <head>
            <title>Test Article</title>
            <meta name="author" content="John Doe">
            <meta name="description" content="Test description">
        </head>
        <body>
            <nav>Navigation</nav>
            <article>
                <h1>Article Title</h1>
                <p>First paragraph with content.</p>
                <p>Second paragraph with more content.</p>
                <a href="https://example.com">Link</a>
            </article>
            <aside>Sidebar content</aside>
            <script>console.log('test');</script>
        </body>
        </html>
        """
    
    def test_extract_content(self, extractor, sample_html):
        """Test content extraction."""
        result = extractor.extract(sample_html, "https://example.com")
        
        assert result['url'] == "https://example.com"
        assert 'content' in result
        assert 'metadata' in result
        
        # Check that unwanted elements are removed
        assert 'Navigation' not in result['content']
        assert 'Sidebar' not in result['content']
        assert 'console.log' not in result['content']
        
        # Check that main content is preserved
        assert 'Article Title' in result['content']
        assert 'First paragraph' in result['content']
    
    def test_extract_metadata(self, extractor, sample_html):
        """Test metadata extraction."""
        result = extractor.extract(sample_html)
        metadata = result['metadata']
        
        assert metadata.get('title') == 'Test Article'
        assert metadata.get('author') == 'John Doe'
        assert metadata.get('description') == 'Test description'
    
    def test_targeted_extraction(self, extractor, sample_html):
        """Test targeted extraction with selectors."""
        selectors = {
            'title': 'h1',
            'paragraphs': 'p',
            'links': 'a'
        }
        
        result = extractor.extract_targeted(sample_html, selectors)
        extracted = result['extracted']
        
        assert extracted['title'] == 'Article Title'
        assert isinstance(extracted['paragraphs'], list)
        assert len(extracted['paragraphs']) == 2
        assert 'First paragraph' in extracted['paragraphs'][0]
    
    def test_detect_content_type(self, extractor):
        """Test content type detection."""
        article_html = '<article><p>Content</p></article>'
        blog_html = '<div class="blog-post"><p>Content</p></div>'
        docs_html = '<div class="documentation"><p>Content</p></div>'
        
        assert extractor.detect_content_type(article_html) == 'article'
        assert extractor.detect_content_type(blog_html) == 'blog'
        assert extractor.detect_content_type(docs_html) == 'documentation'
    
    def test_clean_whitespace(self, extractor):
        """Test whitespace cleaning."""
        html = '<p>Text   with    extra   spaces\n\n\nand\n\nnewlines</p>'
        result = extractor.extract(html)
        
        # Should clean up excessive whitespace
        content = result['content']
        assert '   ' not in content  # No triple spaces
        assert '\n\n\n' not in content  # No triple newlines
