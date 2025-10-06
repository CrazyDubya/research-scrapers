# Patent Database Scraper

The Patent Scraper provides comprehensive access to multiple patent databases including USPTO and Google Patents, with advanced search capabilities, full-text extraction, and citation analysis.

## Features

- 🔍 **Multi-source Search**: USPTO Patent API and Google Patents integration
- 📊 **Advanced Filtering**: Keywords, inventors, assignees, CPC/IPC codes
- 📅 **Date Range Filtering**: Publication, filing, and priority dates
- 📝 **Full Content Extraction**: Patent text, claims, descriptions
- 🔗 **Citation Analysis**: Forward and backward patent citations
- ⚡ **Batch Operations**: Concurrent processing of multiple patents
- 💾 **Multiple Formats**: Export to JSON, CSV, XML
- 🚦 **Rate Limiting**: Compliant with USPTO guidelines (120 req/min)
- 🛡️ **Error Handling**: Automatic retry with exponential backoff

## Quick Start

### Basic Search

```python
from research_scrapers import PatentScraper, PatentSearchOptions

# Initialize scraper
scraper = PatentScraper()

# Search by keywords
options = PatentSearchOptions(
    keywords=["machine learning", "neural network"],
    max_results=50
)

patents = scraper.scrape(options)

for patent in patents:
    print(f"{patent.patent_number}: {patent.title}")
```

### Get Specific Patent

```python
# Retrieve a specific patent with full content
patent = scraper.get_patent_by_number(
    "US10123456B2", 
    include_content=True
)

print(f"Title: {patent.title}")
print(f"Inventors: {', '.join(patent.inventors)}")
print(f"Abstract: {patent.abstract}")

if patent.claims:
    print(f"Number of claims: {len(patent.claims)}")
```

### Search by Inventor

```python
# Find all patents by an inventor
patents = scraper.search_by_inventor("Geoffrey Hinton", max_results=100)

print(f"Found {len(patents)} patents")
for patent in patents[:5]:
    print(f"  {patent.patent_number}: {patent.title}")
```

### Search by Company/Assignee

```python
# Find patents from a specific company
patents = scraper.search_by_assignee("Google LLC", max_results=100)

# Analyze by technology area
tech_areas = {}
for patent in patents:
    for code in patent.cpc_codes or []:
        section = code[0] if code else "Unknown"
        tech_areas[section] = tech_areas.get(section, 0) + 1

print("Top technology areas:")
for area, count in sorted(tech_areas.items(), key=lambda x: x[1], reverse=True)[:5]:
    print(f"  {area}: {count} patents")
```

### Search by Technology Classification

```python
# Search by CPC code
patents = scraper.search_by_cpc_code("G06N", max_results=100)

# G06N = Computing arrangements based on specific computational models
print(f"Found {len(patents)} patents in AI/machine learning")
```

### Recent Patents

```python
# Find patents published in last 30 days
patents = scraper.search_recent_patents(
    days=30,
    keywords=["quantum computing"],
    max_results=50
)
```

## Advanced Search

### Multi-criteria Search

```python
options = PatentSearchOptions(
    keywords=["artificial intelligence"],
    assignees=["IBM", "Microsoft", "Google"],
    cpc_codes=["G06N"],
    start_date="2020-01-01",
    end_date="2023-12-31",
    country_codes=["US"],
    max_results=200,
    include_full_text=True,
    include_claims=True,
    include_citations=True
)

patents = scraper.scrape(options)
```

### Batch Patent Retrieval

```python
# Retrieve multiple patents concurrently
patent_numbers = [
    "US10123456B2",
    "US10234567B2", 
    "US10345678B2"
]

patents = scraper.batch_get_patents(
    patent_numbers,
    include_content=True,
    max_workers=5
)
```

### Citation Network Analysis

```python
# Get patent with citations
patent = scraper.get_patent_by_number("US10123456B2", include_content=True)

if patent.cited_patents:
    print(f"This patent cites {len(patent.cited_patents)} other patents")
    
    # Retrieve cited patents
    cited = scraper.batch_get_patents(
        patent.cited_patents[:10],
        include_content=False
    )
    
    for cited_patent in cited:
        print(f"  {cited_patent.patent_number}: {cited_patent.title}")
```

## Search Options

```python
PatentSearchOptions(
    # Search terms
    query="general search query",
    keywords=["keyword1", "keyword2"],
    inventors=["John Smith"],
    assignees=["Google LLC", "Microsoft"],
    patent_numbers=["US10123456B2"],
    
    # Classification codes
    cpc_codes=["G06N", "G06F"],
    ipc_codes=["G06F15/18"],
    uspc_codes=["706/15"],
    
    # Date filtering
    start_date="2020-01-01",
    end_date="2023-12-31",
    date_type="publication",  # or "filing", "priority"
    
    # Patent characteristics
    patent_type="utility",  # or "design", "plant", "reissue"
    status="active",        # or "expired", "pending", "abandoned"
    country_codes=["US", "EP"],
    
    # Result configuration
    max_results=100,
    start_index=0,
    sort_by="date",         # or "relevance", "patent_number"
    sort_order="descending",
    
    # Content extraction
    include_full_text=True,
    include_claims=True,
    include_citations=True,
    include_family=True,
    
    # Output
    output_format="json",   # or "csv", "xml"
    verbose=False
)
```

## Patent Data Structure

```python
@dataclass
class Patent:
    patent_number: str          # e.g., "US10123456B2"
    title: str
    abstract: str
    inventors: List[str]
    assignees: List[str]
    
    filing_date: str
    publication_date: str
    grant_date: Optional[str]
    priority_date: Optional[str]
    
    cpc_codes: List[str]       # Cooperative Patent Classification
    ipc_codes: List[str]       # International Patent Classification
    uspc_codes: List[str]      # US Patent Classification
    
    status: str
    country_code: str
    patent_type: str
    
    claims: Optional[List[str]]
    description: Optional[str]
    full_text: Optional[str]
    
    cited_patents: Optional[List[str]]
    citing_patents: Optional[List[str]]
    patent_family: Optional[List[str]]
    
    patent_url: str
    pdf_url: str
    source: str               # "uspto" or "google_patents"
```

## Save Results

```python
# JSON format
scraper.save_patents(patents, Path("patents.json"), format='json')

# CSV format (flattened data)
scraper.save_patents(patents, Path("patents.csv"), format='csv')

# XML format
scraper.save_patents(patents, Path("patents.xml"), format='xml')
```

## Common CPC Classification Codes

| Code | Description |
|------|-------------|
| **A** | Human Necessities |
| **B** | Performing Operations; Transporting |
| **C** | Chemistry; Metallurgy |
| **D** | Textiles; Paper |
| **E** | Fixed Constructions |
| **F** | Mechanical Engineering |
| **G** | Physics |
| **H** | Electricity |

### Technology-Specific Codes

| Code | Description |
|------|-------------|
| **G06F** | Electric digital data processing |
| **G06N** | Computing arrangements (AI/ML) |
| **G06N3/08** | Neural networks |
| **H04L** | Transmission of digital information |
| **G06Q** | Data processing for business |
| **H01L** | Semiconductor devices |
| **A61K** | Medical preparations |
| **H02S** | Solar energy generation |

## Examples

### Example 1: Technology Landscape Analysis

```python
# Analyze AI patent trends by year
ai_patents_by_year = {}

for year in range(2019, 2024):
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
# Compare patent portfolios
companies = ["Google LLC", "Microsoft Corporation", "Apple Inc."]

for company in companies:
    patents = scraper.search_by_assignee(company, max_results=500)
    print(f"\n{company}: {len(patents)} patents")
    
    # Top technology areas
    tech_areas = {}
    for patent in patents:
        for code in patent.cpc_codes or []:
            section = code[0]
            tech_areas[section] = tech_areas.get(section, 0) + 1
    
    print("Top areas:", dict(sorted(tech_areas.items(), key=lambda x: x[1], reverse=True)[:3]))
```

### Example 3: Inventor Portfolio

```python
# Analyze prolific inventors
options = PatentSearchOptions(
    cpc_codes=["G06N"],  # AI/ML patents
    start_date="2020-01-01",
    max_results=1000
)

patents = scraper.scrape(options)

inventor_counts = {}
for patent in patents:
    for inventor in patent.inventors:
        inventor_counts[inventor] = inventor_counts.get(inventor, 0) + 1

top_inventors = sorted(inventor_counts.items(), key=lambda x: x[1], reverse=True)
print("Top 10 AI inventors:")
for inventor, count in top_inventors[:10]:
    print(f"  {inventor}: {count} patents")
```

## Rate Limiting and Best Practices

### Rate Limits
- **USPTO API**: 120 requests per minute (automatic)
- **Google Patents**: 1 request per second (automatic)

### Best Practices

1. **Use specific search criteria** to reduce API calls
2. **Process in batches** for large datasets
3. **Implement error recovery** for network issues
4. **Cache results** when possible
5. **Validate data** before processing

```python
# Efficient batch processing
def process_in_batches(patent_numbers, batch_size=50):
    all_patents = []
    for i in range(0, len(patent_numbers), batch_size):
        batch = patent_numbers[i:i + batch_size]
        patents = scraper.batch_get_patents(batch, max_workers=3)
        all_patents.extend(patents)
    return all_patents
```

## Error Handling

```python
try:
    patents = scraper.scrape(options)
    
    # Check for errors
    for patent in patents:
        if not patent.scraping_success:
            print(f"Error: {patent.scraping_errors}")
            
except Exception as e:
    print(f"Search failed: {e}")
```

## Documentation

For comprehensive documentation, see:
- [Patent Scraper Guide](PATENT_SCRAPER_GUIDE.md) - Complete usage guide
- [Examples](../examples/patent_scraper_examples.py) - Detailed examples
- [API Reference](api-reference.md) - Full API documentation

## Command Line Usage (Coming Soon)

```bash
# Search patents
python patent_scraper.py --keywords "machine learning" --max-results 100

# Get specific patent
python patent_scraper.py --patent-id US10123456B2 --include-full-text

# Search by assignee
python patent_scraper.py --assignee "Google LLC" --cpc-codes G06N --output patents.json
```

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](contributing.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.