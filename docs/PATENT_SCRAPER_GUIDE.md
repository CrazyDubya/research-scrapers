# Patent Scraper Guide

A comprehensive guide to using the Patent Database scraper for research and patent analysis.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Quick Start](#quick-start)
- [Patent Search Options](#patent-search-options)
- [Search Methods](#search-methods)
- [Patent Data Structure](#patent-data-structure)
- [Advanced Usage](#advanced-usage)
- [Output Formats](#output-formats)
- [Rate Limiting](#rate-limiting)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Best Practices](#best-practices)
- [API References](#api-references)

## Overview

The Patent Scraper provides unified access to multiple patent databases including:

- **USPTO Patent API**: Official US Patent and Trademark Office API
- **Google Patents**: Comprehensive patent search and analysis
- **EPO (European Patent Office)**: European patent data
- **WIPO**: World Intellectual Property Organization patents

The scraper follows the established patterns of the research-scrapers package with comprehensive error handling, rate limiting, and multiple output formats.

## Features

### Core Capabilities
- ✅ **Multi-source patent search**: USPTO, Google Patents, EPO, WIPO
- ✅ **Advanced filtering**: Keywords, inventors, assignees, CPC codes
- ✅ **Date range filtering**: Publication, filing, priority dates
- ✅ **Patent classification**: CPC, IPC, USPC code support
- ✅ **Full-text extraction**: Patent descriptions, claims, abstracts
- ✅ **Citation analysis**: Cited and citing patents
- ✅ **Batch operations**: Concurrent processing of multiple patents
- ✅ **Multiple output formats**: JSON, CSV, XML
- ✅ **Rate limiting**: Compliant with USPTO guidelines (120 req/min)
- ✅ **Comprehensive error handling**: Retry logic with exponential backoff

### Patent Content
- Patent metadata (number, title, abstract, inventors, assignees)
- Legal information (status, filing/publication dates, country codes)
- Classification codes (CPC, IPC, USPC)
- Full patent text and claims
- Citation networks (forward and backward citations)
- Patent family information
- Legal status tracking

## Quick Start

### Basic Installation

```python
from research_scrapers import PatentScraper, PatentSearchOptions

# Initialize the scraper
scraper = PatentScraper()

# Simple keyword search
options = PatentSearchOptions(
    keywords=["machine learning", "artificial intelligence"],
    max_results=50
)

patents = scraper.scrape(options)

# Print results
for patent in patents:
    print(f"{patent.patent_number}: {patent.title}")
```

### Get Specific Patent

```python
# Get a specific patent by number
patent = scraper.get_patent_by_number("US10123456B2", include_content=True)

if patent:
    print(f"Title: {patent.title}")
    print(f"Inventors: {', '.join(patent.inventors)}")
    print(f"Abstract: {patent.abstract}")
    
    if patent.claims:
        print(f"Number of claims: {len(patent.claims)}")
```

### Search by Inventor

```python
# Find all patents by a specific inventor
patents = scraper.search_by_inventor("John Smith", max_results=100)
print(f"Found {len(patents)} patents by John Smith")
```

## Patent Search Options

The `PatentSearchOptions` class provides comprehensive search configuration:

```python
@dataclass
class PatentSearchOptions:
    # Search terms
    query: Optional[str] = None                    # General search query
    keywords: Optional[List[str]] = None           # Specific keywords
    inventors: Optional[List[str]] = None          # Inventor names
    assignees: Optional[List[str]] = None          # Company/assignee names
    patent_numbers: Optional[List[str]] = None     # Specific patent numbers
    
    # Classification codes
    cpc_codes: Optional[List[str]] = None          # CPC classification codes
    ipc_codes: Optional[List[str]] = None          # IPC classification codes
    uspc_codes: Optional[List[str]] = None         # US classification codes
    
    # Date filtering
    start_date: Optional[str] = None               # Start date (YYYY-MM-DD)
    end_date: Optional[str] = None                 # End date (YYYY-MM-DD)
    date_type: str = 'publication'                 # publication, filing, priority
    
    # Patent characteristics
    patent_type: Optional[str] = None              # utility, design, plant, reissue
    status: Optional[str] = None                   # active, expired, pending, abandoned
    country_codes: Optional[List[str]] = None      # US, EP, WO, etc.
    
    # Result configuration
    max_results: int = 100                         # Maximum results to return
    start_index: int = 0                           # Starting index for pagination
    sort_by: str = 'relevance'                     # relevance, date, patent_number
    sort_order: str = 'descending'                 # ascending, descending
    
    # Content options
    include_full_text: bool = False                # Extract full patent text
    include_claims: bool = False                   # Extract patent claims
    include_citations: bool = False                # Extract citation data
    include_family: bool = False                   # Extract patent family info
    
    # Output options
    output_format: str = 'json'                    # json, csv, xml
    output_file: Optional[str] = None              # Output file path
    verbose: bool = False                          # Verbose logging
```

## Search Methods

### 1. General Search

```python
options = PatentSearchOptions(
    query="quantum computing AND machine learning",
    max_results=100,
    sort_by='date',
    sort_order='descending'
)
patents = scraper.scrape(options)
```

### 2. Keyword Search

```python
options = PatentSearchOptions(
    keywords=["blockchain", "cryptocurrency", "distributed ledger"],
    max_results=50
)
patents = scraper.scrape(options)
```

### 3. Inventor Search

```python
# Single inventor
patents = scraper.search_by_inventor("Geoffrey Hinton", max_results=50)

# Multiple inventors
options = PatentSearchOptions(
    inventors=["Geoffrey Hinton", "Yann LeCun", "Yoshua Bengio"],
    max_results=100
)
patents = scraper.scrape(options)
```

### 4. Assignee/Company Search

```python
# Single company
patents = scraper.search_by_assignee("Google LLC", max_results=100)

# Multiple companies
options = PatentSearchOptions(
    assignees=["Google LLC", "Microsoft Corporation", "Apple Inc."],
    max_results=200
)
patents = scraper.scrape(options)
```

### 5. Classification Code Search

```python
# Search by CPC code
patents = scraper.search_by_cpc_code("G06N", max_results=100)

# Multiple classification systems
options = PatentSearchOptions(
    cpc_codes=["G06N", "G06F"],  # AI and computing
    ipc_codes=["G06F15/18"],     # Learning machines
    max_results=150
)
patents = scraper.scrape(options)
```

### 6. Date Range Search

```python
options = PatentSearchOptions(
    keywords=["artificial intelligence"],
    start_date="2020-01-01",
    end_date="2023-12-31",
    date_type="publication",
    max_results=200
)
patents = scraper.scrape(options)
```

### 7. Recent Patents

```python
# Patents from last 30 days
patents = scraper.search_recent_patents(
    days=30,
    keywords=["quantum computing"],
    max_results=50
)
```

### 8. Advanced Multi-criteria Search

```python
options = PatentSearchOptions(
    keywords=["machine learning"],
    assignees=["IBM", "Google"],
    cpc_codes=["G06N"],
    start_date="2022-01-01",
    country_codes=["US"],
    patent_type="utility",
    max_results=100,
    include_full_text=True,
    include_claims=True,
    include_citations=True
)
patents = scraper.scrape(options)
```

## Patent Data Structure

Each patent is represented by a `Patent` dataclass:

```python
@dataclass
class Patent:
    # Basic information
    patent_number: str                    # Patent number (e.g., "US10123456B2")
    title: str                           # Patent title
    abstract: str                        # Patent abstract
    inventors: List[str]                 # List of inventor names
    assignees: List[str]                 # List of assignee names
    
    # Important dates
    filing_date: str                     # Filing date (YYYY-MM-DD)
    publication_date: str                # Publication date
    grant_date: Optional[str]            # Grant date (if granted)
    priority_date: Optional[str]         # Priority date
    
    # Classification codes
    cpc_codes: List[str]                 # CPC classification codes
    ipc_codes: List[str]                 # IPC classification codes
    uspc_codes: List[str]                # US classification codes
    
    # Legal information
    status: str                          # Patent status
    country_code: str                    # Country code (US, EP, etc.)
    patent_type: str                     # Patent type (utility, design, etc.)
    
    # Content (optional)
    claims: Optional[List[str]]          # Patent claims
    description: Optional[str]           # Patent description
    full_text: Optional[str]             # Complete patent text
    
    # Citations and relationships
    cited_patents: Optional[List[str]]   # Patents cited by this patent
    citing_patents: Optional[List[str]]  # Patents citing this patent
    patent_family: Optional[List[str]]   # Patent family members
    
    # URLs and metadata
    patent_url: str                      # URL to patent page
    pdf_url: str                         # URL to patent PDF
    scraped_at: Optional[str]            # Scraping timestamp
    scraping_success: bool               # Scraping success flag
    scraping_errors: Optional[List[str]] # Any scraping errors
    source: str                          # Data source (uspto, google_patents, etc.)
```

## Advanced Usage

### Batch Patent Retrieval

```python
# Retrieve multiple specific patents
patent_numbers = [
    "US10123456B2",
    "US10234567B2", 
    "US10345678B2"
]

patents = scraper.batch_get_patents(
    patent_numbers,
    include_content=True,
    max_workers=5  # Concurrent workers
)
```

### Full Content Extraction

```python
options = PatentSearchOptions(
    keywords=["neural network"],
    max_results=10,
    include_full_text=True,    # Extract complete patent text
    include_claims=True,       # Extract all claims
    include_citations=True     # Extract citation data
)

patents = scraper.scrape(options)

for patent in patents:
    if patent.full_text:
        print(f"Full text length: {len(patent.full_text)} characters")
    if patent.claims:
        print(f"Number of claims: {len(patent.claims)}")
    if patent.cited_patents:
        print(f"Cites {len(patent.cited_patents)} patents")
```

### Citation Network Analysis

```python
# Get a patent with its citation network
patent = scraper.get_patent_by_number("US10123456B2", include_content=True)

if patent and patent.cited_patents:
    # Get all cited patents
    cited_patents = scraper.batch_get_patents(
        patent.cited_patents[:20],  # Limit to first 20
        include_content=False,
        max_workers=5
    )
    
    print(f"Patent {patent.patent_number} cites:")
    for cited in cited_patents:
        print(f"  {cited.patent_number}: {cited.title}")
```

### Technology Landscape Analysis

```python
# Analyze patents in a technology area
options = PatentSearchOptions(
    cpc_codes=["G06N3/08"],  # Neural networks
    start_date="2020-01-01",
    max_results=500
)

patents = scraper.scrape(options)

# Analyze by assignee
assignee_counts = {}
for patent in patents:
    for assignee in patent.assignees:
        assignee_counts[assignee] = assignee_counts.get(assignee, 0) + 1

# Top assignees in neural networks
top_assignees = sorted(assignee_counts.items(), key=lambda x: x[1], reverse=True)
print("Top assignees in neural networks:")
for assignee, count in top_assignees[:10]:
    print(f"  {assignee}: {count} patents")
```

## Output Formats

### JSON Format

```python
scraper.save_patents(patents, Path("patents.json"), format='json')
```

JSON structure:
```json
{
  "scraped_at": "2023-10-06T12:00:00",
  "total_patents": 100,
  "patents": [
    {
      "patent_number": "US10123456B2",
      "title": "Method for machine learning",
      "abstract": "A method for...",
      "inventors": ["John Smith", "Jane Doe"],
      "assignees": ["Tech Corp"],
      "filing_date": "2018-01-15",
      "publication_date": "2019-11-12",
      "cpc_codes": ["G06N3/08"],
      "status": "granted",
      "country_code": "US"
    }
  ]
}
```

### CSV Format

```python
scraper.save_patents(patents, Path("patents.csv"), format='csv')
```

CSV includes flattened data with comma-separated lists for multi-value fields.

### XML Format

```python
scraper.save_patents(patents, Path("patents.xml"), format='xml')
```

## Rate Limiting

The scraper implements rate limiting per USPTO guidelines:

- **USPTO API**: 120 requests per minute (2 requests per second)
- **Google Patents**: 1 request per second
- **Automatic backoff**: Exponential backoff on rate limit errors

```python
# Rate limiting is automatic, but you can configure it
from research_scrapers.config import Config

config = Config()
config.RATE_LIMIT = 1.0  # 1 request per second

scraper = PatentScraper(config)
```

## Error Handling

The scraper includes comprehensive error handling:

```python
try:
    patents = scraper.scrape(options)
    
    # Check for scraping errors
    for patent in patents:
        if not patent.scraping_success:
            print(f"Error scraping {patent.patent_number}: {patent.scraping_errors}")
            
except Exception as e:
    print(f"Search failed: {e}")
```

### Common Error Types

- **Rate limit exceeded**: Automatic retry with backoff
- **Patent not found**: Returns None or empty list
- **Network errors**: Automatic retry with exponential backoff
- **Invalid patent number**: Validation and normalization
- **API changes**: Graceful degradation

## Examples

### Example 1: Technology Trend Analysis

```python
# Analyze AI patent trends over time
years = ["2019", "2020", "2021", "2022", "2023"]
ai_patents_by_year = {}

for year in years:
    options = PatentSearchOptions(
        keywords=["artificial intelligence"],
        start_date=f"{year}-01-01",
        end_date=f"{year}-12-31",
        max_results=1000
    )
    
    patents = scraper.scrape(options)
    ai_patents_by_year[year] = len(patents)
    
    print(f"{year}: {len(patents)} AI patents")
```

### Example 2: Competitive Intelligence

```python
# Compare patent portfolios of competitors
companies = ["Google LLC", "Microsoft Corporation", "Apple Inc."]
company_patents = {}

for company in companies:
    patents = scraper.search_by_assignee(company, max_results=500)
    company_patents[company] = patents
    
    # Analyze by technology area
    tech_areas = {}
    for patent in patents:
        for code in patent.cpc_codes or []:
            section = code[0] if code else "Unknown"
            tech_areas[section] = tech_areas.get(section, 0) + 1
    
    print(f"\n{company} - Top technology areas:")
    for area, count in sorted(tech_areas.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"  {area}: {count} patents")
```

### Example 3: Inventor Analysis

```python
# Analyze prolific inventors in a field
options = PatentSearchOptions(
    cpc_codes=["G06N"],  # Computing arrangements based on specific computational models
    start_date="2020-01-01",
    max_results=1000
)

patents = scraper.scrape(options)

# Count patents per inventor
inventor_counts = {}
for patent in patents:
    for inventor in patent.inventors:
        inventor_counts[inventor] = inventor_counts.get(inventor, 0) + 1

# Top inventors
top_inventors = sorted(inventor_counts.items(), key=lambda x: x[1], reverse=True)
print("Most prolific inventors in AI:")
for inventor, count in top_inventors[:20]:
    print(f"  {inventor}: {count} patents")
```

## Best Practices

### 1. Efficient Searching

```python
# Use specific search criteria to reduce API calls
options = PatentSearchOptions(
    cpc_codes=["G06N3/08"],  # Specific CPC code
    assignees=["Google LLC"],  # Specific assignee
    start_date="2022-01-01",   # Recent patents only
    max_results=100            # Reasonable limit
)
```

### 2. Batch Processing

```python
# Process patents in batches to avoid memory issues
def process_patents_in_batches(patent_numbers, batch_size=50):
    all_patents = []
    
    for i in range(0, len(patent_numbers), batch_size):
        batch = patent_numbers[i:i + batch_size]
        patents = scraper.batch_get_patents(batch, max_workers=3)
        all_patents.extend(patents)
        
        # Save intermediate results
        if len(all_patents) % 100 == 0:
            print(f"Processed {len(all_patents)} patents...")
    
    return all_patents
```

### 3. Error Recovery

```python
# Implement robust error handling
def safe_patent_search(options, max_retries=3):
    for attempt in range(max_retries):
        try:
            return scraper.scrape(options)
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)  # Exponential backoff
```

### 4. Data Validation

```python
# Validate patent data before processing
def validate_patent(patent):
    if not patent.patent_number:
        return False
    if not patent.title:
        return False
    if not patent.inventors:
        return False
    return True

# Filter valid patents
valid_patents = [p for p in patents if validate_patent(p)]
```

## API References

### Classification Codes

#### CPC (Cooperative Patent Classification)
- **A**: Human Necessities
- **B**: Performing Operations; Transporting  
- **C**: Chemistry; Metallurgy
- **D**: Textiles; Paper
- **E**: Fixed Constructions
- **F**: Mechanical Engineering; Lighting; Heating; Weapons; Blasting
- **G**: Physics
- **H**: Electricity
- **Y**: General Tagging of New Technological Developments

#### Common CPC Codes for Technology
- **G06F**: Electric digital data processing
- **G06N**: Computing arrangements based on specific computational models
- **G06N3/08**: Learning methods (Neural networks)
- **H04L**: Transmission of digital information
- **G06Q**: Data processing systems or methods for administrative purposes

### Patent Number Formats

- **US Utility**: US1234567B2, US10123456B2
- **US Application**: US20230123456A1
- **European**: EP1234567B1
- **World**: WO2023/123456A1
- **Japanese**: JP2023123456A

### Date Formats

All dates should be in ISO format: `YYYY-MM-DD`

### Country Codes

- **US**: United States
- **EP**: European Patent Office
- **WO**: World Intellectual Property Organization
- **JP**: Japan
- **CN**: China
- **KR**: South Korea
- **DE**: Germany
- **GB**: United Kingdom
- **FR**: France

---

For more examples and advanced usage, see the `examples/patent_scraper_examples.py` file in the repository.