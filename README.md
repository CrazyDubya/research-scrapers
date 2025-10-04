# Research Scrapers

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A comprehensive toolkit for scraping and analyzing data from various research sources. This package provides a robust, extensible framework for web scraping with built-in rate limiting, error handling, and support for both static and JavaScript-heavy websites.

## 🎆 Features

- **Multiple Scraping Engines**: Support for both requests/BeautifulSoup and Selenium
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

### Selenium for JavaScript Sites

```python
from research_scrapers.scraper import SeleniumScraper

# Create Selenium scraper
scraper = SeleniumScraper(browser='chrome', headless=True)

# Scrape JavaScript-heavy site
result = scraper.scrape(
    'https://spa-example.com',
    wait_for_element='.dynamic-content',
    selector='.data-item'
)

scraper.close()
```

## 📁 Project Structure

```
research-scrapers/
├── src/
│   └── research_scrapers/
│       ├── __init__.py
│       ├── scraper.py          # Core scraping classes
│       ├── utils.py            # Utility functions
│       └── config.py           # Configuration management
├── tests/
│   ├── test_scraper.py
│   ├── test_utils.py
│   └── test_config.py
├── docs/
│   ├── getting-started.md
│   ├── api-reference.md
│   └── configuration.md
├── scripts/
│   ├── example_basic_scraping.py
│   ├── example_selenium_scraping.py
│   ├── example_batch_scraping.py
│   └── setup.py
├── requirements.txt
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
```

### Configuration File

```json
{
  "request_timeout": 45,
  "rate_limit": 1.5,
  "log_level": "INFO",
  "api_keys": {
    "github": "your_github_token"
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
```

## 📚 Examples

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
pytest tests/test_scraper.py -v
```

### Code Quality

```bash
# Format code
black src/ tests/ scripts/

# Lint code
flake8 src/ tests/ scripts/

# Type checking
mypy src/research_scrapers/
```

## 📝 Documentation

Comprehensive documentation is available in the `docs/` directory:

- [Getting Started](docs/getting-started.md) - Installation and basic usage
- [Configuration](docs/configuration.md) - Detailed configuration options
- [API Reference](docs/api-reference.md) - Complete API documentation
- [Examples](docs/examples/) - Advanced usage examples

## 🔍 Key Components

### Core Classes

- **`BaseScraper`**: Abstract base class for all scrapers
- **`WebScraper`**: HTTP-based scraper using requests and BeautifulSoup
- **`SeleniumScraper`**: Browser-based scraper for JavaScript sites
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

## 🔄 Workflow Examples

### Research Paper Collection

```python
# Scrape academic paper metadata
from research_scrapers import WebScraper

scraper = WebScraper()
papers = []

for url in paper_urls:
    result = scraper.scrape(url, selector='.paper-title, .abstract')
    papers.append({
        'title': result['selected_content'][0],
        'abstract': result['selected_content'][1],
        'url': url
    })

save_to_json(papers, 'research_papers.json')
```

### Social Media Analysis

```python
# Scrape social media posts (with proper authentication)
from research_scrapers.scraper import SeleniumScraper

scraper = SeleniumScraper(headless=True)
posts = []

for hashtag in hashtags:
    result = scraper.scrape(
        f'https://example-social.com/hashtag/{hashtag}',
        selector='.post-content',
        wait_for_element='.posts-loaded'
    )
    posts.extend(result['selected_content'])

save_to_json(posts, f'social_posts_{hashtag}.json')
```

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

2. **Rate limiting too aggressive**
   ```python
   config.RATE_LIMIT = 0.5  # Slower rate
   ```

3. **JavaScript not loading**
   ```python
   # Use Selenium with explicit waits
   scraper = SeleniumScraper()
   result = scraper.scrape(url, wait_for_element='.content')
   ```

4. **Memory issues with large datasets**
   ```python
   # Process in smaller batches
   batches = batch_process(urls, batch_size=10)
   ```

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

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [requests](https://requests.readthedocs.io/) and [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/)
- Selenium integration for JavaScript support
- Inspired by the research community's need for reliable data collection tools

## 📞 Support

For questions, issues, or feature requests:

- 🐛 [Report bugs](https://github.com/CrazyDubya/research-scrapers/issues)
- 💡 [Request features](https://github.com/CrazyDubya/research-scrapers/issues)
- 💬 [Discussions](https://github.com/CrazyDubya/research-scrapers/discussions)

---

**Happy Scraping! 🕷️📊**
