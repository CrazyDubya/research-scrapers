# Web Research Scraper

A comprehensive, production-ready web scraping solution for research purposes.

## Quick Start

```python
import asyncio
from research_scrapers.web_scraper import WebScraper

async def main():
    scraper = WebScraper()
    result = await scraper.scrape_url("https://example.com")
    print(result['content'])
    await scraper.close()

asyncio.run(main())
```

## Features

- **Smart Content Extraction**: Automatically detects and extracts main content
- **Rate Limiting**: Respects server resources with configurable rate limits
- **Robots.txt Compliance**: Automatically checks and respects robots.txt
- **Authentication Support**: Basic, Bearer, Cookie, and Form-based auth
- **Pagination Handling**: Supports various pagination methods
- **Browser Support**: Playwright integration for JavaScript-heavy sites
- **Content Cleaning**: Removes ads, navigation, and unwanted elements
- **Async Operations**: Full async support for high performance

## Installation

```bash
# Install dependencies
pip install -r requirements-web-scraper.txt

# Install Playwright browsers (optional)
playwright install
```

## Configuration

### Using Presets

```python
from research_scrapers.web_scraper import get_preset, WebScraper

# For news articles
config = get_preset("article")
scraper = WebScraper(config)

# For documentation
config = get_preset("documentation")
scraper = WebScraper(config)

# For JavaScript-heavy sites
config = get_preset("spa")
scraper = WebScraper(config)
```

### Custom Configuration

```python
from research_scrapers.web_scraper import ScraperConfig, ExtractionConfig

config = ScraperConfig(
    user_agent="MyBot/1.0",
    extraction=ExtractionConfig(
        method="targeted",
        selectors={
            "title": "h1",
            "content": ".article-body"
        }
    )
)
```

## Command Line Usage

```bash
# Scrape a single URL
python -m research_scrapers.web_scraper.cli scrape https://example.com

# Use preset configuration
python -m research_scrapers.web_scraper.cli scrape https://example.com --preset article

# Scrape with pagination
python -m research_scrapers.web_scraper.cli scrape-paginated https://example.com --max-pages 10

# List available presets
python -m research_scrapers.web_scraper.cli list-presets
```

## Examples

See the `examples/web_scraper_usage/` directory for comprehensive examples:

- `basic_scraping.py`: Basic usage examples
- `advanced_scraping.py`: Advanced features and configurations
- `real_world_examples.py`: Real-world scraping scenarios

## Documentation

Full documentation is available in `docs/web_scraper/README.md`.

## Best Practices

1. **Respect Robots.txt**: Always enable robots.txt compliance
2. **Use Rate Limiting**: Don't overload target servers
3. **Proper User-Agent**: Include contact information
4. **Handle Errors**: Implement proper error handling and retries
5. **Legal Compliance**: Check terms of service and applicable laws

## Testing

```bash
# Run tests
python -m pytest tests/web_scraper/ -v

# Run with coverage
python -m pytest tests/web_scraper/ --cov=src/research_scrapers/web_scraper
```
