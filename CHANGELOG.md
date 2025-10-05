# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added - Web Research Scraper

#### Core Features
- **WebScraper**: Main scraper class with async support
- **ContentExtractor**: Smart content detection and extraction
- **RateLimiter**: Token bucket rate limiting with burst support
- **RobotsHandler**: Automatic robots.txt parsing and compliance
- **AuthManager**: Multiple authentication methods (Basic, Bearer, Cookie, Form)
- **PaginationHandler**: Support for various pagination types

#### Content Extraction
- Auto-detection of content types (article, documentation, blog)
- Targeted extraction using CSS selectors
- Full-page extraction option
- Metadata extraction (title, author, date, keywords)
- Link extraction and following
- Content cleaning and processing
- Whitespace normalization
- Unwanted element removal

#### Browser Support
- Playwright integration for JavaScript-heavy sites
- Support for Chromium, Firefox, and WebKit
- Stealth mode for anti-bot protection
- Configurable viewport and timeouts
- Wait conditions for dynamic content

#### Rate Limiting & Compliance
- Token bucket algorithm with configurable rates
- Exponential backoff for retries
- Retry-After header support
- Per-domain rate tracking
- Robots.txt caching and compliance
- Crawl delay support

#### Authentication
- HTTP Basic Authentication
- Bearer token authentication
- Cookie-based authentication
- Form-based login with CSRF support
- Custom headers support
- Session management

#### Pagination
- Next button pagination
- Numbered pagination
- URL pattern pagination
- Infinite scroll detection
- Configurable page limits
- Inter-page delays

#### Configuration
- YAML and JSON configuration files
- Preset configurations for common use cases
- Programmatic configuration
- Environment variable support
- Validation and error handling

#### CLI Interface
- Command-line tool for scraping
- Preset management
- Multiple output formats
- Batch processing support
- Progress reporting

#### Examples & Documentation
- Comprehensive usage examples
- Real-world scraping scenarios
- Configuration templates
- Best practices guide
- API documentation

#### Testing
- Unit tests for all components
- Integration tests
- Mock-based testing
- Async test support
- Coverage reporting

#### Error Handling
- Comprehensive error handling
- Retry logic with exponential backoff
- Graceful degradation
- Detailed logging
- Statistics and monitoring

### Configuration Presets
- **article**: Optimized for news articles and blog posts
- **documentation**: Designed for technical documentation
- **blog**: Configured for blog scraping with pagination
- **spa**: Optimized for Single Page Applications

### Dependencies Added
- playwright>=1.40.0 (browser automation)
- aiohttp>=3.9.0 (async HTTP client)
- click>=8.1.7 (CLI interface)
- loguru>=0.7.2 (enhanced logging)
- pydantic>=2.5.0 (data validation, optional)

### Files Added
- `src/research_scrapers/web_scraper/` - Main package directory
- `examples/web_scraper_configs/` - Configuration examples
- `examples/web_scraper_usage/` - Usage examples
- `docs/web_scraper/` - Documentation
- `tests/web_scraper/` - Test suite
- `requirements-web-scraper.txt` - Additional dependencies
- `setup_web_scraper.py` - Setup script

## [Previous Versions]

### Existing Features
- GitHub repository scraper
- GitHub issue scraper
- GitHub user scraper
- Linear integration
- Basic utilities and configuration
