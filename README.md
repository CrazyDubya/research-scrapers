# Research Scrapers 🔍

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![GitHub Issues](https://img.shields.io/github/issues/CrazyDubya/research-scrapers)](https://github.com/CrazyDubya/research-scrapers/issues)
[![GitHub Stars](https://img.shields.io/github/stars/CrazyDubya/research-scrapers)](https://github.com/CrazyDubya/research-scrapers/stargazers)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A comprehensive Python toolkit for scraping GitHub data with robust rate limiting, error handling, and multiple output formats. Perfect for research, analytics, and data collection projects.

## 🚀 Features

- **🏢 Repository Analysis**: Complete repository metadata, statistics, commit history, and file structure
- **🐛 Issue & PR Tracking**: Issues, pull requests, discussions with comments and reviews
- **👥 User & Organization Profiles**: Comprehensive user data, activity, and social connections
- **⚡ Rate Limiting**: Intelligent rate limiting with automatic backoff
- **🛡️ Error Handling**: Robust error handling with retry mechanisms
- **📊 Multiple Formats**: JSON, CSV, and pickle output formats
- **🎯 Configurable**: Extensive configuration options for customized scraping
- **📈 Progress Tracking**: Real-time progress bars and detailed logging
- **🔧 CLI Interface**: User-friendly command-line interfaces for all scrapers

## 📦 Installation

### Prerequisites

- Python 3.8 or higher
- GitHub Personal Access Token (recommended for higher rate limits)

### Quick Install

```bash
# Clone the repository
git clone https://github.com/CrazyDubya/research-scrapers.git
cd research-scrapers

# Install dependencies
pip install -r requirements.txt

# Set up your GitHub token (optional but recommended)
export GITHUB_TOKEN="your_github_token_here"
```

### Dependencies

The toolkit uses several key libraries:

- **requests** & **PyGithub**: GitHub API interaction
- **pandas** & **numpy**: Data processing and analysis
- **click**: Command-line interface
- **tqdm**: Progress bars
- **ratelimit** & **backoff**: Rate limiting and retry logic

## 🎯 Quick Start

### Repository Scraping

```bash
# Basic repository scraping
python github_repo_scraper.py microsoft/vscode

# Include commits and issues (comprehensive)
python github_repo_scraper.py torvalds/linux --include-commits --include-issues

# Custom output file
python github_repo_scraper.py facebook/react --output react_analysis.json
```

### Issue & PR Scraping

```bash
# Scrape open issues
python github_issue_scraper.py microsoft/vscode --type issues --state open

# Scrape pull requests with reviews
python github_issue_scraper.py facebook/react --type pulls --max-items 50

# Filter by labels
python github_issue_scraper.py torvalds/linux --type issues --labels bug,regression
```

### User & Organization Scraping

```bash
# Scrape user profile and activity
python github_user_scraper.py torvalds

# Organization with members
python github_user_scraper.py microsoft --activity-days 7

# Multiple users
python github_user_scraper.py --multiple torvalds gvanrossum
```

## 📚 API Documentation

### GitHubRepoScraper

The main class for repository data extraction.

```python
from github_repo_scraper import GitHubRepoScraper, ScrapingOptions

# Initialize scraper
scraper = GitHubRepoScraper(token="your_token")

# Configure scraping options
options = ScrapingOptions(
    include_commits=True,
    include_issues=True,
    max_commits=200,
    max_issues=100,
    output_format='json'
)

# Scrape repository
data = scraper.scrape_repository("owner", "repo", options)
```

#### ScrapingOptions Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `include_metadata` | bool | True | Repository metadata and basic info |
| `include_statistics` | bool | True | Commit activity and code frequency |
| `include_commits` | bool | False | Commit history (can be large) |
| `include_contributors` | bool | True | Contributor information |
| `include_languages` | bool | True | Language breakdown |
| `include_topics` | bool | True | Repository topics |
| `include_releases` | bool | True | Release information |
| `include_issues` | bool | False | Issues data (can be large) |
| `include_pull_requests` | bool | False | Pull requests (can be large) |
| `include_file_tree` | bool | True | File structure analysis |
| `include_readme` | bool | True | README content |
| `include_license` | bool | True | License information |
| `max_commits` | int | 100 | Maximum commits to fetch |
| `max_contributors` | int | 100 | Maximum contributors to fetch |
| `max_releases` | int | 20 | Maximum releases to fetch |
| `file_tree_depth` | int | 5 | File tree traversal depth |

### GitHubIssueScraper

Specialized scraper for issues, pull requests, and discussions.

```python
from github_issue_scraper import GitHubIssueScraper

scraper = GitHubIssueScraper(token="your_token")

# Scrape issues with filters
issues_data = scraper.scrape_issues(
    owner="microsoft",
    repo="vscode",
    state="open",
    labels=["bug", "enhancement"],
    max_items=100,
    include_comments=True
)

# Scrape pull requests
pr_data = scraper.scrape_pull_requests(
    owner="facebook",
    repo="react",
    state="all",
    include_reviews=True
)
```

### GitHubUserScraper

Comprehensive user and organization data extraction.

```python
from github_user_scraper import GitHubUserScraper

scraper = GitHubUserScraper(token="your_token")

# Comprehensive user scraping
user_data = scraper.scrape_user_comprehensive(
    username="torvalds",
    include_activity=True,
    activity_days=30
)

# Get specific data
profile = scraper.get_user_profile("username")
repos = scraper.get_user_repositories("username")
followers = scraper.get_user_followers("username")
```

## ⚙️ Configuration

### Environment Variables

```bash
# GitHub API token (recommended)
export GITHUB_TOKEN="ghp_your_token_here"

# Logging level
export LOG_LEVEL="INFO"  # DEBUG, INFO, WARNING, ERROR
```

### Configuration File (config.py)

The `config.py` file contains extensive configuration options:

```python
# Rate limiting
DEFAULT_RATE_LIMIT = 1.0  # requests per second
AUTHENTICATED_RATE_LIMIT = 5.0  # with token

# Output settings
OUTPUT_DIR = Path('./output')
DEFAULT_OUTPUT_FORMAT = 'json'

# Scraping defaults
DEFAULT_MAX_COMMITS = 100
DEFAULT_MAX_ISSUES = 100
DEFAULT_PER_PAGE = 100

# Feature flags
SCRAPE_METADATA = True
SCRAPE_COMMITS = False  # Large datasets
ENABLE_CACHE = True
SHOW_PROGRESS = True
```

### Custom Configuration

```python
from config import *

# Override defaults
DEFAULT_MAX_COMMITS = 500
SCRAPE_COMMITS = True
OUTPUT_DIR = Path('./my_data')
```

## 🏗️ Architecture

### Core Components

```
research-scrapers/
├── github_repo_scraper.py     # Repository data scraping
├── github_issue_scraper.py    # Issues, PRs, discussions
├── github_user_scraper.py     # User and organization data
├── utils.py                   # Shared utilities and helpers
├── config.py                  # Configuration management
└── requirements.txt           # Dependencies
```

### Utility Functions (utils.py)

The `utils.py` module provides shared functionality:

- **RateLimiter**: Intelligent rate limiting with backoff
- **APIResponseProcessor**: Response validation and processing
- **DataFormatter**: Data cleaning and formatting
- **FileManager**: File I/O operations
- **DataValidator**: Input validation and sanitization

### Data Flow

```
Input (Repository/User) → API Requests → Rate Limiting → 
Data Processing → Validation → Output (JSON/CSV/Pickle)
```

## 🛠️ Advanced Usage

### Batch Processing

```python
# Process multiple repositories
repositories = [
    ("microsoft", "vscode"),
    ("facebook", "react"),
    ("google", "tensorflow")
]

for owner, repo in repositories:
    data = scraper.scrape_repository(owner, repo)
    # Process data...
```

### Custom Data Processing

```python
from utils import DataFormatter, FileManager

# Custom data transformation
def process_commits(commits_data):
    df = pd.DataFrame(commits_data)
    # Custom analysis...
    return df

# Save in multiple formats
FileManager.save_json(data, "output.json")
FileManager.save_csv(flattened_data, "output.csv")
```

### Error Handling

```python
from utils import ScrapingError, APIError

try:
    data = scraper.scrape_repository("owner", "repo")
except APIError as e:
    print(f"API Error: {e}")
except ScrapingError as e:
    print(f"Scraping Error: {e}")
```

## 🔧 Troubleshooting

### Common Issues

#### Rate Limiting
```bash
# Error: Rate limit exceeded
# Solution: Set GITHUB_TOKEN environment variable
export GITHUB_TOKEN="your_token"

# Or reduce rate in config.py
DEFAULT_RATE_LIMIT = 0.5  # Slower requests
```

#### Authentication Issues
```bash
# Error: 401 Unauthorized
# Check token validity
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user
```

#### Large Datasets
```bash
# For large repositories, disable heavy operations
python github_repo_scraper.py owner/repo --no-commits --no-issues --max-contributors 50
```

#### Memory Issues
```python
# Process data in chunks for large datasets
options = ScrapingOptions(
    max_commits=50,      # Reduce limits
    max_issues=25,
    include_file_tree=False  # Skip file tree for large repos
)
```

### Debug Mode

```bash
# Enable verbose logging
export LOG_LEVEL="DEBUG"
python github_repo_scraper.py owner/repo --verbose
```

### Performance Optimization

1. **Use Authentication**: Increases rate limits from 60 to 5000 requests/hour
2. **Selective Scraping**: Only enable needed data sections
3. **Caching**: Enable caching for repeated requests
4. **Batch Processing**: Process multiple items efficiently

## 🤝 Contributing

We welcome contributions! Here's how to get started:

### Development Setup

```bash
# Fork and clone the repository
git clone https://github.com/yourusername/research-scrapers.git
cd research-scrapers

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements.txt
pip install pytest pytest-cov black flake8

# Run tests
pytest tests/

# Format code
black *.py
```

### Contribution Guidelines

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Write** tests for new functionality
4. **Ensure** code passes all tests and linting
5. **Commit** changes (`git commit -m 'Add amazing feature'`)
6. **Push** to branch (`git push origin feature/amazing-feature`)
7. **Open** a Pull Request

### Code Style

- Follow PEP 8 guidelines
- Use type hints where possible
- Add docstrings for all functions and classes
- Write comprehensive tests

### Reporting Issues

Please use the [GitHub Issues](https://github.com/CrazyDubya/research-scrapers/issues) page to report bugs or request features. Include:

- Python version
- Operating system
- Error messages and stack traces
- Steps to reproduce

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **GitHub API**: For providing comprehensive data access
- **PyGithub**: Excellent Python GitHub API wrapper
- **Requests**: Reliable HTTP library
- **Click**: User-friendly CLI framework
- **Community**: Contributors and users who make this project better

## 📞 Support

- **Documentation**: Check this README and inline code documentation
- **Issues**: [GitHub Issues](https://github.com/CrazyDubya/research-scrapers/issues)
- **Discussions**: [GitHub Discussions](https://github.com/CrazyDubya/research-scrapers/discussions)

---

**Made with ❤️ by Stephen Thompson**

*Happy scraping! 🚀*