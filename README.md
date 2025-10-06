# Research Scrapers

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A comprehensive toolkit for scraping and analyzing data from various research and project management sources. This package provides a robust, extensible framework for web scraping with built-in rate limiting, error handling, and support for both static and JavaScript-heavy websites.

## 🎯 What's New

### 📚 ArXiv Research Paper Scraper
**NEW**: Comprehensive ArXiv scraper with advanced features:
- ArXiv API integration with XML parsing
- Search by categories, authors, date ranges, keywords
- PDF download and full-text extraction
- Batch operations with concurrent processing
- Multiple output formats (JSON, CSV, XML)
- Rate limiting per ArXiv guidelines

### 💡 Stack Overflow Scraper
**NEW**: Production-ready Stack Overflow scraper:
- Stack Overflow API integration with comprehensive search
- Question and answer extraction with metadata
- User profile and reputation tracking
- Tag-based filtering and advanced search queries
- Rate limiting per Stack Overflow API guidelines
- Export to multiple formats with rich metadata

### 📋 Patent Database Scraper
**NEW**: Comprehensive patent research tool:
- USPTO Patent API integration
- Google Patents scraper with BeautifulSoup parsing
- Search by inventors, assignees, CPC codes, keywords
- Patent metadata extraction (claims, citations, legal status)
- Date range filtering and patent family tracking
- Full-text patent content extraction

### 🚀 Linear Integration Coming Soon (RUB-50)
We're actively developing a comprehensive Linear API integration to enable seamless project management workflows. This will include:
- Issue and project data extraction from Linear workspaces
- Synchronization between Linear, GitHub, and other platforms
- Automated workflow management and analytics
- **Track Progress**: [Linear Project RUB-50](https://linear.app/rubberducky/issue/RUB-50)

### 📚 Enhanced Documentation
- **Roadmap**: See our [ROADMAP.md](ROADMAP.md) for planned features and timeline
- **Notion Documentation**: Comprehensive planning and architecture docs available in our Notion workspace
- **Integration Guides**: Detailed guides for platform integrations and workflows

## 🎆 Features

- **Multiple Scraping Engines**: Support for both requests/BeautifulSoup and Selenium
- **GitHub Integration**: Production-ready GitHub API scraper with full feature support
- **ArXiv Integration**: Comprehensive ArXiv research paper scraper with PDF processing
- **Stack Overflow Integration**: Complete Stack Overflow API scraper with Q&A extraction
- **Patent Integration**: USPTO and Google Patents scraper with comprehensive search
- **Linear Integration**: *Coming Soon* - Comprehensive Linear API integration (RUB-50)
- **Rate Limiting**: Built-in rate limiting to respect website policies
- **Error Handling**: Robust retry mechanisms with exponential backoff
- **Configuration Management**: Flexible configuration via files, environment variables, or code
- **Async Support**: Asynchronous scraping capabilities for high-performance scenarios
- **Data Processing**: Utilities for cleaning, validating, and processing scraped data
- **Extensible Architecture**: Easy to extend with custom scrapers for specific sites
- **Comprehensive Logging**: Detailed logging for debugging and monitoring
- **Testing Suite**: Full test coverage with pytest

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/CrazyDubya/research-scrapers.git
cd research-scrapers

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### Basic Usage

```python
from research_scrapers import WebScraper, Config
from research_scrapers.utils import setup_logging, save_to_json

# Setup logging
setup_logging(level='INFO')

# Create and configure scraper
config = Config()
config.RATE_LIMIT = 1.0  # 1 request per second
scraper = WebScraper(config)

# Scrape a webpage
result = scraper.scrape('https://example.com')

# Save results
save_to_json(result, 'output/scraped_data.json')

# Clean up
scraper.close()
```

## 📚 ArXiv Research Paper Scraper

The ArXiv scraper provides comprehensive access to ArXiv research papers with advanced search capabilities, PDF processing, and text extraction.

### Features

- **ArXiv API Integration**: Native XML parsing of ArXiv API responses
- **Advanced Search**: Search by categories, authors, keywords, date ranges
- **PDF Processing**: Multiple PDF engines (pdfplumber, PyPDF2, pdfminer)
- **Text Extraction**: Full-text extraction from research papers
- **Batch Operations**: Concurrent processing of multiple papers
- **Rate Limiting**: Complies with ArXiv's 3-second rate limit guidelines
- **Multiple Formats**: Export to JSON, CSV, XML

### Quick Start

```bash
# Search for machine learning papers
python arxiv_scraper.py --query "machine learning" --max-results 50

# Search by category with full content
python arxiv_scraper.py --categories cs.AI cs.LG --include-pdf --include-full-text

# Get specific paper
python arxiv_scraper.py --paper-id 2301.07041 --include-full-text

# Recent papers in AI
python arxiv_scraper.py --recent-days 7 --categories cs.AI --max-results 100
```

### Programming Interface

```python
from arxiv_scraper import ArxivScraper, ArxivSearchOptions

# Initialize scraper
scraper = ArxivScraper()

# Create search options
options = ArxivSearchOptions(
    query="deep learning",
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
    print(f"Categories: {', '.join(paper.categories)}")
    if paper.full_text:
        print(f"Full text length: {len(paper.full_text)} characters")
```

See the [ArXiv Scraper Guide](docs/ARXIV_SCRAPER_GUIDE.md) for complete documentation.

## 💡 Stack Overflow Scraper

The Stack Overflow scraper provides comprehensive access to Stack Overflow data through the official API, enabling research and analysis of programming Q&A content.

### Features

- **Stack Overflow API Integration**: Official API with authentication support
- **Comprehensive Search**: Questions, answers, users, tags, and comments
- **Advanced Filtering**: By tags, date ranges, scores, activity
- **User Analytics**: Reputation tracking, badge analysis, activity patterns
- **Content Extraction**: Full question/answer text with formatting preservation
- **Rate Limiting**: Respects Stack Overflow API quotas and guidelines
- **Rich Metadata**: Vote counts, view counts, accepted answers, user profiles

### Quick Start

```bash
# Search questions by tags
python stackoverflow_scraper.py --tags python machine-learning --max-results 100

# Search by keywords
python stackoverflow_scraper.py --query "neural networks" --sort activity --max-results 50

# Get user information
python stackoverflow_scraper.py --user-ids 12345 67890 --include-user-details

# Search recent questions
python stackoverflow_scraper.py --recent-days 7 --tags python --min-score 5

# Export to CSV
python stackoverflow_scraper.py --tags javascript --format csv --output js_questions.csv
```

### Programming Interface

```python
from research_scrapers.stackoverflow_scraper import StackOverflowScraper, ScrapingOptions

# Initialize scraper (API key optional but recommended)
scraper = StackOverflowScraper(api_key="your_api_key")

# Create search options
options = ScrapingOptions(
    tags=["python", "machine-learning"],
    max_results=100,
    include_answers=True,
    include_comments=True,
    min_score=5
)

# Search questions
questions = scraper.search_questions(options)

# Process results
for question in questions:
    print(f"Title: {question.title}")
    print(f"Score: {question.score}")
    print(f"Tags: {', '.join(question.tags)}")
    print(f"Answers: {len(question.answers)}")
```

See the [Stack Overflow Scraper Guide](docs/STACKOVERFLOW_SCRAPER.md) for complete documentation.

## 📋 Patent Database Scraper

The Patent scraper provides unified access to multiple patent databases including USPTO and Google Patents for comprehensive patent research and analysis.

### Features

- **USPTO Patent API Integration**: Official USPTO API with full search capabilities
- **Google Patents Scraper**: BeautifulSoup-based scraper for additional coverage
- **Advanced Search**: By keywords, inventors, assignees, CPC codes, date ranges
- **Patent Metadata**: Number, title, abstract, claims, citations, legal status
- **Classification Support**: CPC, IPC, and USPC classification systems
- **Full-text Extraction**: Complete patent content including claims and descriptions
- **Patent Family Tracking**: Related patents and citation networks
- **Rate Limiting**: Complies with USPTO API guidelines

### Quick Start

```bash
# Search patents by keyword
python patent_scraper.py --keywords "machine learning" --max-results 50

# Search by inventor
python patent_scraper.py --inventors "John Smith" --max-results 100

# Search by assignee/company
python patent_scraper.py --assignees "Google" --include-full-text --max-results 50

# Search by CPC classification
python patent_scraper.py --cpc-codes "G06F" --recent-days 30

# Get specific patent
python patent_scraper.py --patent-number US10123456B2 --include-claims --include-citations

# Batch retrieve patents
python patent_scraper.py --patent-numbers US10123456 US10234567 --include-full-text
```

### Programming Interface

```python
from research_scrapers.patent_scraper import PatentScraper, PatentSearchOptions

# Initialize scraper
scraper = PatentScraper()

# Create search options
options = PatentSearchOptions(
    keywords=["artificial intelligence"],
    assignees=["Google"],
    max_results=100,
    include_full_text=True,
    include_claims=True,
    include_citations=True
)

# Search patents
patents = scraper.scrape(options)

# Process results
for patent in patents:
    print(f"Patent: {patent.patent_number}")
    print(f"Title: {patent.title}")
    print(f"Inventors: {', '.join(patent.inventors)}")
    print(f"Assignees: {', '.join(patent.assignees)}")
    if patent.claims:
        print(f"Claims: {len(patent.claims)}")
```

See the [Patent Scraper Guide](docs/PATENT_SCRAPER_GUIDE.md) for complete documentation.

## 🐙 GitHub Scraper

The `GitHubScraper` class provides a comprehensive, production-ready interface for scraping GitHub data using the GitHub REST API. It includes automatic rate limiting, pagination, error handling, and support for all major GitHub resources.

### Features

- **Authentication**: Automatic token detection from environment variables
- **Rate Limiting**: Respects GitHub API rate limits (5000/hr authenticated, 60/hr unauthenticated)
- **Pagination**: Automatic pagination handling for all list endpoints
- **Error Handling**: Comprehensive error handling with exponential backoff retry logic
- **Data Validation**: Built-in validation for GitHub data structures
- **Context Manager**: Supports Python context manager protocol for automatic cleanup

### Quick Start

```python
from research_scrapers import GitHubScraper

# Initialize with token (or uses GITHUB_TOKEN env var)
scraper = GitHubScraper(token="ghp_your_token_here")

# Or use as context manager
with GitHubScraper() as scraper:
    # Scrape repository
    repo_data = scraper.scrape_repository("facebook", "react")
    print(f"Stars: {repo_data['stargazers_count']}")
    
    # Scrape user
    user_data = scraper.scrape_user("torvalds")
    print(f"Followers: {user_data['followers']}")
```

## 🔮 Linear Integration (Coming Soon)

We're developing a comprehensive Linear API integration as part of project **RUB-50**. This will enable:

### Planned Features
- **Issue Management**: Extract and manage Linear issues, sub-issues, and projects
- **Team Analytics**: Analyze team performance and project metrics
- **Cross-Platform Sync**: Synchronize data between Linear, GitHub, and other platforms
- **Workflow Automation**: Automate project management workflows
- **Real-time Updates**: Webhook support for live data synchronization

### Preview Usage
```python
# Coming soon in v2.0
from research_scrapers import LinearScraper

scraper = LinearScraper(api_key="lin_api_xxx")

# Get team issues
issues = scraper.scrape_issues(team_key="RUB", state="active")

# Sync with GitHub
scraper.sync_to_github("CrazyDubya/research-scrapers")
```

**Track Progress**: [RUB-50 Linear Integration](https://linear.app/rubberducky/issue/RUB-50)

## 📁 Project Structure

```
research-scrapers/
├── arxiv_scraper.py           # ArXiv research paper scraper
├── stackoverflow_scraper.py   # Stack Overflow Q&A scraper
├── patent_scraper.py          # Patent database scraper
├── github_repo_scraper.py     # GitHub repository scraper
├── github_issue_scraper.py    # GitHub issues scraper
├── github_user_scraper.py     # GitHub user scraper
├── utils.py                   # Utility functions and classes
├── config.py                  # Configuration management
├── src/
│   └── research_scrapers/
│       ├── __init__.py
│       ├── scraper.py          # Core scraping classes
│       ├── github_scraper.py   # GitHub API scraper
│       ├── stackoverflow_scraper.py  # Stack Overflow API scraper
│       ├── patent_scraper.py   # Patent database scraper
│       ├── linear/             # Linear integration (coming soon)
│       ├── utils.py            # Utility functions
│       └── config.py           # Configuration management
├── tests/
│   ├── test_scraper.py
│   ├── test_github_scraper.py  # GitHub scraper tests
│   ├── test_arxiv_scraper.py   # ArXiv scraper tests
│   ├── test_stackoverflow_scraper.py  # Stack Overflow scraper tests
│   ├── test_patent_scraper.py  # Patent scraper tests
│   ├── test_utils.py
│   └── test_config.py
├── docs/
│   ├── getting-started.md
│   ├── ARXIV_SCRAPER_GUIDE.md  # Comprehensive ArXiv documentation
│   ├── STACKOVERFLOW_SCRAPER.md  # Stack Overflow scraper guide
│   ├── PATENT_SCRAPER_GUIDE.md   # Patent scraper guide
│   ├── api-reference.md
│   ├── configuration.md
│   ├── INTEGRATION_GUIDE.md    # Platform integration guide
│   ├── API_ARCHITECTURE.md     # System architecture
│   └── SECURITY_ARCHITECTURE.md
├── scripts/
│   ├── example_basic_scraping.py
│   ├── example_selenium_scraping.py
│   ├── example_batch_scraping.py
│   └── setup.py
├── requirements.txt
├── requirements-linear.txt     # Linear integration dependencies
├── ROADMAP.md                  # Project roadmap and planned features
├── setup.py
├── .gitignore
└── README.md
```

## 🔧 Configuration

The package supports multiple configuration methods:

### Environment Variables

```bash
export SCRAPER_REQUEST_TIMEOUT=60
export SCRAPER_RATE_LIMIT=2.0
export SCRAPER_LOG_LEVEL=DEBUG
export GITHUB_API_KEY=your_token_here
export STACKOVERFLOW_API_KEY=your_so_token
export LINEAR_API_KEY=your_linear_token  # Coming soon
```

### Configuration File

```json
{
  "request_timeout": 45,
  "rate_limit": 1.5,
  "log_level": "INFO",
  "api_keys": {
    "github": "your_github_token",
    "stackoverflow": "your_so_token",
    "linear": "your_linear_token"
  }
}
```

### Programmatic Configuration

```python
from research_scrapers import Config

config = Config()
config.REQUEST_TIMEOUT = 60
config.RATE_LIMIT = 2.0
config.set_api_key('github', 'your_token')
config.set_api_key('stackoverflow', 'your_so_token')
config.set_api_key('linear', 'your_linear_token')  # Coming soon
```

## 📚 Examples

### Research Workflow Examples

```python
# Daily research update workflow
from arxiv_scraper import ArxivScraper, ArxivSearchOptions
from research_scrapers.stackoverflow_scraper import StackOverflowScraper, ScrapingOptions

def daily_research_update():
    # Get recent ArXiv papers
    arxiv_scraper = ArxivScraper()
    papers = arxiv_scraper.search_recent_papers(
        days=1,
        categories=["cs.AI", "cs.LG", "cs.CV"],
        max_results=50
    )
    
    # Get trending Stack Overflow questions
    so_scraper = StackOverflowScraper()
    so_options = ScrapingOptions(
        tags=["machine-learning", "deep-learning"],
        sort="activity",
        max_results=20
    )
    questions = so_scraper.search_questions(so_options)
    
    return papers, questions
```

### Patent Research Workflow

```python
# Comprehensive patent landscape analysis
from research_scrapers.patent_scraper import PatentScraper, PatentSearchOptions

def patent_landscape_analysis(technology_area, company_list):
    scraper = PatentScraper()
    
    all_patents = []
    
    # Search by technology keywords
    tech_options = PatentSearchOptions(
        keywords=[technology_area],
        max_results=500,
        include_citations=True,
        start_date="2020-01-01"
    )
    tech_patents = scraper.scrape(tech_options)
    all_patents.extend(tech_patents)
    
    # Search by key companies
    for company in company_list:
        company_options = PatentSearchOptions(
            assignees=[company],
            keywords=[technology_area],
            max_results=200,
            include_full_text=True
        )
        company_patents = scraper.scrape(company_options)
        all_patents.extend(company_patents)
    
    return all_patents
```

### Cross-Platform Research

```python
# Multi-platform research aggregation
def comprehensive_research(topic):
    results = {}
    
    # ArXiv papers
    arxiv_scraper = ArxivScraper()
    arxiv_options = ArxivSearchOptions(
        query=topic,
        max_results=100,
        include_full_text=True
    )
    results['papers'] = arxiv_scraper.search_papers(arxiv_options)
    
    # Stack Overflow discussions
    so_scraper = StackOverflowScraper()
    so_options = ScrapingOptions(
        query=topic,
        max_results=50,
        include_answers=True
    )
    results['discussions'] = so_scraper.search_questions(so_options)
    
    # Patents
    patent_scraper = PatentScraper()
    patent_options = PatentSearchOptions(
        keywords=[topic],
        max_results=100,
        include_claims=True
    )
    results['patents'] = patent_scraper.scrape(patent_options)
    
    return results
```

## 🛠️ Development Setup

For development, use the provided setup script:

```bash
# Run the development setup
python scripts/setup.py
```

This will:
- Check Python version compatibility
- Install dependencies
- Create necessary directories
- Set up pre-commit hooks
- Create example configuration files
- Run the test suite

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=research_scrapers --cov-report=html

# Run specific test files
pytest tests/test_arxiv_scraper.py -v
pytest tests/test_stackoverflow_scraper.py -v
pytest tests/test_patent_scraper.py -v
```

### Code Quality

```bash
# Format code
black src/ tests/ scripts/ *.py

# Lint code
flake8 src/ tests/ scripts/ *.py

# Type checking
mypy src/research_scrapers/ *.py
```

## 📝 Documentation

Comprehensive documentation is available in the `docs/` directory:

- [Getting Started](docs/getting-started.md) - Installation and basic usage
- [ArXiv Scraper Guide](docs/ARXIV_SCRAPER_GUIDE.md) - Complete ArXiv scraper documentation
- [Stack Overflow Scraper Guide](docs/STACKOVERFLOW_SCRAPER.md) - Stack Overflow API integration
- [Patent Scraper Guide](docs/PATENT_SCRAPER_GUIDE.md) - Patent database scraping
- [Configuration](docs/configuration.md) - Detailed configuration options
- [Integration Guide](docs/INTEGRATION_GUIDE.md) - Platform integration patterns
- [API Architecture](docs/API_ARCHITECTURE.md) - System design and architecture
- [Security Architecture](docs/SECURITY_ARCHITECTURE.md) - Security best practices
- [Roadmap](ROADMAP.md) - Planned features and timeline

### External Documentation

- **Notion Workspace**: Comprehensive project planning, requirements, and architecture documentation
- **Linear Project**: [RUB-50](https://linear.app/rubberducky/issue/RUB-50) - Track Linear integration progress

## 🔍 Key Components

### Core Classes

- **`BaseScraper`**: Abstract base class for all scrapers
- **`WebScraper`**: HTTP-based scraper using requests and BeautifulSoup
- **`SeleniumScraper`**: Browser-based scraper for JavaScript sites
- **`GitHubScraper`**: Production-ready GitHub API integration
- **`ArxivScraper`**: Comprehensive ArXiv research paper scraper
- **`StackOverflowScraper`**: Stack Overflow API scraper with Q&A extraction
- **`PatentScraper`**: Multi-source patent database scraper
- **`LinearScraper`**: *Coming Soon* - Linear API integration (RUB-50)
- **`Config`**: Configuration management with multiple sources

### Utilities

- **Rate Limiting**: `@rate_limit` decorator
- **Retry Logic**: `@retry_on_failure` decorator
- **Text Processing**: `clean_text()` function
- **File Operations**: `save_to_json()`, `load_from_json()`
- **URL Validation**: `validate_url()`, `extract_domain()`
- **Batch Processing**: `batch_process()` function

### Features

- ✅ **Rate Limiting**: Configurable requests per second
- ✅ **Error Handling**: Automatic retries with exponential backoff
- ✅ **User Agent Rotation**: Customizable user agent strings
- ✅ **Proxy Support**: HTTP/HTTPS proxy configuration
- ✅ **Content Filtering**: MIME type and size validation
- ✅ **Logging**: Comprehensive logging with multiple levels
- ✅ **Configuration**: Environment variables, files, and programmatic
- ✅ **Testing**: Full test suite with mocking
- ✅ **ArXiv Integration**: Complete research paper scraping
- ✅ **Stack Overflow Integration**: Q&A and user data extraction
- ✅ **Patent Integration**: USPTO and Google Patents scraping
- 🚧 **Linear Integration**: In development (RUB-50)

## 🔒 Security & Ethics

- **Respect robots.txt**: Always check and respect website policies
- **Rate Limiting**: Built-in rate limiting to avoid overwhelming servers
- **User Agent**: Identify your scraper appropriately
- **Terms of Service**: Ensure compliance with website terms
- **Data Privacy**: Handle personal data responsibly
- **API First**: Use official APIs when available

## 📊 Performance Tips

1. **Use appropriate scraper**: HTTP for static content, Selenium for JavaScript
2. **Configure rate limits**: Balance speed with server respect
3. **Batch processing**: Process URLs in batches for efficiency
4. **Caching**: Implement caching for repeated requests
5. **Async operations**: Use async scrapers for high-volume tasks
6. **Resource cleanup**: Always close scrapers and sessions

## 🐛 Troubleshooting

### Common Issues

1. **API Key Issues**
   ```bash
   # Set environment variables
   export STACKOVERFLOW_API_KEY=your_key_here
   export GITHUB_TOKEN=your_token_here
   ```

2. **PDF processing libraries missing**
   ```bash
   pip install PyPDF2 pdfplumber pdfminer.six
   ```

3. **Rate limiting too aggressive**
   ```python
   config.RATE_LIMIT = 0.5  # Slower rate
   ```

4. **Memory issues with large datasets**
   ```python
   # Process in smaller batches
   batches = batch_process(urls, batch_size=10)
   ```

## 🗺️ Roadmap & Future Plans

See our comprehensive [ROADMAP.md](ROADMAP.md) for detailed information about:

- **Linear Integration (RUB-50)**: Timeline, features, and implementation details
- **Notion API Integration**: Planned for Q3 2025
- **Additional Platform Integrations**: Jira, GitLab, Confluence
- **Performance Enhancements**: Async support, caching improvements
- **Developer Experience**: CLI tools, VS Code extension, Docker support

**Key Milestones:**
- **Q1 2025**: Linear integration core features
- **Q2 2025**: GitHub-Linear synchronization
- **Q3 2025**: Notion integration and web dashboard
- **Q4 2025**: Enterprise features and plugin architecture

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](docs/contributing.md) for guidelines.

### Development Workflow

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

### Code Standards

- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Write comprehensive docstrings
- Add tests for new features
- Update documentation as needed

### Project Tracking

- **Linear Project**: [RUB-50](https://linear.app/rubberducky/issue/RUB-50) for Linear integration
- **GitHub Issues**: For bug reports and feature requests
- **Notion Workspace**: For detailed planning and architecture docs

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [requests](https://requests.readthedocs.io/) and [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/)
- Selenium integration for JavaScript support
- ArXiv API for research paper access
- Stack Overflow API for Q&A data
- USPTO Patent API for patent data
- PDF processing libraries: PyPDF2, pdfplumber, pdfminer
- Inspired by the research community's need for reliable data collection tools

## 📞 Support

For questions, issues, or feature requests:

- 🐛 [Report bugs](https://github.com/CrazyDubya/research-scrapers/issues)
- 💡 [Request features](https://github.com/CrazyDubya/research-scrapers/issues)
- 💬 [Discussions](https://github.com/CrazyDubya/research-scrapers/discussions)
- 📋 [Linear Project Board](https://linear.app/rubberducky/project/rub-50) - Track development progress
- 📚 **Notion Documentation** - Request access for detailed project docs

---

**Happy Scraping! 🕷️📊**