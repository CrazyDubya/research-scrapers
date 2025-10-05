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

#### User Profile Scraping

```python
# Get user profile
user = scraper.scrape_user("guido")

print(f"Name: {user['name']}")
print(f"Bio: {user['bio']}")
print(f"Public Repos: {user['public_repos']}")
print(f"Followers: {user['followers']}")
print(f"Following: {user['following']}")
```

#### Organization Scraping

```python
# Get organization with repositories
org = scraper.scrape_organization("google")

print(f"Organization: {org['name']}")
print(f"Description: {org['description']}")
print(f"Public Repos: {org['public_repos']}")
print(f"Repositories: {len(org['repositories'])}")

# List first 5 repositories
for repo in org['repositories'][:5]:
    print(f"  - {repo['name']}: {repo['stargazers_count']} stars")
```

#### Issues and Pull Requests

```python
# Get issues
issues = scraper.scrape_issues(
    "facebook", 
    "react", 
    state="open",  # 'open', 'closed', or 'all'
    limit=50
)

print(f"Found {len(issues)} open issues")
for issue in issues[:5]:
    print(f"#{issue['number']}: {issue['title']}")

# Get pull requests
prs = scraper.scrape_pull_requests(
    "microsoft", 
    "vscode", 
    state="closed",
    limit=100
)

print(f"Found {len(prs)} closed pull requests")
```

#### Search Functionality

```python
# Search repositories
repos = scraper.search_repositories(
    "machine learning language:python stars:>1000",
    sort="stars",  # 'stars', 'forks', 'updated', or 'help-wanted-issues'
    limit=50
)

for repo in repos[:10]:
    print(f"{repo['full_name']}: {repo['stargazers_count']} stars")

# Search users
users = scraper.search_users(
    "location:seattle followers:>100",
    limit=30
)

for user in users:
    print(f"{user['login']}: {user.get('followers', 0)} followers")

# Search code
code_results = scraper.search_code(
    "def scrape_repository language:python",
    limit=30
)

for result in code_results:
    print(f"{result['repository']['full_name']}: {result['path']}")
```

#### Rate Limit Management

```python
# Check rate limit status
status = scraper.get_rate_limit_status()

core_limits = status['resources']['core']
print(f"Rate Limit: {core_limits['remaining']}/{core_limits['limit']}")
print(f"Resets at: {core_limits['reset']}")

search_limits = status['resources']['search']
print(f"Search Rate Limit: {search_limits['remaining']}/{search_limits['limit']}")
```

#### Saving Data

```python
# Scrape and save data
repo_data = scraper.scrape_repository("pytorch", "pytorch")

# Save to JSON file
output_path = scraper.save_data(
    repo_data, 
    filename="pytorch_data.json",
    output_dir="./output"
)

print(f"Data saved to: {output_path}")
```

#### Advanced Usage

```python
from research_scrapers import GitHubScraper
from pathlib import Path

# Enable caching for repeated requests
scraper = GitHubScraper(
    token="ghp_your_token",
    enable_caching=True
)

# Batch scrape multiple repositories
repos_to_scrape = [
    ("facebook", "react"),
    ("vuejs", "vue"),
    ("angular", "angular"),
]

results = []
for owner, repo in repos_to_scrape:
    try:
        data = scraper.scrape_repository(owner, repo)
        results.append(data)
        print(f"✓ Scraped {owner}/{repo}")
    except Exception as e:
        print(f"✗ Failed to scrape {owner}/{repo}: {e}")

# Save all results
scraper.save_data(results, "frameworks_comparison.json")

# Always close the scraper when done
scraper.close()
```

### Authentication

The scraper supports multiple authentication methods:

1. **Direct token parameter**:
   ```python
   scraper = GitHubScraper(token="ghp_your_token_here")
   ```

2. **Environment variable**:
   ```bash
   export GITHUB_TOKEN="ghp_your_token_here"
   ```
   ```python
   scraper = GitHubScraper()  # Automatically uses GITHUB_TOKEN
   ```

3. **No authentication** (limited to 60 requests/hour):
   ```python
   scraper = GitHubScraper()  # Works without token but with lower rate limits
   ```

### Error Handling

The scraper includes comprehensive error handling:

```python
from research_scrapers import GitHubScraper
from utils import APIError, RateLimitError, ValidationError

scraper = GitHubScraper()

try:
    # This will raise APIError if repo doesn't exist
    repo = scraper.scrape_repository("nonexistent", "repo")
except APIError as e:
    print(f"API Error: {e}")
except RateLimitError as e:
    print(f"Rate limit exceeded: {e}")
except ValidationError as e:
    print(f"Data validation failed: {e}")
```

### Best Practices

1. **Use authentication** for higher rate limits (5000 vs 60 requests/hour)
2. **Use context manager** for automatic cleanup:
   ```python
   with GitHubScraper() as scraper:
       data = scraper.scrape_repository("owner", "repo")
   ```
3. **Monitor rate limits** with `get_rate_limit_status()`
4. **Handle errors gracefully** with try/except blocks
5. **Use pagination limits** to avoid excessive API calls
6. **Enable caching** for development/testing to reduce API calls

## 📁 Project Structure

```
research-scrapers/
├── src/
│   └── research_scrapers/
│       ├── __init__.py
│       ├── scraper.py          # Core scraping classes
│       ├── github_scraper.py   # GitHub API scraper
│       ├── utils.py            # Utility functions
│       └── config.py           # Configuration management
├── tests/
│   ├── test_scraper.py
│   ├── test_github_scraper.py  # GitHub scraper tests
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
