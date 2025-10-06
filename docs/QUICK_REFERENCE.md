# Research Scrapers - Quick Reference Guide

This guide provides a quick overview of all available scrapers and their most common usage patterns.

## 📚 Available Scrapers

| Scraper | Description | Script | Documentation |
|---------|-------------|--------|---------------|
| **ArXiv** | Research papers from ArXiv.org | `arxiv_scraper.py` | [Guide](ARXIV_SCRAPER_GUIDE.md) |
| **Stack Overflow** | Q&A from Stack Overflow | `stackoverflow_scraper.py` | [Guide](STACKOVERFLOW_SCRAPER.md) |
| **Patent** | Patents from USPTO & Google Patents | `patent_scraper.py` | [Guide](PATENT_SCRAPER_GUIDE.md) |
| **GitHub** | GitHub repositories, issues, users | `github_*_scraper.py` | Built-in |
| **Linear** | Project management (Coming Soon) | - | [RUB-50](https://linear.app/rubberducky/issue/RUB-50) |

## 🚀 Quick Start Commands

### ArXiv Research Papers

```bash
# Search by query
python arxiv_scraper.py --query "machine learning" --max-results 50

# Search by category
python arxiv_scraper.py --categories cs.AI cs.LG --max-results 100

# Get specific paper with full text
python arxiv_scraper.py --paper-id 2301.07041 --include-full-text

# Recent papers
python arxiv_scraper.py --recent-days 7 --categories cs.AI --max-results 50
```

### Stack Overflow Q&A

```bash
# Search by tags
python stackoverflow_scraper.py --tags python machine-learning --max-results 100

# Search by keywords
python stackoverflow_scraper.py --query "neural networks" --sort activity --max-results 50

# Get user information
python stackoverflow_scraper.py --user-ids 12345 67890 --include-user-details

# Recent questions
python stackoverflow_scraper.py --recent-days 7 --tags python --min-score 5
```

### Patent Databases

```bash
# Search by keywords
python patent_scraper.py --keywords "machine learning" --max-results 50

# Search by inventor
python patent_scraper.py --inventors "John Smith" --max-results 100

# Search by company
python patent_scraper.py --assignees "Google" --include-full-text --max-results 50

# Get specific patent
python patent_scraper.py --patent-number US10123456B2 --include-claims

# Search by classification
python patent_scraper.py --cpc-codes "G06F" --recent-days 30
```

## 💻 Programming Interface Examples

### ArXiv

```python
from arxiv_scraper import ArxivScraper, ArxivSearchOptions

scraper = ArxivScraper()
options = ArxivSearchOptions(
    query="deep learning",
    categories=["cs.AI", "cs.LG"],
    max_results=50,
    include_full_text=True
)
papers = scraper.search_papers(options)
```

### Stack Overflow

```python
from research_scrapers.stackoverflow_scraper import StackOverflowScraper, ScrapingOptions

scraper = StackOverflowScraper(api_key="your_key")
options = ScrapingOptions(
    tags=["python", "machine-learning"],
    max_results=100,
    include_answers=True
)
questions = scraper.search_questions(options)
```

### Patent

```python
from research_scrapers.patent_scraper import PatentScraper, PatentSearchOptions

scraper = PatentScraper()
options = PatentSearchOptions(
    keywords=["artificial intelligence"],
    assignees=["Google"],
    max_results=100,
    include_full_text=True
)
patents = scraper.scrape(options)
```

### GitHub

```python
from research_scrapers import GitHubScraper

with GitHubScraper() as scraper:
    repo = scraper.scrape_repository("facebook", "react")
    user = scraper.scrape_user("torvalds")
```

## 🔧 Common Configuration

### Environment Variables

```bash
# API Keys
export GITHUB_TOKEN=ghp_your_github_token
export STACKOVERFLOW_API_KEY=your_stackoverflow_key

# Scraper Settings
export SCRAPER_RATE_LIMIT=2.0
export SCRAPER_REQUEST_TIMEOUT=60
export SCRAPER_LOG_LEVEL=INFO
```

### Config File (config.json)

```json
{
  "rate_limit": 2.0,
  "request_timeout": 60,
  "log_level": "INFO",
  "api_keys": {
    "github": "ghp_your_token",
    "stackoverflow": "your_key"
  }
}
```

## 📊 Output Formats

All scrapers support multiple output formats:

```bash
# JSON (default)
python arxiv_scraper.py --query "AI" --output results.json

# CSV
python stackoverflow_scraper.py --tags python --format csv --output results.csv

# XML
python patent_scraper.py --keywords "blockchain" --format xml --output results.xml
```

## 🔍 Advanced Search Examples

### Multi-Source Research

```python
# Combine multiple sources for comprehensive research
from arxiv_scraper import ArxivScraper, ArxivSearchOptions
from research_scrapers.stackoverflow_scraper import StackOverflowScraper, ScrapingOptions
from research_scrapers.patent_scraper import PatentScraper, PatentSearchOptions

topic = "neural networks"

# ArXiv papers
arxiv = ArxivScraper()
papers = arxiv.search_papers(ArxivSearchOptions(
    query=topic, max_results=100, include_full_text=True
))

# Stack Overflow discussions
so = StackOverflowScraper()
questions = so.search_questions(ScrapingOptions(
    query=topic, max_results=50, include_answers=True
))

# Patents
patents = PatentScraper()
patent_results = patents.scrape(PatentSearchOptions(
    keywords=[topic], max_results=100, include_claims=True
))
```

### Date-Filtered Searches

```bash
# ArXiv: Papers from specific date range
python arxiv_scraper.py --query "quantum computing" \
  --start-date 2023-01-01 --end-date 2023-12-31

# Stack Overflow: Recent activity
python stackoverflow_scraper.py --tags python \
  --recent-days 30 --sort activity

# Patents: Recent filings
python patent_scraper.py --keywords "AI" \
  --start-date 2023-01-01 --date-type filing
```

### Batch Operations

```bash
# ArXiv: Multiple paper IDs
python arxiv_scraper.py --paper-ids 2301.07041 2302.12345 2303.56789 \
  --include-full-text

# Stack Overflow: Multiple users
python stackoverflow_scraper.py --user-ids 12345 67890 54321 \
  --include-user-details

# Patents: Multiple patent numbers
python patent_scraper.py --patent-numbers US10123456 US10234567 US10345678 \
  --include-claims
```

## 🎯 Common Use Cases

### 1. Literature Review

```bash
# Get comprehensive research papers on a topic
python arxiv_scraper.py --query "transformer models" \
  --categories cs.AI cs.LG cs.CL \
  --start-date 2020-01-01 \
  --max-results 200 \
  --include-full-text \
  --extract-references \
  --output literature_review.json
```

### 2. Technology Trend Analysis

```bash
# Analyze Stack Overflow trends
python stackoverflow_scraper.py --tags artificial-intelligence machine-learning \
  --sort creation --order desc \
  --max-results 1000 \
  --format csv \
  --output ai_trends.csv
```

### 3. Patent Landscape Analysis

```bash
# Company patent portfolio analysis
python patent_scraper.py --assignees "Google" "Microsoft" "Amazon" \
  --keywords "machine learning" \
  --start-date 2020-01-01 \
  --include-citations \
  --max-results 500 \
  --output company_patents.json
```

### 4. Code Example Collection

```bash
# Find well-answered coding questions
python stackoverflow_scraper.py --tags python tensorflow \
  --min-score 10 \
  --has-accepted-answer \
  --include-answers \
  --include-comments \
  --max-results 100 \
  --output tensorflow_examples.json
```

### 5. Inventor Research

```bash
# Track specific inventor's patents
python patent_scraper.py --inventors "John Smith" "Jane Doe" \
  --sort-by date \
  --include-full-text \
  --include-family \
  --max-results 200 \
  --output inventor_portfolio.json
```

## 🛠️ Troubleshooting

### Rate Limiting

```python
# Slow down requests if hitting rate limits
from research_scrapers import Config

config = Config()
config.RATE_LIMIT = 0.5  # 0.5 requests per second
```

### API Quotas

```bash
# Stack Overflow API quotas
# - Authenticated: 10,000 requests/day
# - Unauthenticated: 300 requests/day

# Use API key for higher limits
export STACKOVERFLOW_API_KEY=your_key_here
```

### Memory Management

```python
# Process large datasets in batches
from research_scrapers.utils import batch_process

# Split into smaller batches
for batch in batch_process(large_list, batch_size=100):
    process_batch(batch)
```

## 📚 Additional Resources

- **Full Documentation**: See individual scraper guides in `docs/`
- **API Architecture**: [docs/API_ARCHITECTURE.md](API_ARCHITECTURE.md)
- **Integration Guide**: [docs/INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md)
- **Security Best Practices**: [docs/SECURITY_ARCHITECTURE.md](SECURITY_ARCHITECTURE.md)
- **Project Roadmap**: [ROADMAP.md](../ROADMAP.md)

## 🔗 Quick Links

| Resource | Link |
|----------|------|
| GitHub Repository | https://github.com/CrazyDubya/research-scrapers |
| Issue Tracker | https://github.com/CrazyDubya/research-scrapers/issues |
| Discussions | https://github.com/CrazyDubya/research-scrapers/discussions |
| Linear Project (RUB-50) | https://linear.app/rubberducky/issue/RUB-50 |

## 💡 Tips & Best Practices

1. **Always Use API Keys**: Better rate limits and access to more features
2. **Respect Rate Limits**: Built-in rate limiting helps avoid bans
3. **Cache Results**: Save results to avoid re-scraping the same data
4. **Use Batch Operations**: More efficient for multiple items
5. **Filter Early**: Use search parameters to reduce data transfer
6. **Handle Errors**: Implement proper error handling in your code
7. **Monitor Usage**: Track API quotas to avoid hitting limits

## 🚀 Getting Help

If you encounter issues or have questions:

1. Check the relevant scraper guide in `docs/`
2. Review the [Troubleshooting](#troubleshooting) section
3. Search existing [GitHub Issues](https://github.com/CrazyDubya/research-scrapers/issues)
4. Create a new issue with detailed information
5. Join the [Discussions](https://github.com/CrazyDubya/research-scrapers/discussions)

---

**Happy Scraping! 🕷️📊**
