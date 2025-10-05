# Web Research Scraper

A comprehensive, production-ready web scraping solution designed for research purposes. This scraper provides advanced features for extracting content from websites while respecting robots.txt, implementing rate limiting, and handling various authentication methods.

## Features

### Core Capabilities
- **HTML Parsing**: Support for both BeautifulSoup (fast) and Playwright (JavaScript-enabled)
- **Smart Content Detection**: Automatically detects article, documentation, blog, and other content types
- **Rate Limiting**: Token bucket algorithm with configurable rates and burst sizes
- **Robots.txt Compliance**: Automatic robots.txt parsing and compliance checking
- **Authentication**: Support for Basic, Bearer, Cookie, and Form-based authentication
- **Content Cleaning**: Removes ads, navigation, and other non-content elements
- **Pagination**: Handles next-button, numbered, and URL pattern pagination
- **Error Handling**: Comprehensive retry logic with exponential backoff

### Advanced Features
- **Targeted Extraction**: Use CSS selectors for precise content extraction
- **Metadata Extraction**: Automatically extracts titles, authors, dates, and other metadata
- **Link Following**: Extract and optionally follow internal links
- **Multi-format Output**: JSON, Markdown, HTML, and plain text output
- **Async Support**: Full asynchronous operation for high performance
- **Stealth Mode**: Browser fingerprinting protection for Playwright

## Quick Start

### Installation

```bash
# Install the package
pip install -e .

# Install additional dependencies for browser support
playwright install
```

### Basic Usage

```python
import asyncio
from research_scrapers.web_scraper import WebScraper, ScraperConfig

async def main():
    # Create scraper with default configuration
    scraper = WebScraper()
    
    # Scrape a single URL
    result = await scraper.scrape_url("https://example.com/article")
    print(result['content'])
    
    # Clean up
    await scraper.close()

asyncio.run(main())
```

### Using Presets

```python
from research_scrapers.web_scraper import WebScraper, get_preset

# Use article preset for news/blog scraping
config = get_preset("article")
scraper = WebScraper(config)

# Use documentation preset for technical docs
config = get_preset("documentation")
scraper = WebScraper(config)

# Use SPA preset for JavaScript-heavy sites
config = get_preset("spa")
scraper = WebScraper(config)
```

### Command Line Interface

```bash
# Scrape a single URL
web-scraper scrape https://example.com/article

# Use a preset configuration
web-scraper scrape https://example.com/docs --preset documentation

# Scrape with pagination
web-scraper scrape-paginated https://example.com/blog --max-pages 10

# Scrape multiple URLs
web-scraper scrape-multiple https://example1.com https://example2.com

# List available presets
web-scraper list-presets
```

## Configuration

### Configuration File

Create a YAML configuration file:

```yaml
user_agent: "ResearchBot/1.0"
timeout: 30
respect_robots_txt: true

rate_limit:
  requests_per_second: 1.0
  burst_size: 3
  max_retries: 3

extraction:
  method: "auto"
  content_type: "article"
  extract_metadata: true
  clean_whitespace: true

pagination:
  enabled: true
  method: "next_button"
  max_pages: 50

output_format: "json"
output_dir: "./output"
```

### Programmatic Configuration

```python
from research_scrapers.web_scraper import ScraperConfig, ExtractionConfig

config = ScraperConfig(
    user_agent="MyBot/1.0",
    extraction=ExtractionConfig(
        method="targeted",
        selectors={
            "title": "h1.article-title",
            "content": ".article-body",
            "author": ".author-name"
        }
    )
)
```

## Authentication

### Basic Authentication

```python
from research_scrapers.web_scraper import ScraperConfig, AuthConfig

config = ScraperConfig(
    auth=AuthConfig(
        auth_type="basic",
        username="your_username",
        password="your_password"
    )
)
```

### Bearer Token

```python
config = ScraperConfig(
    auth=AuthConfig(
        auth_type="bearer",
        token="your_api_token"
    )
)
```

### Cookie-based Authentication

```python
config = ScraperConfig(
    auth=AuthConfig(
        auth_type="cookie",
        cookies={
            "session_id": "abc123",
            "auth_token": "xyz789"
        }
    )
)
```

### Form-based Login

```python
config = ScraperConfig(
    auth=AuthConfig(
        auth_type="form",
        username="your_username",
        password="your_password",
        form_login_url="https://example.com/login",
        form_fields={
            "csrf_token": "token_value"
        }
    )
)
```

## Content Extraction Methods

### Automatic Detection

```python
config = ScraperConfig(
    extraction=ExtractionConfig(
        method="auto",  # Automatically detects content type
        extract_metadata=True
    )
)
```

### Targeted Extraction

```python
config = ScraperConfig(
    extraction=ExtractionConfig(
        method="targeted",
        selectors={
            "title": "h1, .title",
            "content": "article, .content",
            "date": "time, .date",
            "tags": ".tags a"
        }
    )
)
```

### Full Page Extraction

```python
config = ScraperConfig(
    extraction=ExtractionConfig(
        method="full_page"  # Returns complete HTML
    )
)
```

## Pagination Handling

### Next Button Pagination

```python
config = ScraperConfig(
    pagination=PaginationConfig(
        enabled=True,
        method="next_button",
        next_selector="a.next-page",
        max_pages=100
    )
)
```

### Numbered Pagination

```python
config = ScraperConfig(
    pagination=PaginationConfig(
        enabled=True,
        method="numbered",
        max_pages=50
    )
)
```

### URL Pattern Pagination

```python
config = ScraperConfig(
    pagination=PaginationConfig(
        enabled=True,
        method="url_pattern",
        page_number_pattern="https://example.com/articles?page={page}",
        max_pages=20
    )
)
```

## Browser Support (Playwright)

For JavaScript-heavy sites:

```python
config = ScraperConfig(
    browser=BrowserConfig(
        enabled=True,
        headless=True,
        browser_type="chromium",
        wait_for_load_state="networkidle",
        stealth_mode=True
    )
)
```

## Rate Limiting and Compliance

### Rate Limiting

```python
config = ScraperConfig(
    rate_limit=RateLimitConfig(
        requests_per_second=2.0,
        burst_size=5,
        backoff_factor=2.0,
        max_retries=3
    )
)
```

### Robots.txt Compliance

```python
config = ScraperConfig(
    respect_robots_txt=True,
    robots_txt_cache_time=3600,  # Cache for 1 hour
    user_agent="YourBot/1.0 (+https://yoursite.com/bot)"
)
```

## Error Handling and Logging

```python
import logging
from loguru import logger

# Configure logging
logger.add("scraper.log", rotation="10 MB", level="INFO")

# The scraper automatically handles:
# - Network timeouts and retries
# - Rate limiting (429 responses)
# - Authentication failures
# - Robots.txt violations
# - Content extraction errors
```

## Best Practices

### 1. Respect Website Policies
- Always check and respect robots.txt
- Use appropriate rate limiting
- Include contact information in User-Agent
- Don't overload servers

### 2. Handle Errors Gracefully
- Implement proper retry logic
- Log errors for debugging
- Have fallback extraction methods

### 3. Optimize Performance
- Use async operations for multiple URLs
- Cache robots.txt responses
- Reuse sessions for authenticated scraping

### 4. Content Quality
- Clean extracted content appropriately
- Validate extracted data
- Handle different content types

### 5. Legal and Ethical Considerations
- Check website terms of service
- Respect copyright and intellectual property
- Consider data privacy regulations
- Use scraped data responsibly

## Examples

See the `examples/` directory for:
- Configuration files for different use cases
- Python scripts demonstrating various features
- Real-world scraping scenarios

## Troubleshooting

### Common Issues

1. **JavaScript-heavy sites**: Use browser mode with Playwright
2. **Rate limiting**: Reduce requests_per_second or increase delays
3. **Authentication failures**: Check credentials and auth method
4. **Content not found**: Adjust selectors or use auto-detection
5. **Robots.txt blocking**: Check robots.txt compliance settings

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or with loguru
from loguru import logger
logger.add(sys.stderr, level="DEBUG")
```

## API Reference

See the individual module documentation for detailed API information:
- `WebScraper`: Main scraper class
- `ScraperConfig`: Configuration management
- `ContentExtractor`: Content extraction and cleaning
- `RateLimiter`: Rate limiting implementation
- `AuthManager`: Authentication handling
- `PaginationHandler`: Pagination support
