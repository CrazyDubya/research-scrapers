# ArXiv Scraper Documentation

## Overview

The ArXiv scraper (`arxiv_scraper.py`) is a comprehensive tool for searching, downloading, and extracting content from ArXiv research papers. It provides advanced search capabilities, PDF processing, full-text extraction, and batch operations while respecting ArXiv's rate limiting guidelines.

## Features

### Core Functionality
- **ArXiv API Integration**: Native XML parsing of ArXiv API responses
- **Advanced Search**: Search by categories, authors, keywords, date ranges
- **PDF Download**: Automatic PDF retrieval with retry logic
- **Text Extraction**: Multiple PDF processing engines (pdfplumber, PyPDF2, pdfminer)
- **Batch Operations**: Concurrent processing of multiple papers
- **Rate Limiting**: Complies with ArXiv's 3-second rate limit guidelines
- **Multiple Output Formats**: JSON, CSV, XML export options

### Search Capabilities
- General keyword search across all fields
- Category-specific filtering (cs.AI, physics.gen-ph, etc.)
- Author name filtering
- Title and abstract keyword matching
- Date range filtering
- Recent papers discovery
- Specific paper ID retrieval

### Content Processing
- Metadata extraction (title, authors, abstract, categories, dates)
- PDF content download and storage
- Full-text extraction from PDFs
- Reference extraction from paper text
- Data validation and cleaning

## Installation

### Prerequisites

```bash
# Install required PDF processing libraries
pip install PyPDF2>=3.0.0 pdfplumber>=0.10.0 pdfminer.six>=20221105

# Or install all requirements
pip install -r requirements.txt
```

### Dependencies

The scraper requires the following Python packages:
- `requests` - HTTP requests
- `PyPDF2` - PDF processing (primary)
- `pdfplumber` - Advanced PDF text extraction
- `pdfminer.six` - Alternative PDF processing
- Standard library: `xml.etree.ElementTree`, `concurrent.futures`, `dataclasses`

## Quick Start

### Basic Usage

```bash
# Search for machine learning papers
python arxiv_scraper.py --query "machine learning" --max-results 50

# Search by category
python arxiv_scraper.py --categories cs.AI cs.LG --max-results 100

# Get a specific paper
python arxiv_scraper.py --paper-id 2301.07041 --include-full-text
```

### Advanced Examples

```bash
# Search with full content extraction
python arxiv_scraper.py --query "deep learning" --include-pdf --include-full-text --extract-references

# Recent papers in multiple categories
python arxiv_scraper.py --recent-days 7 --categories cs.AI cs.CV cs.LG --max-results 200

# Batch download specific papers
python arxiv_scraper.py --paper-ids 2301.07041 2302.12345 2303.56789 --include-pdf

# Search with date range and author filter
python arxiv_scraper.py --query "quantum computing" --authors "John Preskill" --start-date 2023-01-01 --end-date 2023-12-31

# Export to different formats
python arxiv_scraper.py --query "neural networks" --format csv --output results.csv
```

## Command Line Interface

### Search Options

| Option | Description | Example |
|--------|-------------|---------|
| `--query` | General search query | `--query "machine learning"` |
| `--categories` | ArXiv categories | `--categories cs.AI physics.gen-ph` |
| `--authors` | Author names | `--authors "Geoffrey Hinton" "Yann LeCun"` |
| `--title-keywords` | Keywords in titles | `--title-keywords neural network` |
| `--abstract-keywords` | Keywords in abstracts | `--abstract-keywords "deep learning"` |

### Date Filtering

| Option | Description | Format | Example |
|--------|-------------|--------|---------|
| `--start-date` | Start date | YYYY-MM-DD | `--start-date 2023-01-01` |
| `--end-date` | End date | YYYY-MM-DD | `--end-date 2023-12-31` |
| `--recent-days` | Last N days | Integer | `--recent-days 7` |

### Content Options

| Option | Description | Impact |
|--------|-------------|--------|
| `--include-pdf` | Download PDF files | Increases processing time and storage |
| `--include-full-text` | Extract text from PDFs | Requires PDF processing libraries |
| `--extract-references` | Extract paper references | Requires full-text extraction |

### Result Options

| Option | Description | Default | Range |
|--------|-------------|---------|-------|
| `--max-results` | Maximum papers to fetch | 100 | 1-2000 |
| `--start-index` | Starting result index | 0 | 0+ |
| `--sort-by` | Sort criterion | relevance | relevance, lastUpdatedDate, submittedDate |
| `--sort-order` | Sort direction | descending | ascending, descending |

### Output Options

| Option | Description | Formats |
|--------|-------------|---------|
| `--output` | Output file path | Any valid path |
| `--format` | Output format | json, csv, xml |
| `--verbose` | Detailed logging | Flag |

## Programming Interface

### Basic Usage

```python
from arxiv_scraper import ArxivScraper, ArxivSearchOptions

# Initialize scraper
scraper = ArxivScraper()

# Create search options
options = ArxivSearchOptions(
    query="machine learning",
    categories=["cs.AI", "cs.LG"],
    max_results=50,
    include_pdf=True,
    include_full_text=True
)

# Perform search
papers = scraper.search_papers(options)

# Process results
for paper in papers:
    print(f"Title: {paper.title}")
    print(f"Authors: {', '.join(paper.authors)}")
    print(f"Abstract: {paper.abstract[:200]}...")
    if paper.full_text:
        print(f"Full text length: {len(paper.full_text)} characters")
```

### Advanced Operations

```python
# Get specific paper
paper = scraper.get_paper_by_id("2301.07041", include_content=True)

# Batch download
paper_ids = ["2301.07041", "2302.12345", "2303.56789"]
papers = scraper.batch_download_papers(paper_ids, include_content=True)

# Search by category
ai_papers = scraper.search_by_category("cs.AI", max_results=100)

# Recent papers
recent_papers = scraper.search_recent_papers(days=7, categories=["cs.AI"])
```

### Data Structures

#### ArxivPaper Class

```python
@dataclass
class ArxivPaper:
    id: str                           # ArXiv ID (e.g., "2301.07041")
    title: str                        # Paper title
    authors: List[str]                # List of author names
    abstract: str                     # Paper abstract
    categories: List[str]             # ArXiv categories
    primary_category: str             # Primary category
    published: str                    # Publication date (ISO format)
    updated: str                      # Last update date (ISO format)
    doi: Optional[str]                # DOI if available
    journal_ref: Optional[str]        # Journal reference
    comments: Optional[str]           # Author comments
    pdf_url: str                      # PDF download URL
    abs_url: str                      # Abstract page URL
    
    # Optional content
    pdf_content: Optional[bytes]      # PDF binary data
    full_text: Optional[str]          # Extracted text
    references: Optional[List[str]]   # Extracted references
    
    # Metadata
    scraped_at: Optional[str]         # Scraping timestamp
    scraping_success: bool            # Success flag
    scraping_errors: Optional[List[str]]  # Error messages
```

#### ArxivSearchOptions Class

```python
@dataclass
class ArxivSearchOptions:
    query: Optional[str] = None                    # General search query
    categories: Optional[List[str]] = None         # Category filters
    authors: Optional[List[str]] = None            # Author filters
    title_keywords: Optional[List[str]] = None     # Title keywords
    abstract_keywords: Optional[List[str]] = None  # Abstract keywords
    
    # Date filtering
    start_date: Optional[str] = None               # Start date (YYYY-MM-DD)
    end_date: Optional[str] = None                 # End date (YYYY-MM-DD)
    
    # Result limits
    max_results: int = 100                         # Maximum results
    start_index: int = 0                           # Starting index
    
    # Sorting
    sort_by: str = 'relevance'                     # Sort criterion
    sort_order: str = 'descending'                 # Sort order
    
    # Content options
    include_pdf: bool = False                      # Download PDFs
    include_full_text: bool = False                # Extract full text
    extract_references: bool = False               # Extract references
    
    # Output options
    output_format: str = 'json'                    # Output format
    output_file: Optional[str] = None              # Output file
    verbose: bool = False                          # Verbose mode
```

## ArXiv Categories

### Computer Science
- `cs.AI` - Artificial Intelligence
- `cs.CL` - Computation and Language
- `cs.CV` - Computer Vision and Pattern Recognition
- `cs.LG` - Machine Learning
- `cs.NE` - Neural and Evolutionary Computing
- `cs.RO` - Robotics
- `cs.CR` - Cryptography and Security
- `cs.DS` - Data Structures and Algorithms

### Physics
- `physics.gen-ph` - General Physics
- `quant-ph` - Quantum Physics
- `cond-mat` - Condensed Matter
- `astro-ph` - Astrophysics
- `hep-th` - High Energy Physics - Theory
- `hep-ph` - High Energy Physics - Phenomenology

### Mathematics
- `math.AG` - Algebraic Geometry
- `math.AT` - Algebraic Topology
- `math.CO` - Combinatorics
- `math.NT` - Number Theory
- `math.ST` - Statistics Theory

### Other Fields
- `q-bio` - Quantitative Biology
- `q-fin` - Quantitative Finance
- `stat` - Statistics
- `eess` - Electrical Engineering and Systems Science
- `econ` - Economics

## Rate Limiting and Best Practices

### ArXiv Guidelines
- **Rate Limit**: 1 request per 3 seconds (automatically enforced)
- **Bulk Downloads**: Use batch operations for multiple papers
- **Respectful Usage**: Avoid unnecessary requests
- **Caching**: Results are automatically timestamped for caching

### Performance Tips

```python
# Use batch operations for multiple papers
papers = scraper.batch_download_papers(paper_ids, max_workers=3)

# Limit results for faster processing
options = ArxivSearchOptions(max_results=50)  # Instead of 1000

# Skip full-text extraction for metadata-only searches
options = ArxivSearchOptions(include_pdf=False, include_full_text=False)

# Use specific categories to narrow search
options = ArxivSearchOptions(categories=["cs.AI"], query="neural networks")
```

## Error Handling

### Common Issues and Solutions

#### PDF Processing Errors
```python
# Install all PDF libraries for best compatibility
pip install PyPDF2 pdfplumber pdfminer.six

# Check available processors
scraper = ArxivScraper()
print(f"Available PDF processors: {scraper.pdf_processors}")
```

#### Rate Limiting
```python
# Rate limiting is automatic, but you can check status
try:
    papers = scraper.search_papers(options)
except APIError as e:
    if "rate limit" in str(e).lower():
        print("Rate limit exceeded, waiting...")
        time.sleep(10)
```

#### Network Issues
```python
# Exponential backoff is built-in, but you can catch network errors
try:
    papers = scraper.search_papers(options)
except APIError as e:
    print(f"API error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Output Formats

### JSON Format
```json
{
  "scraped_at": "2024-01-15T10:30:00",
  "total_papers": 2,
  "papers": [
    {
      "id": "2301.07041",
      "title": "Example Paper Title",
      "authors": ["Author One", "Author Two"],
      "abstract": "Paper abstract...",
      "categories": ["cs.AI", "cs.LG"],
      "primary_category": "cs.AI",
      "published": "2023-01-17T18:00:00Z",
      "updated": "2023-01-17T18:00:00Z",
      "pdf_url": "https://arxiv.org/pdf/2301.07041.pdf",
      "abs_url": "https://arxiv.org/abs/2301.07041"
    }
  ]
}
```

### CSV Format
- Flattened structure with comma-separated lists
- Suitable for spreadsheet analysis
- Limited reference data (first 5 references)

### XML Format
- Hierarchical structure preserving all data
- Suitable for structured data processing
- Full reference lists included

## Integration Examples

### Research Workflow
```python
# Daily research update workflow
def daily_research_update():
    scraper = ArxivScraper()
    
    # Get recent papers in your field
    papers = scraper.search_recent_papers(
        days=1,
        categories=["cs.AI", "cs.LG", "cs.CV"],
        max_results=50
    )
    
    # Filter by keywords
    relevant_papers = [
        paper for paper in papers
        if any(keyword in paper.title.lower() or keyword in paper.abstract.lower()
               for keyword in ["neural", "deep learning", "transformer"])
    ]
    
    # Save results
    save_papers(relevant_papers, Path("daily_papers.json"))
    
    return relevant_papers
```

### Literature Review
```python
# Comprehensive literature review
def literature_review(topic, start_year=2020):
    scraper = ArxivScraper()
    
    all_papers = []
    
    # Search multiple related queries
    queries = [
        f"{topic}",
        f"{topic} survey",
        f"{topic} review",
        f"{topic} applications"
    ]
    
    for query in queries:
        options = ArxivSearchOptions(
            query=query,
            start_date=f"{start_year}-01-01",
            max_results=200,
            sort_by="submittedDate",
            sort_order="descending"
        )
        
        papers = scraper.search_papers(options)
        all_papers.extend(papers)
    
    # Remove duplicates
    unique_papers = {paper.id: paper for paper in all_papers}.values()
    
    return list(unique_papers)
```

### Citation Analysis
```python
# Extract and analyze citations
def analyze_citations(paper_ids):
    scraper = ArxivScraper()
    
    papers = scraper.batch_download_papers(
        paper_ids,
        include_content=True,
        max_workers=3
    )
    
    all_references = []
    for paper in papers:
        if paper.references:
            all_references.extend(paper.references)
    
    # Analyze citation patterns
    citation_counts = {}
    for ref in all_references:
        # Simple citation counting (could be enhanced)
        citation_counts[ref] = citation_counts.get(ref, 0) + 1
    
    return sorted(citation_counts.items(), key=lambda x: x[1], reverse=True)
```

## Troubleshooting

### Common Issues

1. **No PDF processors available**
   ```bash
   pip install PyPDF2 pdfplumber pdfminer.six
   ```

2. **Rate limit errors**
   - The scraper automatically handles rate limiting
   - For large batches, use smaller `max_workers` values

3. **Memory issues with large PDFs**
   - Process papers in smaller batches
   - Skip PDF download for metadata-only searches

4. **Network timeouts**
   - Built-in retry logic handles temporary failures
   - Check internet connection for persistent issues

### Debug Mode

```bash
# Enable verbose logging
python arxiv_scraper.py --query "test" --verbose

# Check available categories
python arxiv_scraper.py --show-categories
```

## Contributing

To contribute to the ArXiv scraper:

1. Follow the existing code patterns from `github_repo_scraper.py`
2. Use the utilities from `utils.py` and `config.py`
3. Add comprehensive error handling
4. Include unit tests for new functionality
5. Update documentation for new features

## License

This scraper is part of the research-scrapers project and follows the same MIT license terms.