# Configuration

The research scrapers package provides flexible configuration options through the `Config` class.

## Configuration Methods

### 1. Default Configuration

```python
from research_scrapers import Config

# Uses all default values
config = Config()
```

### 2. Environment Variables

Set environment variables with the `SCRAPER_` prefix:

```bash
export SCRAPER_REQUEST_TIMEOUT=60
export SCRAPER_MAX_RETRIES=5
export SCRAPER_RATE_LIMIT=2.0
export SCRAPER_USER_AGENT="My Custom Bot 1.0"
export SCRAPER_LOG_LEVEL=DEBUG
```

### 3. Configuration File

#### JSON Configuration

```json
{
  "request_timeout": 45,
  "max_retries": 4,
  "rate_limit": 1.5,
  "log_level": "INFO",
  "user_agent": "Research Bot 1.0",
  "output_dir": "./data",
  "api_keys": {
    "github": "your_github_token",
    "twitter": "your_twitter_token"
  }
}
```

```python
config = Config(config_file='config.json')
```

#### YAML Configuration

```yaml
request_timeout: 45
max_retries: 4
rate_limit: 1.5
log_level: INFO
user_agent: "Research Bot 1.0"
output_dir: "./data"
api_keys:
  github: "your_github_token"
  twitter: "your_twitter_token"
```

```python
config = Config(config_file='config.yaml')
```

## Configuration Options

### HTTP Settings

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `REQUEST_TIMEOUT` | int | 30 | Request timeout in seconds |
| `MAX_RETRIES` | int | 3 | Maximum number of retry attempts |
| `RETRY_DELAY` | float | 1.0 | Initial delay between retries |
| `RETRY_BACKOFF` | float | 2.0 | Backoff multiplier for retries |
| `RATE_LIMIT` | float | 1.0 | Requests per second |

### User Agent

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `USER_AGENT` | str | Chrome UA | User agent string for requests |

### Proxy Settings

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `PROXY` | str | None | Proxy URL (http://proxy:port) |
| `PROXY_USERNAME` | str | None | Proxy authentication username |
| `PROXY_PASSWORD` | str | None | Proxy authentication password |

### Output Settings

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `OUTPUT_DIR` | Path | 'output' | Default output directory |
| `LOG_LEVEL` | str | 'INFO' | Logging level |
| `LOG_FILE` | str | None | Log file path (optional) |

### Selenium Settings

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `SELENIUM_BROWSER` | str | 'chrome' | Browser to use (chrome/firefox) |
| `SELENIUM_HEADLESS` | bool | True | Run browser in headless mode |
| `SELENIUM_IMPLICIT_WAIT` | int | 10 | Implicit wait timeout |

### Content Processing

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `MAX_CONTENT_LENGTH` | int | 1000000 | Maximum content length (1MB) |
| `ALLOWED_CONTENT_TYPES` | list | HTML, JSON, etc. | Allowed MIME types |
| `MAX_FILE_SIZE` | int | 10485760 | Maximum file size (10MB) |
| `ALLOWED_FILE_EXTENSIONS` | list | Common formats | Allowed file extensions |

## API Keys Management

### Setting API Keys

```python
config = Config()

# Set API keys programmatically
config.set_api_key('github', 'your_github_token')
config.set_api_key('twitter', 'your_twitter_token')

# Or via environment variables
# GITHUB_API_KEY=your_token
# TWITTER_API_KEY=your_token
```

### Using API Keys

```python
# Get API key
github_token = config.get_api_key('github')

if github_token:
    # Use the token for authenticated requests
    headers = {'Authorization': f'token {github_token}'}
else:
    print("GitHub API key not configured")
```

## Environment Variable Reference

### HTTP Settings
- `SCRAPER_REQUEST_TIMEOUT`
- `SCRAPER_MAX_RETRIES`
- `SCRAPER_RATE_LIMIT`
- `SCRAPER_USER_AGENT`

### Proxy Settings
- `SCRAPER_PROXY`
- `SCRAPER_PROXY_USERNAME`
- `SCRAPER_PROXY_PASSWORD`

### Output Settings
- `SCRAPER_OUTPUT_DIR`
- `SCRAPER_LOG_LEVEL`
- `SCRAPER_LOG_FILE`

### Database
- `DATABASE_URL`

### API Keys
- `GITHUB_API_KEY`
- `TWITTER_API_KEY`
- `REDDIT_API_KEY`
- `LINKEDIN_API_KEY`

## Configuration Precedence

Configuration values are loaded in this order (later values override earlier ones):

1. **Default values** - Built-in defaults
2. **Environment variables** - OS environment variables
3. **Configuration file** - JSON/YAML file (if provided)

## Example Configurations

### Development Configuration

```python
config = Config()
config.LOG_LEVEL = 'DEBUG'
config.REQUEST_TIMEOUT = 10
config.RATE_LIMIT = 5.0  # Faster for development
config.SELENIUM_HEADLESS = False  # See browser for debugging
```

### Production Configuration

```python
config = Config()
config.LOG_LEVEL = 'WARNING'
config.REQUEST_TIMEOUT = 60
config.RATE_LIMIT = 0.5  # Respectful rate limiting
config.MAX_RETRIES = 5
config.SELENIUM_HEADLESS = True
```

### High-Volume Scraping

```python
config = Config()
config.RATE_LIMIT = 10.0  # 10 requests per second
config.MAX_RETRIES = 1  # Fail fast
config.REQUEST_TIMEOUT = 15  # Shorter timeout
```

## Validation

The configuration system includes basic validation:

```python
config = Config()

# This will work
config.RATE_LIMIT = 2.0

# This might cause issues (validation depends on implementation)
config.RATE_LIMIT = -1  # Negative rate limit doesn't make sense
```

## Configuration Utilities

```python
# Convert config to dictionary
config_dict = config.to_dict()
print(config_dict)

# Print configuration
print(repr(config))

# Check if API key is configured
if config.get_api_key('github'):
    print("GitHub API key is configured")
```
