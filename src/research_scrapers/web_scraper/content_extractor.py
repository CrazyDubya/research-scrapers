"""Content extraction and cleaning for web scraping."""

import re
from typing import Dict, List, Optional, Any
from bs4 import BeautifulSoup, Tag, NavigableString
from loguru import logger
from urllib.parse import urljoin, urlparse


class ContentExtractor:
    """Extract and clean content from HTML."""
    
    # Content type detection patterns
    CONTENT_PATTERNS = {
        "article": [
            {"name": "article"},
            {"class_": re.compile(r"article|post|content|entry")},
            {"itemprop": "articleBody"},
            {"role": "article"},
        ],
        "documentation": [
            {"class_": re.compile(r"docs|documentation|api-content|markdown-body")},
            {"role": "main"},
            {"id": re.compile(r"docs|documentation|content")},
        ],
        "blog": [
            {"class_": re.compile(r"blog|post|entry")},
            {"itemprop": "blogPost"},
        ],
    }
    
    # Metadata extraction selectors
    METADATA_SELECTORS = {
        "title": [
            ("meta", {"property": "og:title"}),
            ("meta", {"name": "twitter:title"}),
            ("title", {}),
            ("h1", {}),
        ],
        "description": [
            ("meta", {"property": "og:description"}),
            ("meta", {"name": "description"}),
            ("meta", {"name": "twitter:description"}),
        ],
        "author": [
            ("meta", {"name": "author"}),
            ("meta", {"property": "article:author"}),
            ({"class_": re.compile(r"author|byline")}, {}),
        ],
        "published_date": [
            ("meta", {"property": "article:published_time"}),
            ("time", {"datetime": True}),
            ({"class_": re.compile(r"date|published|time")}, {}),
        ],
        "keywords": [
            ("meta", {"name": "keywords"}),
            ("meta", {"property": "article:tag"}),
        ],
    }
    
    def __init__(
        self,
        remove_elements: Optional[List[str]] = None,
        clean_whitespace: bool = True,
        remove_empty_paragraphs: bool = True,
        preserve_formatting: bool = True,
        extract_metadata: bool = True,
        extract_links: bool = False,
    ):
        """
        Initialize content extractor.
        
        Args:
            remove_elements: List of elements/selectors to remove
            clean_whitespace: Clean excessive whitespace
            remove_empty_paragraphs: Remove empty paragraph elements
            preserve_formatting: Preserve text formatting (bold, italic, etc.)
            extract_metadata: Extract page metadata
            extract_links: Extract links from content
        """
        self.remove_elements = remove_elements or [
            "script", "style", "nav", "header", "footer", "aside",
            ".advertisement", ".ad", ".sidebar", ".comments"
        ]
        self.clean_whitespace = clean_whitespace
        self.remove_empty_paragraphs = remove_empty_paragraphs
        self.preserve_formatting = preserve_formatting
        self.extract_metadata = extract_metadata
        self.extract_links = extract_links
        
        logger.info("Initialized ContentExtractor")
    
    def extract(self, html: str, url: Optional[str] = None) -> Dict[str, Any]:
        """Extract content from HTML."""
        soup = BeautifulSoup(html, "lxml")
        
        result = {
            "url": url,
            "content": None,
            "metadata": {},
            "links": [],
        }
        
        # Extract metadata
        if self.extract_metadata:
            result["metadata"] = self._extract_metadata(soup)
        
        # Clean unwanted elements
        self._remove_unwanted_elements(soup)
        
        # Extract main content
        content_element = self._find_main_content(soup)
        if content_element:
            result["content"] = self._extract_text(content_element)
            
            if self.extract_links:
                result["links"] = self._extract_links(content_element, url)
        else:
            logger.warning("Could not find main content")
            result["content"] = self._extract_text(soup.body if soup.body else soup)
        
        return result
    
    def extract_targeted(self, html: str, selectors: Dict[str, str], url: Optional[str] = None) -> Dict[str, Any]:
        """Extract content using specific CSS selectors."""
        soup = BeautifulSoup(html, "lxml")
        
        result = {
            "url": url,
            "extracted": {},
            "metadata": {},
        }
        
        # Extract metadata
        if self.extract_metadata:
            result["metadata"] = self._extract_metadata(soup)
        
        # Extract using selectors
        for key, selector in selectors.items():
            try:
                elements = soup.select(selector)
                if elements:
                    if len(elements) == 1:
                        result["extracted"][key] = self._extract_text(elements[0])
                    else:
                        result["extracted"][key] = [
                            self._extract_text(elem) for elem in elements
                        ]
                    logger.debug(f"Extracted '{key}' using selector '{selector}'")
                else:
                    logger.warning(f"No elements found for selector '{selector}'")
                    result["extracted"][key] = None
            except Exception as e:
                logger.error(f"Error extracting '{key}': {e}")
                result["extracted"][key] = None
        
        return result
    
    def _find_main_content(self, soup: BeautifulSoup) -> Optional[Tag]:
        """Find main content element."""
        # Try content type patterns
        for content_type, patterns in self.CONTENT_PATTERNS.items():
            for pattern in patterns:
                element = soup.find(**pattern)
                if element:
                    logger.debug(f"Found main content using {content_type} pattern")
                    return element
        
        # Try common main content selectors
        main_selectors = [
            "main",
            "[role='main']",
            "#main",
            "#content",
            ".main-content",
            ".content",
        ]
        
        for selector in main_selectors:
            element = soup.select_one(selector)
            if element:
                logger.debug(f"Found main content using selector '{selector}'")
                return element
        
        # Fallback: find largest text block
        return self._find_largest_text_block(soup)
    
    def _find_largest_text_block(self, soup: BeautifulSoup) -> Optional[Tag]:
        """Find element with most text content."""
        candidates = soup.find_all(["div", "section", "article"])
        
        if not candidates:
            return None
        
        # Score by text length
        max_len = 0
        best_candidate = None
        
        for candidate in candidates:
            text = candidate.get_text(strip=True)
            if len(text) > max_len:
                max_len = len(text)
                best_candidate = candidate
        
        logger.debug(f"Found largest text block with {max_len} characters")
        return best_candidate
    
    def _remove_unwanted_elements(self, soup: BeautifulSoup) -> None:
        """Remove unwanted elements from soup."""
        for selector in self.remove_elements:
            try:
                # Handle both tag names and CSS selectors
                if selector.startswith(".") or selector.startswith("#") or "[" in selector:
                    elements = soup.select(selector)
                else:
                    elements = soup.find_all(selector)
                
                for element in elements:
                    element.decompose()
            except Exception as e:
                logger.warning(f"Error removing elements with selector '{selector}': {e}")
    
    def _extract_text(self, element: Tag) -> str:
        """Extract and clean text from element."""
        if self.preserve_formatting:
            text = self._get_formatted_text(element)
        else:
            text = element.get_text(separator=" ")
        
        if self.clean_whitespace:
            text = self._clean_whitespace(text)
        
        return text
    
    def _get_formatted_text(self, element: Tag) -> str:
        """Extract text while preserving basic formatting."""
        lines = []
        
        for child in element.descendants:
            if isinstance(child, NavigableString):
                text = str(child).strip()
                if text:
                    lines.append(text)
            elif isinstance(child, Tag):
                if child.name in ["br", "hr"]:
                    lines.append("\n")
                elif child.name in ["p", "div", "h1", "h2", "h3", "h4", "h5", "h6"]:
                    if lines and lines[-1] != "\n":
                        lines.append("\n\n")
        
        return " ".join(lines)
    
    def _clean_whitespace(self, text: str) -> str:
        """Clean excessive whitespace."""
        # Replace multiple spaces with single space
        text = re.sub(r" +", " ", text)
        
        # Replace multiple newlines with double newline
        text = re.sub(r"\n\s*\n+", "\n\n", text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def _extract_metadata(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract metadata from HTML."""
        metadata = {}
        
        for key, selectors in self.METADATA_SELECTORS.items():
            for selector_tuple in selectors:
                if len(selector_tuple) == 2:
                    tag_name, attrs = selector_tuple
                    
                    if isinstance(tag_name, dict):
                        # Class/attribute based selector
                        element = soup.find(**tag_name)
                    else:
                        element = soup.find(tag_name, attrs)
                    
                    if element:
                        # Extract value
                        if element.name == "meta":
                            value = element.get("content", "")
                        elif element.name == "time":
                            value = element.get("datetime", element.get_text(strip=True))
                        else:
                            value = element.get_text(strip=True)
                        
                        if value:
                            metadata[key] = value
                            break
        
        return metadata
    
    def _extract_links(self, element: Tag, base_url: Optional[str] = None) -> List[Dict[str, str]]:
        """Extract links from element."""
        links = []
        
        for link in element.find_all("a", href=True):
            href = link["href"]
            text = link.get_text(strip=True)
            
            # Make absolute URL if base_url provided
            if base_url:
                href = urljoin(base_url, href)
            
            links.append({
                "url": href,
                "text": text,
                "title": link.get("title", ""),
            })
        
        return links
    
    def detect_content_type(self, html: str) -> Optional[str]:
        """Detect content type from HTML."""
        soup = BeautifulSoup(html, "lxml")
        
        for content_type, patterns in self.CONTENT_PATTERNS.items():
            for pattern in patterns:
                if soup.find(**pattern):
                    logger.debug(f"Detected content type: {content_type}")
                    return content_type
        
        return None
