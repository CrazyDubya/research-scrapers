# Getting Started

This guide will help you get up and running with the research scrapers package.

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Install from Source

```bash
# Clone the repository
git clone https://github.com/CrazyDubya/research-scrapers.git
cd research-scrapers

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install the package in development mode
pip install -e .
```

### Browser Drivers (for Selenium)

If you plan to use Selenium for JavaScript-heavy sites:

```bash
# Install ChromeDriver (recommended)
# Download from: https://chromedriver.chromium.org/
# Or use webdriver-manager:
pip install webdriver-manager
```

## Basic Usage

### Simple Web Scraping

```python
from research_scrapers import WebScraper

# Create a scraper instance
scraper = WebScraper()

# Scrape a webpage
result = scraper.scrape('https://example.com')

print(f"Title: {result['title']}")
print(f"Links found: {len(result['links'])}")

# Clean up
scraper.close()
```

### Using Configuration

```python
from research_scrapers import WebScraper, Config

# Create custom configuration
config = Config()
config.REQUEST_TIMEOUT = 60
config.RATE_LIMIT = 0.5  # 0.5 requests per second

# Create scraper with custom config
scraper = WebScraper(config)

# Scrape with CSS selector
result = scraper.scrape(
    'https://example.com',
    selector='article p'  # Extract paragraphs from articles
)

print(result['selected_content'])
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
    wait_for_element='.dynamic-content'
)

print(result['title'])
scraper.close()
```

### Saving Results

```python
from research_scrapers import WebScraper
from research_scrapers.utils import save_to_json

scraper = WebScraper()
result = scraper.scrape('https://example.com')

# Save to JSON file
save_to_json(result, 'output/scraped_data.json')

scraper.close()
```

## Environment Variables

You can configure the scrapers using environment variables:

```bash
# Create a .env file
echo "SCRAPER_REQUEST_TIMEOUT=60" >> .env
echo "SCRAPER_RATE_LIMIT=2.0" >> .env
echo "SCRAPER_LOG_LEVEL=DEBUG" >> .env
```

```python
# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configuration will automatically use environment variables
from research_scrapers import Config
config = Config()  # Uses environment variables
```

## Logging

```python
from research_scrapers.utils import setup_logging

# Setup logging
logger = setup_logging(level='INFO', log_file='scraper.log')

# Now all scraper operations will be logged
from research_scrapers import WebScraper
scraper = WebScraper()
result = scraper.scrape('https://example.com')  # This will be logged
```

## Error Handling

```python
from research_scrapers import WebScraper
import requests

scraper = WebScraper()

try:
    result = scraper.scrape('https://invalid-url.com')
except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
finally:
    scraper.close()
```

## Next Steps

- Read the [API Reference](api-reference.md) for detailed documentation
- Check out [Configuration](configuration.md) for advanced settings
- Explore [Examples](examples/) for more complex use cases
- See [Contributing](contributing.md) if you want to contribute
