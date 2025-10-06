"""
Comprehensive Patent Database Scraper

A production-ready patent scraper that provides unified access to USPTO Patent API
and Google Patents for comprehensive patent research and analysis.

This module builds on the existing utility functions (RateLimiter, APIResponseProcessor, 
DataFormatter, FileManager) and follows the architecture patterns of the research-scrapers package.

Features:
- USPTO Patent API integration with full search capabilities
- Google Patents scraper with BeautifulSoup parsing
- Advanced search by keywords, inventors, assignees, CPC codes
- Patent metadata extraction (number, title, abstract, claims, citations)
- Date range filtering and status filtering
- Rate limiting per USPTO guidelines
- Comprehensive error handling and retry logic
- Multiple output formats (JSON, CSV, XML)
- Batch operations with concurrent processing
- Full-text patent content extraction
- Legal status and patent family tracking

Author: Stephen Thompson
"""

import os
import logging
import time
import re
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from urllib.parse import urljoin, quote, urlparse
import concurrent.futures
from io import StringIO

import requests
from bs4 import BeautifulSoup

# Import from the base scraper classes
from .scraper import BaseScraper
from .config import Config
from .utils import (
    rate_limit, retry_on_failure, clean_text, save_to_json, 
    load_from_json, setup_logging, validate_url, extract_domain,
    batch_process, create_output_directory
)

logger = logging.getLogger(__name__)

# USPTO API Configuration
USPTO_API_BASE_URL = 'https://developer.uspto.gov/ptab-api/v1'
USPTO_PATENT_API_URL = 'https://developer.uspto.gov/ds-api'
USPTO_SEARCH_URL = 'https://ppubs.uspto.gov/dirsearch-public/searches/searchWithBeginDate'

# Google Patents Configuration
GOOGLE_PATENTS_BASE_URL = 'https://patents.google.com'
GOOGLE_PATENTS_SEARCH_URL = 'https://patents.google.com/xhr/query'

# Patent Office URLs
PATENT_OFFICE_URLS = {
    'uspto': 'https://patft.uspto.gov',
    'epo': 'https://worldwide.espacenet.com',
    'wipo': 'https://patentscope.wipo.int',
    'google': 'https://patents.google.com'
}

# Rate limiting (USPTO guidelines: 120 requests per minute)
USPTO_RATE_LIMIT = 2.0  # 2 requests per second
GOOGLE_PATENTS_RATE_LIMIT = 1.0  # 1 request per second

# Patent classification systems
CPC_SECTIONS = {
    'A': 'Human Necessities',
    'B': 'Performing Operations; Transporting',
    'C': 'Chemistry; Metallurgy',
    'D': 'Textiles; Paper',
    'E': 'Fixed Constructions',
    'F': 'Mechanical Engineering; Lighting; Heating; Weapons; Blasting',
    'G': 'Physics',
    'H': 'Electricity',
    'Y': 'General Tagging of New Technological Developments'
}

IPC_SECTIONS = {
    'A': 'Human Necessities',
    'B': 'Performing Operations; Transporting',
    'C': 'Chemistry; Metallurgy',
    'D': 'Textiles; Paper',
    'E': 'Fixed Constructions',
    'F': 'Mechanical Engineering; Lighting; Heating; Weapons; Blasting',
    'G': 'Physics',
    'H': 'Electricity'
}


@dataclass
class PatentSearchOptions:
    """Configuration options for patent searching."""
    query: Optional[str] = None
    keywords: Optional[List[str]] = None
    inventors: Optional[List[str]] = None
    assignees: Optional[List[str]] = None
    patent_numbers: Optional[List[str]] = None
    
    # Classification codes
    cpc_codes: Optional[List[str]] = None
    ipc_codes: Optional[List[str]] = None
    uspc_codes: Optional[List[str]] = None
    
    # Date filtering
    start_date: Optional[str] = None  # YYYY-MM-DD format
    end_date: Optional[str] = None    # YYYY-MM-DD format
    date_type: str = 'publication'    # publication, filing, priority
    
    # Patent type and status
    patent_type: Optional[str] = None  # utility, design, plant, reissue
    status: Optional[str] = None       # active, expired, pending, abandoned
    
    # Geographic filtering
    country_codes: Optional[List[str]] = None  # US, EP, WO, etc.
    
    # Result limits
    max_results: int = 100
    start_index: int = 0
    
    # Sorting
    sort_by: str = 'relevance'  # relevance, date, patent_number
    sort_order: str = 'descending'  # ascending, descending
    
    # Content options
    include_full_text: bool = False
    include_claims: bool = False
    include_citations: bool = False
    include_family: bool = False
    
    # Output options
    output_format: str = 'json'
    output_file: Optional[str] = None
    verbose: bool = False


@dataclass
class Patent:
    """Represents a patent with all metadata and content."""
    patent_number: str
    title: str
    abstract: str
    inventors: List[str]
    assignees: List[str]
    
    # Dates
    filing_date: str
    publication_date: str
    grant_date: Optional[str] = None
    priority_date: Optional[str] = None
    
    # Classification
    cpc_codes: List[str] = None
    ipc_codes: List[str] = None
    uspc_codes: List[str] = None
    
    # Legal information
    status: str = ""
    country_code: str = ""
    patent_type: str = ""
    
    # Content
    claims: Optional[List[str]] = None
    description: Optional[str] = None
    full_text: Optional[str] = None
    
    # Citations and family
    cited_patents: Optional[List[str]] = None
    citing_patents: Optional[List[str]] = None
    patent_family: Optional[List[str]] = None
    
    # URLs and identifiers
    patent_url: str = ""
    pdf_url: str = ""
    
    # Metadata
    scraped_at: Optional[str] = None
    scraping_success: bool = True
    scraping_errors: Optional[List[str]] = None
    source: str = ""  # uspto, google_patents, epo, etc.

    def __post_init__(self):
        if self.cpc_codes is None:
            self.cpc_codes = []
        if self.ipc_codes is None:
            self.ipc_codes = []
        if self.uspc_codes is None:
            self.uspc_codes = []


class PatentScraper(BaseScraper):
    """Comprehensive patent scraper supporting multiple patent databases."""
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize the patent scraper."""
        super().__init__(config)
        
        # Setup rate limiters for different sources
        self.uspto_rate_limiter = rate_limit(USPTO_RATE_LIMIT)
        self.google_rate_limiter = rate_limit(GOOGLE_PATENTS_RATE_LIMIT)
        
        # Patent number patterns
        self.patent_patterns = {
            'us_utility': re.compile(r'US\s*(\d{1,2}[,.]?\d{3}[,.]?\d{3})\s*[AB]?\d?'),
            'us_application': re.compile(r'US\s*(\d{2}/\d{3}[,.]?\d{3})'),
            'us_provisional': re.compile(r'US\s*(\d{2}/\d{3}[,.]?\d{3})'),
            'ep_patent': re.compile(r'EP\s*(\d{7})\s*[AB]\d?'),
            'wo_patent': re.compile(r'WO\s*(\d{4}/\d{6})\s*[AB]\d?'),
            'generic': re.compile(r'([A-Z]{2}\s*\d+)')
        }
        
        logger.info("Initialized Patent scraper with USPTO and Google Patents support")
    
    def scrape(self, search_options: PatentSearchOptions) -> List[Patent]:
        """
        Main scraping method that searches patents based on options.
        
        Args:
            search_options: Patent search configuration
            
        Returns:
            List of Patent objects matching the search criteria
        """
        logger.info(f"Starting patent search with options: {search_options}")
        start_time = time.time()
        
        patents = []
        
        # Try USPTO first, then Google Patents as fallback
        try:
            uspto_patents = self._search_uspto(search_options)
            patents.extend(uspto_patents)
            logger.info(f"Found {len(uspto_patents)} patents from USPTO")
        except Exception as e:
            logger.warning(f"USPTO search failed: {e}")
        
        # If we need more results or USPTO failed, try Google Patents
        if len(patents) < search_options.max_results:
            try:
                remaining_results = search_options.max_results - len(patents)
                google_options = PatentSearchOptions(**asdict(search_options))
                google_options.max_results = remaining_results
                
                google_patents = self._search_google_patents(google_options)
                patents.extend(google_patents)
                logger.info(f"Found {len(google_patents)} additional patents from Google Patents")
            except Exception as e:
                logger.warning(f"Google Patents search failed: {e}")
        
        # Enhance patents with additional content if requested
        if search_options.include_full_text or search_options.include_claims or search_options.include_citations:
            patents = self._enhance_patents_with_content(patents, search_options)
        
        # Remove duplicates based on patent number
        patents = self._deduplicate_patents(patents)
        
        # Limit to requested number
        patents = patents[:search_options.max_results]
        
        end_time = time.time()
        logger.info(f"Patent search completed in {end_time - start_time:.2f}s. Found {len(patents)} unique patents.")
        
        return patents
    
    @retry_on_failure(max_retries=3, delay=1.0)
    def _search_uspto(self, options: PatentSearchOptions) -> List[Patent]:
        """Search patents using USPTO Patent API."""
        logger.info("Searching USPTO Patent database")
        
        # Build USPTO search query
        query_params = self._build_uspto_query(options)
        
        # Make request to USPTO API
        response = self._make_uspto_request('/patents/query', params=query_params)
        
        # Parse response
        patents = self._parse_uspto_response(response.json())
        
        return patents
    
    @retry_on_failure(max_retries=3, delay=1.0)
    def _search_google_patents(self, options: PatentSearchOptions) -> List[Patent]:
        """Search patents using Google Patents."""
        logger.info("Searching Google Patents database")
        
        # Build Google Patents search query
        search_query = self._build_google_patents_query(options)
        
        # Make request to Google Patents
        patents = []
        
        # Google Patents uses a different approach - we'll scrape the search results page
        search_url = f"{GOOGLE_PATENTS_BASE_URL}/xhr/query"
        
        params = {
            'url': f'q={quote(search_query)}&num={options.max_results}',
            'exp': ''
        }
        
        response = self._make_google_patents_request(search_url, params=params)
        
        # Parse Google Patents response
        patents = self._parse_google_patents_response(response.text, options)
        
        return patents
    
    def _build_uspto_query(self, options: PatentSearchOptions) -> Dict[str, Any]:
        """Build USPTO API query parameters."""
        params = {
            'searchText': '',
            'start': options.start_index,
            'rows': min(options.max_results, 100),  # USPTO API limit
            'sort': 'date desc' if options.sort_by == 'date' else 'score desc'
        }
        
        # Build search text
        search_parts = []
        
        if options.query:
            search_parts.append(f'({options.query})')
        
        if options.keywords:
            keyword_query = ' AND '.join([f'"{kw}"' for kw in options.keywords])
            search_parts.append(f'({keyword_query})')
        
        if options.inventors:
            inventor_query = ' OR '.join([f'inventor:"{inv}"' for inv in options.inventors])
            search_parts.append(f'({inventor_query})')
        
        if options.assignees:
            assignee_query = ' OR '.join([f'assignee:"{ass}"' for ass in options.assignees])
            search_parts.append(f'({assignee_query})')
        
        if options.cpc_codes:
            cpc_query = ' OR '.join([f'cpc:"{code}"' for code in options.cpc_codes])
            search_parts.append(f'({cpc_query})')
        
        if options.patent_numbers:
            number_query = ' OR '.join([f'patentNumber:"{num}"' for num in options.patent_numbers])
            search_parts.append(f'({number_query})')
        
        # Combine search parts
        if search_parts:
            params['searchText'] = ' AND '.join(search_parts)
        else:
            params['searchText'] = '*:*'  # Default to all patents
        
        # Add date filtering
        if options.start_date or options.end_date:
            date_field = 'publicationDate' if options.date_type == 'publication' else 'filingDate'
            start = options.start_date or '1790-01-01'
            end = options.end_date or datetime.now().strftime('%Y-%m-%d')
            params['fq'] = f'{date_field}:[{start}T00:00:00Z TO {end}T23:59:59Z]'
        
        return params
    
    def _build_google_patents_query(self, options: PatentSearchOptions) -> str:
        """Build Google Patents search query string."""
        query_parts = []
        
        if options.query:
            query_parts.append(options.query)
        
        if options.keywords:
            query_parts.extend(options.keywords)
        
        if options.inventors:
            for inventor in options.inventors:
                query_parts.append(f'inventor:"{inventor}"')
        
        if options.assignees:
            for assignee in options.assignees:
                query_parts.append(f'assignee:"{assignee}"')
        
        if options.cpc_codes:
            for code in options.cpc_codes:
                query_parts.append(f'cpc:{code}')
        
        if options.patent_numbers:
            for number in options.patent_numbers:
                query_parts.append(f'patent:{number}')
        
        # Add date filtering
        if options.start_date and options.end_date:
            query_parts.append(f'after:{options.start_date} before:{options.end_date}')
        elif options.start_date:
            query_parts.append(f'after:{options.start_date}')
        elif options.end_date:
            query_parts.append(f'before:{options.end_date}')
        
        return ' '.join(query_parts) if query_parts else 'patent'
    
    @uspto_rate_limiter
    def _make_uspto_request(self, endpoint: str, params: Optional[Dict] = None) -> requests.Response:
        """Make rate-limited request to USPTO API."""
        url = f"{USPTO_PATENT_API_URL}{endpoint}"
        logger.debug(f"Making USPTO request to: {url}")
        
        response = self.session.get(url, params=params, timeout=self.config.REQUEST_TIMEOUT)
        response.raise_for_status()
        
        return response
    
    @google_rate_limiter
    def _make_google_patents_request(self, url: str, params: Optional[Dict] = None) -> requests.Response:
        """Make rate-limited request to Google Patents."""
        logger.debug(f"Making Google Patents request to: {url}")
        
        headers = {
            'User-Agent': self.config.USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://patents.google.com/'
        }
        
        response = self.session.get(url, params=params, headers=headers, timeout=self.config.REQUEST_TIMEOUT)
        response.raise_for_status()
        
        return response
    
    def _parse_uspto_response(self, data: Dict[str, Any]) -> List[Patent]:
        """Parse USPTO API response."""
        patents = []
        
        if 'response' not in data or 'docs' not in data['response']:
            logger.warning("Invalid USPTO API response format")
            return patents
        
        for doc in data['response']['docs']:
            try:
                patent = self._parse_uspto_patent(doc)
                if patent:
                    patents.append(patent)
            except Exception as e:
                logger.warning(f"Failed to parse USPTO patent: {e}")
                continue
        
        return patents
    
    def _parse_uspto_patent(self, doc: Dict[str, Any]) -> Optional[Patent]:
        """Parse a single USPTO patent document."""
        try:
            # Extract basic information
            patent_number = doc.get('patentNumber', '')
            title = clean_text(doc.get('patentTitle', ''))
            abstract = clean_text(doc.get('abstractText', ''))
            
            # Extract inventors
            inventors = []
            if 'inventorName' in doc:
                if isinstance(doc['inventorName'], list):
                    inventors = [clean_text(name) for name in doc['inventorName']]
                else:
                    inventors = [clean_text(doc['inventorName'])]
            
            # Extract assignees
            assignees = []
            if 'assigneeName' in doc:
                if isinstance(doc['assigneeName'], list):
                    assignees = [clean_text(name) for name in doc['assigneeName']]
                else:
                    assignees = [clean_text(doc['assigneeName'])]
            
            # Extract dates
            filing_date = doc.get('filingDate', '')
            publication_date = doc.get('publicationDate', '')
            grant_date = doc.get('grantDate', '')
            
            # Extract classification codes
            cpc_codes = []
            if 'cpcInventiveClassificationText' in doc:
                if isinstance(doc['cpcInventiveClassificationText'], list):
                    cpc_codes = doc['cpcInventiveClassificationText']
                else:
                    cpc_codes = [doc['cpcInventiveClassificationText']]
            
            ipc_codes = []
            if 'ipcClassificationText' in doc:
                if isinstance(doc['ipcClassificationText'], list):
                    ipc_codes = doc['ipcClassificationText']
                else:
                    ipc_codes = [doc['ipcClassificationText']]
            
            # Build URLs
            patent_url = f"https://patents.uspto.gov/patent/{patent_number}"
            pdf_url = f"https://patents.uspto.gov/patent/{patent_number}/download"
            
            # Create patent object
            patent = Patent(
                patent_number=patent_number,
                title=title,
                abstract=abstract,
                inventors=inventors,
                assignees=assignees,
                filing_date=filing_date,
                publication_date=publication_date,
                grant_date=grant_date,
                cpc_codes=cpc_codes,
                ipc_codes=ipc_codes,
                status=doc.get('patentStatus', ''),
                country_code='US',
                patent_type=doc.get('patentType', 'utility'),
                patent_url=patent_url,
                pdf_url=pdf_url,
                scraped_at=datetime.now().isoformat(),
                source='uspto'
            )
            
            return patent
            
        except Exception as e:
            logger.warning(f"Error parsing USPTO patent: {e}")
            return None
    
    def _parse_google_patents_response(self, html_content: str, options: PatentSearchOptions) -> List[Patent]:
        """Parse Google Patents search results."""
        patents = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find patent result containers
            patent_elements = soup.find_all('article', class_='result')
            
            for element in patent_elements:
                try:
                    patent = self._parse_google_patent_element(element)
                    if patent:
                        patents.append(patent)
                except Exception as e:
                    logger.warning(f"Failed to parse Google Patents result: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Failed to parse Google Patents HTML: {e}")
        
        return patents
    
    def _parse_google_patent_element(self, element) -> Optional[Patent]:
        """Parse a single Google Patents search result element."""
        try:
            # Extract patent number and title
            title_link = element.find('h3').find('a') if element.find('h3') else None
            if not title_link:
                return None
            
            title = clean_text(title_link.get_text())
            patent_url = urljoin(GOOGLE_PATENTS_BASE_URL, title_link.get('href', ''))
            
            # Extract patent number from URL or text
            patent_number = ''
            href = title_link.get('href', '')
            if '/patent/' in href:
                patent_number = href.split('/patent/')[-1].split('/')[0]
            
            # Extract metadata
            metadata_div = element.find('div', class_='metadata')
            inventors = []
            assignees = []
            filing_date = ''
            publication_date = ''
            
            if metadata_div:
                # Parse metadata text for inventors, assignees, dates
                metadata_text = metadata_div.get_text()
                
                # Extract inventors (usually after "Inventor:")
                inventor_match = re.search(r'Inventor[s]?:\s*([^•\n]+)', metadata_text)
                if inventor_match:
                    inventors = [clean_text(inv.strip()) for inv in inventor_match.group(1).split(',')]
                
                # Extract assignees (usually after "Assignee:")
                assignee_match = re.search(r'Assignee[s]?:\s*([^•\n]+)', metadata_text)
                if assignee_match:
                    assignees = [clean_text(ass.strip()) for ass in assignee_match.group(1).split(',')]
                
                # Extract dates
                date_matches = re.findall(r'(\d{4}-\d{2}-\d{2})', metadata_text)
                if date_matches:
                    publication_date = date_matches[0]
                    if len(date_matches) > 1:
                        filing_date = date_matches[1]
            
            # Extract abstract/snippet
            abstract_div = element.find('div', class_='snippet')
            abstract = clean_text(abstract_div.get_text()) if abstract_div else ''
            
            # Create patent object
            patent = Patent(
                patent_number=patent_number,
                title=title,
                abstract=abstract,
                inventors=inventors,
                assignees=assignees,
                filing_date=filing_date,
                publication_date=publication_date,
                patent_url=patent_url,
                scraped_at=datetime.now().isoformat(),
                source='google_patents'
            )
            
            return patent
            
        except Exception as e:
            logger.warning(f"Error parsing Google Patents element: {e}")
            return None
    
    def _enhance_patents_with_content(self, patents: List[Patent], options: PatentSearchOptions) -> List[Patent]:
        """Enhance patents with additional content like full text, claims, citations."""
        logger.info(f"Enhancing {len(patents)} patents with additional content...")
        
        enhanced_patents = []
        
        for i, patent in enumerate(patents):
            logger.info(f"Processing patent {i+1}/{len(patents)}: {patent.patent_number}")
            
            try:
                # Get full patent details
                if options.include_full_text or options.include_claims or options.include_citations:
                    enhanced_patent = self._get_patent_details(patent, options)
                    enhanced_patents.append(enhanced_patent)
                else:
                    enhanced_patents.append(patent)
                
            except Exception as e:
                logger.warning(f"Failed to enhance patent {patent.patent_number}: {e}")
                patent.scraping_success = False
                if patent.scraping_errors is None:
                    patent.scraping_errors = []
                patent.scraping_errors.append(str(e))
                enhanced_patents.append(patent)
        
        return enhanced_patents
    
    def _get_patent_details(self, patent: Patent, options: PatentSearchOptions) -> Patent:
        """Get detailed patent information from the patent page."""
        if not patent.patent_url:
            return patent
        
        try:
            # Determine which scraper to use based on source
            if patent.source == 'uspto' or 'uspto.gov' in patent.patent_url:
                return self._get_uspto_patent_details(patent, options)
            elif patent.source == 'google_patents' or 'patents.google.com' in patent.patent_url:
                return self._get_google_patent_details(patent, options)
            else:
                return patent
                
        except Exception as e:
            logger.warning(f"Failed to get patent details for {patent.patent_number}: {e}")
            return patent
    
    def _get_uspto_patent_details(self, patent: Patent, options: PatentSearchOptions) -> Patent:
        """Get detailed information from USPTO patent page."""
        response = self._make_uspto_request(f'/patents/{patent.patent_number}')
        data = response.json()
        
        # Extract additional details from USPTO API response
        if 'patentData' in data:
            patent_data = data['patentData']
            
            if options.include_claims and 'claims' in patent_data:
                patent.claims = [clean_text(claim) for claim in patent_data['claims']]
            
            if options.include_full_text and 'description' in patent_data:
                patent.description = clean_text(patent_data['description'])
                patent.full_text = f"{patent.abstract}\n\n{patent.description}"
                if patent.claims:
                    patent.full_text += "\n\nCLAIMS:\n" + "\n".join(patent.claims)
            
            if options.include_citations:
                if 'citedPatents' in patent_data:
                    patent.cited_patents = patent_data['citedPatents']
                if 'citingPatents' in patent_data:
                    patent.citing_patents = patent_data['citingPatents']
        
        return patent
    
    def _get_google_patent_details(self, patent: Patent, options: PatentSearchOptions) -> Patent:
        """Get detailed information from Google Patents page."""
        response = self._make_google_patents_request(patent.patent_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract claims
        if options.include_claims:
            claims_section = soup.find('section', {'data-section-id': 'claims'})
            if claims_section:
                claim_divs = claims_section.find_all('div', class_='claim-text')
                patent.claims = [clean_text(div.get_text()) for div in claim_divs]
        
        # Extract description/full text
        if options.include_full_text:
            description_section = soup.find('section', {'data-section-id': 'description'})
            if description_section:
                patent.description = clean_text(description_section.get_text())
                patent.full_text = f"{patent.abstract}\n\n{patent.description}"
                if patent.claims:
                    patent.full_text += "\n\nCLAIMS:\n" + "\n".join(patent.claims)
        
        # Extract citations
        if options.include_citations:
            # Find cited patents
            cited_section = soup.find('section', {'data-section-id': 'citations'})
            if cited_section:
                cited_links = cited_section.find_all('a', href=re.compile(r'/patent/'))
                patent.cited_patents = []
                for link in cited_links:
                    href = link.get('href', '')
                    if '/patent/' in href:
                        patent_num = href.split('/patent/')[-1].split('/')[0]
                        patent.cited_patents.append(patent_num)
        
        return patent
    
    def _deduplicate_patents(self, patents: List[Patent]) -> List[Patent]:
        """Remove duplicate patents based on patent number."""
        seen_numbers = set()
        unique_patents = []
        
        for patent in patents:
            # Normalize patent number for comparison
            normalized_number = re.sub(r'[^\w]', '', patent.patent_number.upper())
            
            if normalized_number not in seen_numbers:
                seen_numbers.add(normalized_number)
                unique_patents.append(patent)
            else:
                logger.debug(f"Skipping duplicate patent: {patent.patent_number}")
        
        logger.info(f"Removed {len(patents) - len(unique_patents)} duplicate patents")
        return unique_patents
    
    def get_patent_by_number(self, patent_number: str, include_content: bool = False) -> Optional[Patent]:
        """
        Get a specific patent by its number.
        
        Args:
            patent_number: Patent number (e.g., 'US10123456B2', '10123456')
            include_content: Whether to include full text, claims, and citations
            
        Returns:
            Patent object or None if not found
        """
        logger.info(f"Fetching patent by number: {patent_number}")
        
        # Normalize patent number
        normalized_number = self._normalize_patent_number(patent_number)
        
        # Create search options for specific patent
        options = PatentSearchOptions(
            patent_numbers=[normalized_number],
            max_results=1,
            include_full_text=include_content,
            include_claims=include_content,
            include_citations=include_content
        )
        
        patents = self.scrape(options)
        return patents[0] if patents else None
    
    def batch_get_patents(self, patent_numbers: List[str], 
                         include_content: bool = False,
                         max_workers: int = 3) -> List[Patent]:
        """
        Get multiple patents in batch with concurrent processing.
        
        Args:
            patent_numbers: List of patent numbers
            include_content: Whether to include full text, claims, and citations
            max_workers: Maximum number of concurrent workers
            
        Returns:
            List of Patent objects
        """
        logger.info(f"Starting batch retrieval of {len(patent_numbers)} patents")
        
        patents = []
        
        # Use ThreadPoolExecutor for concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_number = {
                executor.submit(self.get_patent_by_number, number, include_content): number
                for number in patent_numbers
            }
            
            # Collect results
            for future in concurrent.futures.as_completed(future_to_number):
                patent_number = future_to_number[future]
                try:
                    patent = future.result()
                    if patent:
                        patents.append(patent)
                        logger.info(f"✓ Retrieved patent: {patent_number}")
                    else:
                        logger.warning(f"✗ Patent not found: {patent_number}")
                except Exception as e:
                    logger.error(f"✗ Failed to retrieve patent {patent_number}: {e}")
        
        logger.info(f"Batch retrieval completed. Successfully retrieved {len(patents)} patents.")
        return patents
    
    def search_by_inventor(self, inventor_name: str, max_results: int = 100) -> List[Patent]:
        """
        Search patents by inventor name.
        
        Args:
            inventor_name: Name of the inventor
            max_results: Maximum number of results
            
        Returns:
            List of Patent objects
        """
        options = PatentSearchOptions(
            inventors=[inventor_name],
            max_results=max_results,
            sort_by='date'
        )
        
        return self.scrape(options)
    
    def search_by_assignee(self, assignee_name: str, max_results: int = 100) -> List[Patent]:
        """
        Search patents by assignee/company name.
        
        Args:
            assignee_name: Name of the assignee/company
            max_results: Maximum number of results
            
        Returns:
            List of Patent objects
        """
        options = PatentSearchOptions(
            assignees=[assignee_name],
            max_results=max_results,
            sort_by='date'
        )
        
        return self.scrape(options)
    
    def search_by_cpc_code(self, cpc_code: str, max_results: int = 100) -> List[Patent]:
        """
        Search patents by CPC (Cooperative Patent Classification) code.
        
        Args:
            cpc_code: CPC classification code (e.g., 'G06F', 'H04L29/06')
            max_results: Maximum number of results
            
        Returns:
            List of Patent objects
        """
        options = PatentSearchOptions(
            cpc_codes=[cpc_code],
            max_results=max_results,
            sort_by='date'
        )
        
        return self.scrape(options)
    
    def search_recent_patents(self, days: int = 30, keywords: Optional[List[str]] = None,
                            max_results: int = 100) -> List[Patent]:
        """
        Search for patents published in the last N days.
        
        Args:
            days: Number of days to look back
            keywords: Optional keywords to filter by
            max_results: Maximum number of results
            
        Returns:
            List of Patent objects
        """
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        
        options = PatentSearchOptions(
            keywords=keywords,
            start_date=start_date,
            end_date=end_date,
            max_results=max_results,
            sort_by='date',
            sort_order='descending'
        )
        
        return self.scrape(options)
    
    def _normalize_patent_number(self, patent_number: str) -> str:
        """Normalize patent number to standard format."""
        # Remove common prefixes and suffixes
        normalized = re.sub(r'^(US|EP|WO|CN|JP|KR|DE|FR|GB)', '', patent_number.upper())
        normalized = re.sub(r'[^\d]', '', normalized)  # Keep only digits
        
        # Add US prefix if it looks like a US patent
        if len(normalized) >= 7 and len(normalized) <= 8:
            return f"US{normalized}"
        
        return patent_number
    
    def save_patents(self, patents: List[Patent], output_file: Path, format: str = 'json') -> None:
        """Save patents to file in specified format."""
        if format == 'json':
            data = {
                'scraped_at': datetime.now().isoformat(),
                'total_patents': len(patents),
                'patents': [asdict(patent) for patent in patents]
            }
            save_to_json(data, output_file)
        
        elif format == 'csv':
            import csv
            
            # Flatten patent data for CSV
            flattened_patents = []
            for patent in patents:
                patent_dict = asdict(patent)
                # Convert lists to comma-separated strings
                patent_dict['inventors'] = ', '.join(patent_dict['inventors'])
                patent_dict['assignees'] = ', '.join(patent_dict['assignees'])
                patent_dict['cpc_codes'] = ', '.join(patent_dict['cpc_codes'] or [])
                patent_dict['ipc_codes'] = ', '.join(patent_dict['ipc_codes'] or [])
                if patent_dict['claims']:
                    patent_dict['claims'] = ' | '.join(patent_dict['claims'][:5])  # Limit for CSV
                if patent_dict['cited_patents']:
                    patent_dict['cited_patents'] = ', '.join(patent_dict['cited_patents'][:10])
                # Remove very long text fields
                patent_dict.pop('full_text', None)
                patent_dict.pop('description', None)
                flattened_patents.append(patent_dict)
            
            # Write CSV
            if flattened_patents:
                with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = flattened_patents[0].keys()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(flattened_patents)
        
        elif format == 'xml':
            # Create XML structure
            root = ET.Element('patents')
            root.set('scraped_at', datetime.now().isoformat())
            root.set('total_patents', str(len(patents)))
            
            for patent in patents:
                patent_elem = ET.SubElement(root, 'patent')
                patent_dict = asdict(patent)
                
                for key, value in patent_dict.items():
                    if isinstance(value, list) and value:
                        list_elem = ET.SubElement(patent_elem, key)
                        for item in value:
                            item_elem = ET.SubElement(list_elem, 'item')
                            item_elem.text = str(item)
                    elif value is not None:
                        elem = ET.SubElement(patent_elem, key)
                        elem.text = str(value)
            
            # Write XML to file
            tree = ET.ElementTree(root)
            ET.indent(tree, space="  ", level=0)
            tree.write(output_file, encoding='utf-8', xml_declaration=True)
        
        logger.info(f"Saved {len(patents)} patents to {output_file}")


def print_patent_summary(patent: Patent) -> None:
    """Print a formatted summary of a patent."""
    print(f"\n{'='*80}")
    print(f"Patent Number: {patent.patent_number}")
    print(f"Title: {patent.title}")
    print(f"Inventors: {', '.join(patent.inventors)}")
    print(f"Assignees: {', '.join(patent.assignees)}")
    print(f"Filing Date: {patent.filing_date}")
    print(f"Publication Date: {patent.publication_date}")
    
    if patent.grant_date:
        print(f"Grant Date: {patent.grant_date}")
    
    if patent.cpc_codes:
        print(f"CPC Codes: {', '.join(patent.cpc_codes[:5])}")
    
    if patent.status:
        print(f"Status: {patent.status}")
    
    print(f"\nAbstract:")
    print(patent.abstract[:500] + "..." if len(patent.abstract) > 500 else patent.abstract)
    
    if patent.claims:
        print(f"\nClaims: {len(patent.claims)} total")
        if patent.claims:
            print(f"Claim 1: {patent.claims[0][:200]}...")
    
    if patent.cited_patents:
        print(f"\nCited Patents: {len(patent.cited_patents)} total")
    
    print(f"\nPatent URL: {patent.patent_url}")
    print(f"Source: {patent.source}")


def print_search_summary(patents: List[Patent], options: PatentSearchOptions) -> None:
    """Print a summary of patent search results."""
    print(f"\n{'='*80}")
    print(f"PATENT SEARCH SUMMARY")
    print(f"{'='*80}")
    print(f"Total patents found: {len(patents)}")
    
    if options.query:
        print(f"Query: {options.query}")
    if options.keywords:
        print(f"Keywords: {', '.join(options.keywords)}")
    if options.inventors:
        print(f"Inventors: {', '.join(options.inventors)}")
    if options.assignees:
        print(f"Assignees: {', '.join(options.assignees)}")
    if options.cpc_codes:
        print(f"CPC Codes: {', '.join(options.cpc_codes)}")
    
    # Source breakdown
    if patents:
        source_counts = {}
        for patent in patents:
            source_counts[patent.source] = source_counts.get(patent.source, 0) + 1
        
        print(f"\nSources:")
        for source, count in source_counts.items():
            print(f"  {source}: {count}")
        
        # Assignee breakdown
        assignee_counts = {}
        for patent in patents:
            for assignee in patent.assignees:
                assignee_counts[assignee] = assignee_counts.get(assignee, 0) + 1
        
        if assignee_counts:
            print(f"\nTop assignees:")
            sorted_assignees = sorted(assignee_counts.items(), key=lambda x: x[1], reverse=True)
            for assignee, count in sorted_assignees[:10]:
                print(f"  {assignee}: {count}")
        
        # Year breakdown
        year_counts = {}
        for patent in patents:
            try:
                year = patent.publication_date[:4] if patent.publication_date else 'Unknown'
                year_counts[year] = year_counts.get(year, 0) + 1
            except:
                pass
        
        if year_counts:
            print(f"\nPatents by year:")
            sorted_years = sorted(year_counts.items(), reverse=True)
            for year, count in sorted_years[:10]:
                print(f"  {year}: {count}")
    
    print(f"{'='*80}")


# Example usage and CLI interface would go here
if __name__ == "__main__":
    # Example usage
    scraper = PatentScraper()
    
    # Search for patents related to machine learning
    options = PatentSearchOptions(
        keywords=["machine learning", "artificial intelligence"],
        max_results=10,
        include_full_text=True,
        include_claims=True
    )
    
    patents = scraper.scrape(options)
    
    for patent in patents:
        print_patent_summary(patent)
    
    print_search_summary(patents, options)