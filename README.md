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

### Advanced Examples

```bash
# Search with author and date filters
python arxiv_scraper.py --query "quantum computing" --authors "John Preskill" \
  --start-date 2023-01-01 --end-date 2023-12-31

# Batch download specific papers
python arxiv_scraper.py --paper-ids 2301.07041 2302.12345 2303.56789 \
  --include-pdf --extract-references

# Export to different formats
python arxiv_scraper.py --query "neural networks" --format csv --output results.csv

# Show available categories
python arxiv_scraper.py --show-categories
```

### ArXiv Categories

The scraper supports all ArXiv categories including:

- **Computer Science**: `cs.AI` (Artificial Intelligence), `cs.LG` (Machine Learning), `cs.CV` (Computer Vision)
- **Physics**: `quant-ph` (Quantum Physics), `cond-mat` (Condensed Matter), `astro-ph` (Astrophysics)
- **Mathematics**: `math.AG` (Algebraic Geometry), `math.NT` (Number Theory)
- **Other Fields**: `q-bio` (Quantitative Biology), `q-fin` (Quantitative Finance), `stat` (Statistics)

See the [ArXiv Scraper Guide](docs/ARXIV_SCRAPER_GUIDE.md) for complete documentation.

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

### Examples

#### Repository Scraping

```python
from research_scrapers import GitHubScraper

scraper = GitHubScraper()

# Get repository details
repo = scraper.scrape_repository("microsoft", "vscode")

print(f"Repository: {repo['full_name']}")
print(f"Description: {repo['description']}")
print(f"Stars: {repo['stargazers_count']}")
print(f"Forks: {repo['forks_count']}")
print(f"Language: {repo['language']}")
print(f"License: {repo['license']['name'] if repo['license'] else 'None'}")
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
│       ├── linear/             # Linear integration (coming soon)
│       ├── utils.py            # Utility functions
│       └── config.py           # Configuration management
├── tests/
│   ├── test_scraper.py
│   ├── test_github_scraper.py  # GitHub scraper tests
│   ├── test_arxiv_scraper.py   # ArXiv scraper tests
│   ├── test_utils.py
│   └── test_config.py
├── docs/
│   ├── getting-started.md
│   ├── ARXIV_SCRAPER_GUIDE.md  # Comprehensive ArXiv documentation
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
config.set_api_key('linear', 'your_linear_token')  # Coming soon
```

## 📚 Examples

### ArXiv Research Workflow

```python
# Daily research update workflow
from arxiv_scraper import ArxivScraper, ArxivSearchOptions

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
    
    return relevant_papers
```

### Literature Review

```python
# Comprehensive literature review
def literature_review(topic, start_year=2020):
    scraper = ArxivScraper()
    
    options = ArxivSearchOptions(
        query=topic,
        start_date=f"{start_year}-01-01",
        max_results=200,
        include_pdf=True,
        include_full_text=True,
        extract_references=True
    )
    
    papers = scraper.search_papers(options)
    return papers
```

### Basic Web Scraping

```python
# Run the basic scraping example
python scripts/example_basic_scraping.py
```

### Batch Processing

```python
# Run batch scraping with multiple URLs
python scripts/example_batch_scraping.py
```

### Selenium Scraping

```python
# Scrape JavaScript-heavy sites
python scripts/example_selenium_scraping.py
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

# Run specific test file
pytest tests/test_arxiv_scraper.py -v
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

1. **Selenium WebDriver not found**
   ```bash
   pip install webdriver-manager
   ```

2. **PDF processing libraries missing**
   ```bash
   pip install PyPDF2 pdfplumber pdfminer.six
   ```

3. **Rate limiting too aggressive**
   ```python
   config.RATE_LIMIT = 0.5  # Slower rate
   ```

4. **JavaScript not loading**
   ```python
   # Use Selenium with explicit waits
   scraper = SeleniumScraper()
   result = scraper.scrape(url, wait_for_element='.content')
   ```

5. **Memory issues with large datasets**
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