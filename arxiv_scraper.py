#!/usr/bin/env python3
"""
Comprehensive ArXiv Research Paper Scraper

This scraper extracts comprehensive paper metadata, abstracts, full-text content,
and provides advanced search capabilities for ArXiv papers. It leverages the utils.py
and config.py modules for robust operation.

Features:
- ArXiv API integration with XML parsing
- Search by categories, authors, date ranges, keywords
- Extract metadata (title, authors, abstract, publication date, categories)
- PDF download capabilities with retry logic
- Text extraction from PDFs using multiple methods
- Rate limiting per ArXiv guidelines (3 seconds between requests)
- Batch operations with progress tracking
- Comprehensive CLI interface with filtering options
- Data validation and error handling
- Export to multiple formats (JSON, CSV, XML)

Author: Stephen Thompson
"""

import argparse
import json
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
import concurrent.futures
from dataclasses import dataclass, asdict
import urllib.parse
import urllib.request
import re
from io import BytesIO

# Import our utility modules
try:
    from utils import (
        RateLimiter, APIResponseProcessor, DataFormatter, FileManager,
        setup_logging, handle_api_errors, exponential_backoff, 
        create_session, DataValidator, ScrapingError, APIError,
        safe_get, get_timestamp
    )
    from config import (
        get_output_path, get_log_path, DEFAULT_PER_PAGE,
        JSON_INDENT, CLEAN_TEXT, VALIDATE_DATA
    )
except ImportError as e:
    print(f"Error: Missing required modules: {e}")
    print("Please ensure utils.py and config.py are present in the same directory.")
    sys.exit(1)

import requests
import logging

# Try to import PDF processing libraries
try:
    import PyPDF2
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

try:
    from pdfminer.high_level import extract_text as pdfminer_extract_text
    HAS_PDFMINER = True
except ImportError:
    HAS_PDFMINER = False

# Setup logging
logger = setup_logging(level='INFO', log_file=str(get_log_path('arxiv_scraper')))

# ArXiv API Configuration
ARXIV_API_BASE_URL = 'http://export.arxiv.org/api/query'
ARXIV_PDF_BASE_URL = 'https://arxiv.org/pdf'
ARXIV_ABS_BASE_URL = 'https://arxiv.org/abs'

# ArXiv rate limiting (per their guidelines)
ARXIV_RATE_LIMIT = 1.0 / 3.0  # 1 request per 3 seconds

# ArXiv categories
ARXIV_CATEGORIES = {
    # Physics
    'astro-ph': 'Astrophysics',
    'cond-mat': 'Condensed Matter',
    'gr-qc': 'General Relativity and Quantum Cosmology',
    'hep-ex': 'High Energy Physics - Experiment',
    'hep-lat': 'High Energy Physics - Lattice',
    'hep-ph': 'High Energy Physics - Phenomenology',
    'hep-th': 'High Energy Physics - Theory',
    'math-ph': 'Mathematical Physics',
    'nlin': 'Nonlinear Sciences',
    'nucl-ex': 'Nuclear Experiment',
    'nucl-th': 'Nuclear Theory',
    'physics': 'Physics',
    'quant-ph': 'Quantum Physics',
    
    # Mathematics
    'math': 'Mathematics',
    
    # Computer Science
    'cs': 'Computer Science',
    
    # Quantitative Biology
    'q-bio': 'Quantitative Biology',
    
    # Quantitative Finance
    'q-fin': 'Quantitative Finance',
    
    # Statistics
    'stat': 'Statistics',
    
    # Electrical Engineering and Systems Science
    'eess': 'Electrical Engineering and Systems Science',
    
    # Economics
    'econ': 'Economics'
}


@dataclass
class ArxivSearchOptions:
    """Configuration options for ArXiv searching."""
    query: Optional[str] = None
    categories: Optional[List[str]] = None
    authors: Optional[List[str]] = None
    title_keywords: Optional[List[str]] = None
    abstract_keywords: Optional[List[str]] = None
    
    # Date filtering
    start_date: Optional[str] = None  # YYYY-MM-DD format
    end_date: Optional[str] = None    # YYYY-MM-DD format
    
    # Result limits
    max_results: int = 100
    start_index: int = 0
    
    # Sorting
    sort_by: str = 'relevance'  # relevance, lastUpdatedDate, submittedDate
    sort_order: str = 'descending'  # ascending, descending
    
    # Content options
    include_pdf: bool = False
    include_full_text: bool = False
    extract_references: bool = False
    
    # Output options
    output_format: str = 'json'
    output_file: Optional[str] = None
    verbose: bool = False


@dataclass
class ArxivPaper:
    """Represents an ArXiv paper with all metadata."""
    id: str
    title: str
    authors: List[str]
    abstract: str
    categories: List[str]
    primary_category: str
    published: str
    updated: str
    doi: Optional[str] = None
    journal_ref: Optional[str] = None
    comments: Optional[str] = None
    pdf_url: str = ""
    abs_url: str = ""
    
    # Extended content (optional)
    pdf_content: Optional[bytes] = None
    full_text: Optional[str] = None
    references: Optional[List[str]] = None
    
    # Metadata
    scraped_at: Optional[str] = None
    scraping_success: bool = True
    scraping_errors: Optional[List[str]] = None


class ArxivScraper:
    """Comprehensive ArXiv paper scraper."""
    
    def __init__(self):
        """Initialize the ArXiv scraper."""
        self.session = create_session()
        self.rate_limiter = RateLimiter(ARXIV_RATE_LIMIT)
        self.response_processor = APIResponseProcessor()
        
        # PDF processing capabilities
        self.pdf_processors = []
        if HAS_PDFPLUMBER:
            self.pdf_processors.append('pdfplumber')
        if HAS_PYPDF2:
            self.pdf_processors.append('pypdf2')
        if HAS_PDFMINER:
            self.pdf_processors.append('pdfminer')
        
        if not self.pdf_processors:
            logger.warning("No PDF processing libraries found. Install PyPDF2, pdfplumber, or pdfminer for full-text extraction.")
        
        logger.info(f"Initialized ArXiv scraper with PDF processors: {', '.join(self.pdf_processors)}")
    
    @exponential_backoff(max_retries=3)
    @handle_api_errors
    def _make_request(self, url: str, params: Optional[Dict] = None) -> requests.Response:
        """Make a rate-limited request to ArXiv API."""
        self.rate_limiter._RateLimiter__call__(lambda: None)()  # Apply rate limiting
        
        logger.debug(f"Making request to: {url}")
        response = self.session.get(url, params=params)
        response.raise_for_status()
        
        return response
    
    def build_search_query(self, options: ArxivSearchOptions) -> str:
        """Build ArXiv API search query from options."""
        query_parts = []
        
        # Main query
        if options.query:
            query_parts.append(f"all:{options.query}")
        
        # Category filtering
        if options.categories:
            cat_queries = [f"cat:{cat}" for cat in options.categories]
            query_parts.append(f"({' OR '.join(cat_queries)})")
        
        # Author filtering
        if options.authors:
            author_queries = [f"au:{author}" for author in options.authors]
            query_parts.append(f"({' OR '.join(author_queries)})")
        
        # Title keywords
        if options.title_keywords:
            title_queries = [f"ti:{keyword}" for keyword in options.title_keywords]
            query_parts.append(f"({' AND '.join(title_queries)})")
        
        # Abstract keywords
        if options.abstract_keywords:
            abs_queries = [f"abs:{keyword}" for keyword in options.abstract_keywords]
            query_parts.append(f"({' AND '.join(abs_queries)})")
        
        # Combine all parts
        if query_parts:
            return ' AND '.join(query_parts)
        else:
            return 'all:*'  # Default to all papers if no specific query
    
    def search_papers(self, options: ArxivSearchOptions) -> List[ArxivPaper]:
        """
        Search for papers on ArXiv.
        
        Args:
            options: Search configuration options
            
        Returns:
            List of ArXiv papers matching the search criteria
        """
        logger.info(f"Starting ArXiv search with options: {options}")
        start_time = time.time()
        
        # Build search query
        search_query = self.build_search_query(options)
        logger.info(f"Search query: {search_query}")
        
        # Prepare API parameters
        params = {
            'search_query': search_query,
            'start': options.start_index,
            'max_results': options.max_results,
            'sortBy': options.sort_by,
            'sortOrder': options.sort_order
        }
        
        # Make API request
        response = self._make_request(ARXIV_API_BASE_URL, params=params)
        
        # Parse XML response
        papers = self._parse_arxiv_response(response.text)
        
        # Filter by date if specified
        if options.start_date or options.end_date:
            papers = self._filter_papers_by_date(papers, options.start_date, options.end_date)
        
        # Download additional content if requested
        if options.include_pdf or options.include_full_text:
            papers = self._enhance_papers_with_content(papers, options)
        
        end_time = time.time()
        logger.info(f"Search completed in {end_time - start_time:.2f}s. Found {len(papers)} papers.")
        
        return papers
    
    def _parse_arxiv_response(self, xml_content: str) -> List[ArxivPaper]:
        """Parse ArXiv API XML response."""
        papers = []
        
        try:
            root = ET.fromstring(xml_content)
            
            # Define namespaces
            namespaces = {
                'atom': 'http://www.w3.org/2005/Atom',
                'arxiv': 'http://arxiv.org/schemas/atom'
            }
            
            # Find all entry elements
            entries = root.findall('atom:entry', namespaces)
            
            for entry in entries:
                try:
                    paper = self._parse_paper_entry(entry, namespaces)
                    if paper:
                        papers.append(paper)
                except Exception as e:
                    logger.warning(f"Failed to parse paper entry: {e}")
                    continue
            
        except ET.ParseError as e:
            logger.error(f"Failed to parse ArXiv XML response: {e}")
            raise APIError(f"Invalid XML response from ArXiv: {e}")
        
        return papers
    
    def _parse_paper_entry(self, entry: ET.Element, namespaces: Dict[str, str]) -> Optional[ArxivPaper]:
        """Parse a single paper entry from ArXiv XML."""
        try:
            # Extract basic information
            id_elem = entry.find('atom:id', namespaces)
            if id_elem is None:
                return None
            
            paper_id = id_elem.text.split('/')[-1]  # Extract ID from URL
            
            title_elem = entry.find('atom:title', namespaces)
            title = DataValidator.clean_text(title_elem.text) if title_elem is not None else ""
            
            summary_elem = entry.find('atom:summary', namespaces)
            abstract = DataValidator.clean_text(summary_elem.text) if summary_elem is not None else ""
            
            # Extract authors
            authors = []
            author_elems = entry.findall('atom:author', namespaces)
            for author_elem in author_elems:
                name_elem = author_elem.find('atom:name', namespaces)
                if name_elem is not None:
                    authors.append(name_elem.text.strip())
            
            # Extract categories
            categories = []
            primary_category = ""
            
            primary_cat_elem = entry.find('arxiv:primary_category', namespaces)
            if primary_cat_elem is not None:
                primary_category = primary_cat_elem.get('term', '')
                categories.append(primary_category)
            
            category_elems = entry.findall('atom:category', namespaces)
            for cat_elem in category_elems:
                term = cat_elem.get('term', '')
                if term and term not in categories:
                    categories.append(term)
            
            # Extract dates
            published_elem = entry.find('atom:published', namespaces)
            published = published_elem.text if published_elem is not None else ""
            
            updated_elem = entry.find('atom:updated', namespaces)
            updated = updated_elem.text if updated_elem is not None else ""
            
            # Extract optional fields
            doi = None
            journal_ref = None
            comments = None
            
            doi_elem = entry.find('arxiv:doi', namespaces)
            if doi_elem is not None:
                doi = doi_elem.text
            
            journal_elem = entry.find('arxiv:journal_ref', namespaces)
            if journal_elem is not None:
                journal_ref = journal_elem.text
            
            comment_elem = entry.find('arxiv:comment', namespaces)
            if comment_elem is not None:
                comments = comment_elem.text
            
            # Build URLs
            pdf_url = f"{ARXIV_PDF_BASE_URL}/{paper_id}.pdf"
            abs_url = f"{ARXIV_ABS_BASE_URL}/{paper_id}"
            
            # Create paper object
            paper = ArxivPaper(
                id=paper_id,
                title=title,
                authors=authors,
                abstract=abstract,
                categories=categories,
                primary_category=primary_category,
                published=published,
                updated=updated,
                doi=doi,
                journal_ref=journal_ref,
                comments=comments,
                pdf_url=pdf_url,
                abs_url=abs_url,
                scraped_at=get_timestamp()
            )
            
            return paper
            
        except Exception as e:
            logger.warning(f"Error parsing paper entry: {e}")
            return None
    
    def _filter_papers_by_date(self, papers: List[ArxivPaper], 
                              start_date: Optional[str], 
                              end_date: Optional[str]) -> List[ArxivPaper]:
        """Filter papers by publication date range."""
        if not start_date and not end_date:
            return papers
        
        filtered_papers = []
        
        for paper in papers:
            try:
                # Parse paper publication date
                pub_date = datetime.fromisoformat(paper.published.replace('Z', '+00:00'))
                pub_date_str = pub_date.strftime('%Y-%m-%d')
                
                # Check date range
                if start_date and pub_date_str < start_date:
                    continue
                if end_date and pub_date_str > end_date:
                    continue
                
                filtered_papers.append(paper)
                
            except (ValueError, AttributeError) as e:
                logger.warning(f"Failed to parse date for paper {paper.id}: {e}")
                # Include paper if date parsing fails
                filtered_papers.append(paper)
        
        logger.info(f"Date filtering: {len(papers)} -> {len(filtered_papers)} papers")
        return filtered_papers
    
    def _enhance_papers_with_content(self, papers: List[ArxivPaper], 
                                   options: ArxivSearchOptions) -> List[ArxivPaper]:
        """Download and extract additional content for papers."""
        logger.info(f"Enhancing {len(papers)} papers with additional content...")
        
        enhanced_papers = []
        
        for i, paper in enumerate(papers):
            logger.info(f"Processing paper {i+1}/{len(papers)}: {paper.id}")
            
            try:
                # Download PDF if requested
                if options.include_pdf:
                    paper.pdf_content = self.download_pdf(paper.pdf_url)
                
                # Extract full text if requested
                if options.include_full_text and paper.pdf_content:
                    paper.full_text = self.extract_text_from_pdf(paper.pdf_content)
                
                # Extract references if requested
                if options.extract_references and paper.full_text:
                    paper.references = self.extract_references(paper.full_text)
                
                paper.scraping_success = True
                
            except Exception as e:
                logger.warning(f"Failed to enhance paper {paper.id}: {e}")
                paper.scraping_success = False
                if paper.scraping_errors is None:
                    paper.scraping_errors = []
                paper.scraping_errors.append(str(e))
            
            enhanced_papers.append(paper)
        
        return enhanced_papers
    
    @exponential_backoff(max_retries=3)
    def download_pdf(self, pdf_url: str) -> bytes:
        """Download PDF content from ArXiv."""
        logger.debug(f"Downloading PDF: {pdf_url}")
        
        # Apply rate limiting
        self.rate_limiter._RateLimiter__call__(lambda: None)()
        
        response = self.session.get(pdf_url)
        response.raise_for_status()
        
        if response.headers.get('content-type', '').startswith('application/pdf'):
            return response.content
        else:
            raise APIError(f"Expected PDF content, got: {response.headers.get('content-type')}")
    
    def extract_text_from_pdf(self, pdf_content: bytes) -> str:
        """Extract text from PDF using available libraries."""
        if not self.pdf_processors:
            raise ScrapingError("No PDF processing libraries available")
        
        text = ""
        
        # Try each processor in order of preference
        for processor in self.pdf_processors:
            try:
                if processor == 'pdfplumber':
                    text = self._extract_with_pdfplumber(pdf_content)
                elif processor == 'pdfminer':
                    text = self._extract_with_pdfminer(pdf_content)
                elif processor == 'pypdf2':
                    text = self._extract_with_pypdf2(pdf_content)
                
                if text.strip():  # If we got meaningful text, return it
                    logger.debug(f"Successfully extracted text using {processor}")
                    return DataValidator.clean_text(text)
                    
            except Exception as e:
                logger.warning(f"Failed to extract text with {processor}: {e}")
                continue
        
        raise ScrapingError("Failed to extract text with any available PDF processor")
    
    def _extract_with_pdfplumber(self, pdf_content: bytes) -> str:
        """Extract text using pdfplumber."""
        import pdfplumber
        
        text_parts = []
        with pdfplumber.open(BytesIO(pdf_content)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        
        return '\n'.join(text_parts)
    
    def _extract_with_pdfminer(self, pdf_content: bytes) -> str:
        """Extract text using pdfminer."""
        return pdfminer_extract_text(BytesIO(pdf_content))
    
    def _extract_with_pypdf2(self, pdf_content: bytes) -> str:
        """Extract text using PyPDF2."""
        text_parts = []
        
        pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_content))
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
        
        return '\n'.join(text_parts)
    
    def extract_references(self, full_text: str) -> List[str]:
        """Extract references from paper full text."""
        references = []
        
        # Look for references section
        ref_patterns = [
            r'(?i)references?\s*\n(.*?)(?=\n\s*(?:appendix|acknowledgment|figure|table|\Z))',
            r'(?i)bibliography\s*\n(.*?)(?=\n\s*(?:appendix|acknowledgment|figure|table|\Z))',
            r'\[(\d+)\]\s*([^\[\n]+(?:\n[^\[\n]+)*?)(?=\[\d+\]|\Z)'
        ]
        
        for pattern in ref_patterns:
            matches = re.findall(pattern, full_text, re.MULTILINE | re.DOTALL)
            if matches:
                if isinstance(matches[0], tuple):
                    # Pattern with groups
                    for match in matches:
                        ref_text = ' '.join(match).strip()
                        if len(ref_text) > 20:  # Filter out very short matches
                            references.append(DataValidator.clean_text(ref_text))
                else:
                    # Single group pattern
                    ref_section = matches[0]
                    # Split by common reference delimiters
                    ref_lines = re.split(r'\n(?=\[\d+\]|\d+\.)', ref_section)
                    for line in ref_lines:
                        line = line.strip()
                        if len(line) > 20:
                            references.append(DataValidator.clean_text(line))
                break
        
        return references[:50]  # Limit to first 50 references
    
    def get_paper_by_id(self, arxiv_id: str, include_content: bool = False) -> Optional[ArxivPaper]:
        """
        Get a specific paper by ArXiv ID.
        
        Args:
            arxiv_id: ArXiv paper ID (e.g., '2301.07041')
            include_content: Whether to download PDF and extract full text
            
        Returns:
            ArxivPaper object or None if not found
        """
        logger.info(f"Fetching paper by ID: {arxiv_id}")
        
        # Search for the specific paper
        options = ArxivSearchOptions(
            query=f"id:{arxiv_id}",
            max_results=1,
            include_pdf=include_content,
            include_full_text=include_content
        )
        
        papers = self.search_papers(options)
        return papers[0] if papers else None
    
    def batch_download_papers(self, paper_ids: List[str], 
                            include_content: bool = False,
                            max_workers: int = 3) -> List[ArxivPaper]:
        """
        Download multiple papers in batch with concurrent processing.
        
        Args:
            paper_ids: List of ArXiv paper IDs
            include_content: Whether to download PDF and extract full text
            max_workers: Maximum number of concurrent workers
            
        Returns:
            List of ArxivPaper objects
        """
        logger.info(f"Starting batch download of {len(paper_ids)} papers")
        
        papers = []
        
        # Use ThreadPoolExecutor for concurrent downloads
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_id = {
                executor.submit(self.get_paper_by_id, paper_id, include_content): paper_id
                for paper_id in paper_ids
            }
            
            # Collect results
            for future in concurrent.futures.as_completed(future_to_id):
                paper_id = future_to_id[future]
                try:
                    paper = future.result()
                    if paper:
                        papers.append(paper)
                        logger.info(f"✓ Downloaded paper: {paper_id}")
                    else:
                        logger.warning(f"✗ Paper not found: {paper_id}")
                except Exception as e:
                    logger.error(f"✗ Failed to download paper {paper_id}: {e}")
        
        logger.info(f"Batch download completed. Successfully downloaded {len(papers)} papers.")
        return papers
    
    def search_by_category(self, category: str, max_results: int = 100,
                          include_content: bool = False) -> List[ArxivPaper]:
        """
        Search papers by ArXiv category.
        
        Args:
            category: ArXiv category (e.g., 'cs.AI', 'physics.gen-ph')
            max_results: Maximum number of results
            include_content: Whether to download PDF and extract full text
            
        Returns:
            List of ArxivPaper objects
        """
        options = ArxivSearchOptions(
            categories=[category],
            max_results=max_results,
            include_pdf=include_content,
            include_full_text=include_content,
            sort_by='submittedDate'
        )
        
        return self.search_papers(options)
    
    def search_recent_papers(self, days: int = 7, categories: Optional[List[str]] = None,
                           max_results: int = 100) -> List[ArxivPaper]:
        """
        Search for papers published in the last N days.
        
        Args:
            days: Number of days to look back
            categories: Optional list of categories to filter by
            max_results: Maximum number of results
            
        Returns:
            List of ArxivPaper objects
        """
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        options = ArxivSearchOptions(
            categories=categories,
            start_date=start_date,
            end_date=end_date,
            max_results=max_results,
            sort_by='submittedDate',
            sort_order='descending'
        )
        
        return self.search_papers(options)


def papers_to_dict_list(papers: List[ArxivPaper]) -> List[Dict[str, Any]]:
    """Convert list of ArxivPaper objects to list of dictionaries."""
    return [asdict(paper) for paper in papers]


def save_papers(papers: List[ArxivPaper], output_file: Path, format: str = 'json') -> None:
    """Save papers to file in specified format."""
    if format == 'json':
        data = {
            'scraped_at': get_timestamp(),
            'total_papers': len(papers),
            'papers': papers_to_dict_list(papers)
        }
        FileManager.save_json(data, output_file)
    
    elif format == 'csv':
        # Flatten paper data for CSV
        flattened_papers = []
        for paper in papers:
            paper_dict = asdict(paper)
            # Convert lists to comma-separated strings
            paper_dict['authors'] = ', '.join(paper_dict['authors'])
            paper_dict['categories'] = ', '.join(paper_dict['categories'])
            if paper_dict['references']:
                paper_dict['references'] = ' | '.join(paper_dict['references'][:5])  # Limit for CSV
            # Remove binary content
            paper_dict.pop('pdf_content', None)
            flattened_papers.append(paper_dict)
        
        FileManager.save_csv(flattened_papers, output_file)
    
    elif format == 'xml':
        # Create XML structure
        root = ET.Element('arxiv_papers')
        root.set('scraped_at', get_timestamp())
        root.set('total_papers', str(len(papers)))
        
        for paper in papers:
            paper_elem = ET.SubElement(root, 'paper')
            paper_dict = asdict(paper)
            
            for key, value in paper_dict.items():
                if key == 'pdf_content':  # Skip binary content
                    continue
                elif isinstance(value, list):
                    list_elem = ET.SubElement(paper_elem, key)
                    for item in value:
                        item_elem = ET.SubElement(list_elem, 'item')
                        item_elem.text = str(item)
                else:
                    elem = ET.SubElement(paper_elem, key)
                    elem.text = str(value) if value is not None else ''
        
        # Write XML to file
        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ", level=0)
        tree.write(output_file, encoding='utf-8', xml_declaration=True)


def print_paper_summary(paper: ArxivPaper) -> None:
    """Print a formatted summary of a paper."""
    print(f"\n{'='*80}")
    print(f"ID: {paper.id}")
    print(f"Title: {paper.title}")
    print(f"Authors: {', '.join(paper.authors)}")
    print(f"Primary Category: {paper.primary_category}")
    print(f"Categories: {', '.join(paper.categories)}")
    print(f"Published: {paper.published}")
    print(f"Updated: {paper.updated}")
    
    if paper.doi:
        print(f"DOI: {paper.doi}")
    if paper.journal_ref:
        print(f"Journal: {paper.journal_ref}")
    if paper.comments:
        print(f"Comments: {paper.comments}")
    
    print(f"\nAbstract:")
    print(paper.abstract[:500] + "..." if len(paper.abstract) > 500 else paper.abstract)
    
    if paper.full_text:
        print(f"\nFull text length: {len(paper.full_text)} characters")
    if paper.references:
        print(f"References found: {len(paper.references)}")
    
    print(f"PDF URL: {paper.pdf_url}")
    print(f"Abstract URL: {paper.abs_url}")


def print_search_summary(papers: List[ArxivPaper], options: ArxivSearchOptions) -> None:
    """Print a summary of search results."""
    print(f"\n{'='*80}")
    print(f"ARXIV SEARCH SUMMARY")
    print(f"{'='*80}")
    print(f"Total papers found: {len(papers)}")
    
    if options.query:
        print(f"Query: {options.query}")
    if options.categories:
        print(f"Categories: {', '.join(options.categories)}")
    if options.authors:
        print(f"Authors: {', '.join(options.authors)}")
    if options.start_date or options.end_date:
        print(f"Date range: {options.start_date or 'any'} to {options.end_date or 'any'}")
    
    # Category breakdown
    if papers:
        category_counts = {}
        for paper in papers:
            for cat in paper.categories:
                category_counts[cat] = category_counts.get(cat, 0) + 1
        
        print(f"\nTop categories:")
        sorted_cats = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
        for cat, count in sorted_cats[:10]:
            print(f"  {cat}: {count}")
        
        # Year breakdown
        year_counts = {}
        for paper in papers:
            try:
                year = paper.published[:4]
                year_counts[year] = year_counts.get(year, 0) + 1
            except:
                pass
        
        if year_counts:
            print(f"\nPapers by year:")
            sorted_years = sorted(year_counts.items(), reverse=True)
            for year, count in sorted_years[:10]:
                print(f"  {year}: {count}")
    
    print(f"{'='*80}")


def main():
    """Command-line interface for the ArXiv scraper."""
    parser = argparse.ArgumentParser(
        description='Comprehensive ArXiv Research Paper Scraper',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Search for machine learning papers
  python arxiv_scraper.py --query "machine learning" --max-results 50
  
  # Search by category
  python arxiv_scraper.py --categories cs.AI cs.LG --max-results 100
  
  # Search by author
  python arxiv_scraper.py --authors "Geoffrey Hinton" "Yann LeCun"
  
  # Search recent papers with full content
  python arxiv_scraper.py --recent-days 7 --include-pdf --include-full-text
  
  # Get specific paper by ID
  python arxiv_scraper.py --paper-id 2301.07041 --include-full-text
  
  # Batch download papers
  python arxiv_scraper.py --paper-ids 2301.07041 2302.12345 --include-pdf
  
  # Search with date range
  python arxiv_scraper.py --query "quantum computing" --start-date 2023-01-01 --end-date 2023-12-31
  
  # Export to different formats
  python arxiv_scraper.py --query "deep learning" --format csv --output results.csv
        """
    )
    
    # Search options
    search_group = parser.add_argument_group('Search Options')
    search_group.add_argument('--query', help='General search query')
    search_group.add_argument('--categories', nargs='+', help='ArXiv categories to search')
    search_group.add_argument('--authors', nargs='+', help='Author names to search for')
    search_group.add_argument('--title-keywords', nargs='+', help='Keywords to search in titles')
    search_group.add_argument('--abstract-keywords', nargs='+', help='Keywords to search in abstracts')
    
    # Date filtering
    date_group = parser.add_argument_group('Date Filtering')
    date_group.add_argument('--start-date', help='Start date (YYYY-MM-DD)')
    date_group.add_argument('--end-date', help='End date (YYYY-MM-DD)')
    date_group.add_argument('--recent-days', type=int, help='Search papers from last N days')
    
    # Specific paper options
    paper_group = parser.add_argument_group('Specific Papers')
    paper_group.add_argument('--paper-id', help='Get specific paper by ArXiv ID')
    paper_group.add_argument('--paper-ids', nargs='+', help='Batch download papers by IDs')
    
    # Content options
    content_group = parser.add_argument_group('Content Options')
    content_group.add_argument('--include-pdf', action='store_true', help='Download PDF files')
    content_group.add_argument('--include-full-text', action='store_true', help='Extract full text from PDFs')
    content_group.add_argument('--extract-references', action='store_true', help='Extract references from papers')
    
    # Result options
    result_group = parser.add_argument_group('Result Options')
    result_group.add_argument('--max-results', type=int, default=100, help='Maximum number of results')
    result_group.add_argument('--start-index', type=int, default=0, help='Starting index for results')
    result_group.add_argument('--sort-by', choices=['relevance', 'lastUpdatedDate', 'submittedDate'], 
                             default='relevance', help='Sort results by')
    result_group.add_argument('--sort-order', choices=['ascending', 'descending'], 
                             default='descending', help='Sort order')
    
    # Output options
    output_group = parser.add_argument_group('Output Options')
    output_group.add_argument('--output', '-o', help='Output file path')
    output_group.add_argument('--format', choices=['json', 'csv', 'xml'], default='json', help='Output format')
    output_group.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    output_group.add_argument('--show-categories', action='store_true', help='Show available ArXiv categories')
    
    args = parser.parse_args()
    
    # Setup logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Show categories if requested
    if args.show_categories:
        print("Available ArXiv Categories:")
        print("=" * 50)
        for code, name in sorted(ARXIV_CATEGORIES.items()):
            print(f"{code:15} - {name}")
        return
    
    # Validate arguments
    if not any([args.query, args.categories, args.authors, args.title_keywords, 
                args.abstract_keywords, args.paper_id, args.paper_ids, args.recent_days]):
        parser.error("Must specify at least one search criterion")
    
    # Create scraper
    scraper = ArxivScraper()
    papers = []
    
    try:
        # Handle specific paper ID
        if args.paper_id:
            logger.info(f"Fetching paper: {args.paper_id}")
            paper = scraper.get_paper_by_id(
                args.paper_id, 
                include_content=args.include_pdf or args.include_full_text
            )
            if paper:
                papers = [paper]
                print_paper_summary(paper)
            else:
                print(f"Paper not found: {args.paper_id}")
                sys.exit(1)
        
        # Handle batch paper IDs
        elif args.paper_ids:
            logger.info(f"Batch downloading {len(args.paper_ids)} papers")
            papers = scraper.batch_download_papers(
                args.paper_ids,
                include_content=args.include_pdf or args.include_full_text
            )
        
        # Handle recent papers search
        elif args.recent_days:
            logger.info(f"Searching papers from last {args.recent_days} days")
            papers = scraper.search_recent_papers(
                days=args.recent_days,
                categories=args.categories,
                max_results=args.max_results
            )
        
        # Handle general search
        else:
            # Create search options
            options = ArxivSearchOptions(
                query=args.query,
                categories=args.categories,
                authors=args.authors,
                title_keywords=args.title_keywords,
                abstract_keywords=args.abstract_keywords,
                start_date=args.start_date,
                end_date=args.end_date,
                max_results=args.max_results,
                start_index=args.start_index,
                sort_by=args.sort_by,
                sort_order=args.sort_order,
                include_pdf=args.include_pdf,
                include_full_text=args.include_full_text,
                extract_references=args.extract_references,
                output_format=args.format,
                verbose=args.verbose
            )
            
            # Perform search
            papers = scraper.search_papers(options)
            print_search_summary(papers, options)
        
        # Save results if papers found
        if papers:
            # Determine output file
            if args.output:
                output_file = Path(args.output)
            else:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"arxiv_papers_{timestamp}"
                output_file = get_output_path(filename, args.format)
            
            # Save papers
            save_papers(papers, output_file, args.format)
            print(f"\n✓ Saved {len(papers)} papers to {output_file}")
            
            # Print sample if verbose
            if args.verbose and papers:
                print(f"\nSample paper:")
                print_paper_summary(papers[0])
        
        else:
            print("No papers found matching the search criteria.")
    
    except KeyboardInterrupt:
        logger.info("Search interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during search: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()