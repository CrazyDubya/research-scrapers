# Stack Overflow Scraper - Structured Logging Guide

This guide demonstrates the comprehensive structured logging system integrated with the Stack Overflow scraper, showcasing JSON structured logging, correlation ID tracking, automatic log rotation, and performance metrics collection.

## Overview

The StructuredLogger system provides enterprise-grade logging capabilities with:

- **JSON structured logging** for machine-readable logs
- **Correlation ID tracking** across distributed operations
- **Automatic log rotation** by size and time
- **Performance metrics collection** with detailed analytics
- **Request/response logging** with sensitive data sanitization
- **Error tracking** with full context and stack traces
- **Multiple log formats** (text, JSON, error-only)

## Quick Start

```python
from research_scrapers.structured_logging import StructuredLogger
from research_scrapers.stackoverflow_scraper import StackOverflowScraper

# Create structured logger
logger = StructuredLogger(
    name="stackoverflow_scraper",
    log_dir="logs",
    enable_json=True,
    enable_console=True
)

# Create scraper with logging
scraper = StackOverflowScraper()
scraper.logger = logger

# Track performance and log operations
with logger.track_performance("scrape_questions") as metrics:
    questions = scraper.scrape_questions_by_tag("python", max_questions=10)
    metrics.items_processed = len(questions)
```

## JSON Structured Logging

### Example JSON Log Entry

```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "INFO",
  "logger": "stackoverflow_scraper",
  "message": "Successfully scraped question",
  "module": "stackoverflow_scraper",
  "function": "scrape_question",
  "line": 245,
  "correlation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "user_id": "user_123",
  "session_id": "session_456",
  "operation": "question_scraping",
  "question_id": "12345678",
  "title": "How to use Python logging effectively?",
  "answers_found": 5,
  "vote_count": 42,
  "tags": ["python", "logging"],
  "duration_ms": 234.5
}
```

### Key Features

- **Structured Format**: All logs are valid JSON with consistent schema
- **Rich Context**: Automatic inclusion of correlation IDs, user context, and operation details
- **Sanitization**: Sensitive data (API keys, tokens) automatically redacted
- **Timestamps**: ISO 8601 format with millisecond precision
- **Metadata**: Function, module, and line number for debugging

## Correlation ID Tracking

Correlation IDs enable tracking requests across multiple operations and services:

```python
# Generate correlation ID for request tracking
correlation_id = logger.new_correlation_id()

# Set context that persists across all log entries
logger.set_context(
    user_id="user_123",
    session_id="session_456",
    operation="bulk_scraping"
)

# All subsequent logs will include this context
logger.info("Starting bulk scraping", target_tag="python")
logger.info("Processing question 1")  # Same correlation_id
logger.info("Processing question 2")  # Same correlation_id
```

### Benefits

- **Request Tracing**: Follow a single request through multiple components
- **Debugging**: Quickly isolate logs for a specific operation
- **Analytics**: Analyze performance patterns across related operations
- **Monitoring**: Set up alerts based on correlation ID patterns

## Performance Metrics Collection

### Automatic Performance Tracking

```python
# Track operation performance automatically
with logger.track_performance("scrape_stackoverflow_questions") as metrics:
    questions = scraper.scrape_questions_by_tag("python", max_questions=50)
    
    # Set additional metrics
    metrics.api_calls = 5
    metrics.items_processed = len(questions)
    
    # Metrics automatically logged on completion
```

### Metrics Summary

```python
# Get comprehensive performance summary
summary = logger.get_metrics_summary()
print(f"Success rate: {summary['success_rate']}%")
print(f"Average duration: {summary['avg_duration_ms']}ms")
print(f"Total API calls: {summary['total_api_calls']}")
```

### Sample Metrics Output

```json
{
  "total_operations": 25,
  "successful": 23,
  "failed": 2,
  "success_rate": 92.0,
  "avg_duration_ms": 456.7,
  "min_duration_ms": 89.2,
  "max_duration_ms": 1234.5,
  "total_api_calls": 127,
  "total_items_processed": 1250
}
```

## Automatic Log Rotation

### Configuration

```python
logger = StructuredLogger(
    name="stackoverflow_scraper",
    log_dir="logs",
    max_file_size_mb=10,    # Rotate when file reaches 10MB
    backup_count=5,         # Keep 5 backup files
    rotation_time='midnight' # Also rotate daily at midnight
)
```

### File Structure

```
logs/
├── stackoverflow_scraper.log           # Current text log
├── stackoverflow_scraper.log.1         # Previous text log
├── stackoverflow_scraper.log.2         # Older text log
├── stackoverflow_scraper.json.log      # Current JSON log
├── stackoverflow_scraper.json.log.1    # Previous JSON log
├── stackoverflow_scraper.error.log     # Error-only log
└── stackoverflow_scraper.error.log.1   # Previous error log
```

### Benefits

- **Disk Space Management**: Prevents logs from consuming unlimited disk space
- **Performance**: Smaller active log files improve I/O performance
- **Retention**: Configurable retention policies for compliance
- **Multiple Formats**: Separate rotation for text, JSON, and error logs

## Request/Response Logging with Sanitization

### Automatic Sanitization

```python
# Sensitive data is automatically redacted
logger.log_request(
    method="GET",
    url="https://stackoverflow.com/api/questions?key=secret123&token=abc456",
    status_code=200,
    duration_ms=234.5,
    sanitize=True  # Default: True
)
```

### Sanitized Output

```json
{
  "event": "http_request",
  "method": "GET",
  "url": "https://stackoverflow.com/api/questions?key=***REDACTED***&token=***REDACTED***",
  "status_code": 200,
  "duration_ms": 234.5,
  "timestamp": "2024-01-15T10:30:45.123Z"
}
```

### Sensitive Parameters Detected

- `api_key`, `key`
- `token`, `access_token`
- `password`, `passwd`
- `secret`, `client_secret`
- `authorization`

## Error Tracking with Context

### Comprehensive Error Logging

```python
try:
    result = scraper.scrape_question("invalid_id")
except Exception as e:
    logger.log_exception(
        e,
        context={
            "question_id": "invalid_id",
            "scraping_stage": "question_parsing",
            "retry_attempt": 3
        },
        severity="high",
        recovery_action="user_notification"
    )
```

### Error Log Entry

```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "ERROR",
  "event": "exception",
  "exception_type": "ValueError",
  "exception_message": "Invalid question ID format",
  "traceback": ["Traceback (most recent call last):", "..."],
  "context": {
    "question_id": "invalid_id",
    "scraping_stage": "question_parsing",
    "retry_attempt": 3
  },
  "severity": "high",
  "recovery_action": "user_notification",
  "correlation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

## Integration Examples

### Basic Integration

```python
from research_scrapers.structured_logging import StructuredLogger
from research_scrapers.stackoverflow_scraper import StackOverflowScraper, ScrapingOptions

# Initialize logger
logger = StructuredLogger(
    name="my_stackoverflow_scraper",
    log_dir="logs",
    enable_json=True
)

# Create scraper and replace logger
scraper = StackOverflowScraper()
scraper.logger = logger

# Configure scraping
options = ScrapingOptions(
    include_answers=True,
    max_questions=100
)

# Scrape with full logging
correlation_id = logger.new_correlation_id()
logger.set_context(operation="daily_scraping", batch_id="20240115_001")

with logger.track_performance("daily_stackoverflow_scrape") as metrics:
    questions = scraper.scrape_questions_by_tag("python", options)
    metrics.items_processed = len(questions)
    
    logger.info("Daily scraping completed", 
               questions_scraped=len(questions),
               correlation_id=correlation_id)
```

### Advanced Integration with Error Handling

```python
def robust_stackoverflow_scraping():
    logger = StructuredLogger("robust_scraper", log_dir="logs")
    scraper = StackOverflowScraper()
    scraper.logger = logger
    
    correlation_id = logger.new_correlation_id()
    logger.set_context(
        operation="robust_scraping",
        environment="production"
    )
    
    tags_to_scrape = ["python", "javascript", "java", "go"]
    
    for tag in tags_to_scrape:
        with logger.track_performance(f"scrape_tag_{tag}") as metrics:
            try:
                logger.info(f"Starting to scrape tag: {tag}")
                
                questions = scraper.scrape_questions_by_tag(
                    tag, 
                    max_questions=50,
                    sort_by="votes"
                )
                
                metrics.items_processed = len(questions)
                metrics.api_calls = len(questions)  # Approximate
                
                logger.info(f"Successfully scraped {len(questions)} questions for tag {tag}")
                
            except Exception as e:
                logger.log_exception(
                    e,
                    context={
                        "tag": tag,
                        "scraping_stage": "tag_processing"
                    },
                    severity="medium"
                )
                continue
    
    # Generate final report
    summary = logger.get_metrics_summary()
    logger.info("Scraping session completed", performance_summary=summary)
    
    return summary
```

## Best Practices

### 1. Context Management

```python
# Set context early and maintain throughout operation
logger.set_context(
    user_id=current_user.id,
    session_id=session.id,
    operation="stackoverflow_research"
)
```

### 2. Performance Tracking

```python
# Always use performance tracking for significant operations
with logger.track_performance("expensive_operation") as metrics:
    result = expensive_operation()
    metrics.items_processed = len(result)
    metrics.api_calls = api_call_count
```

### 3. Error Context

```python
# Provide rich context for errors
try:
    risky_operation()
except Exception as e:
    logger.log_exception(
        e,
        context={
            "operation_stage": "data_processing",
            "input_size": len(input_data),
            "configuration": current_config
        }
    )
```

### 4. Sensitive Data

```python
# Always sanitize URLs and requests
logger.log_request(
    method="GET",
    url=potentially_sensitive_url,
    sanitize=True  # Always use sanitization
)
```

## Configuration Options

### Logger Configuration

```python
logger = StructuredLogger(
    name="my_scraper",              # Logger name
    log_dir="logs",                 # Log directory (None for console only)
    log_level="INFO",               # Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    enable_json=True,               # Enable JSON formatted logs
    enable_console=True,            # Enable console output
    max_file_size_mb=10,           # File size rotation threshold
    backup_count=5,                # Number of backup files to keep
    rotation_time="midnight",       # Time-based rotation
    context=LogContext(...)         # Default context
)
```

### Scraper Integration

```python
# Method 1: Replace logger after creation
scraper = StackOverflowScraper()
scraper.logger = my_logger

# Method 2: Custom config with logger
config = Config()
config.logger = my_logger
scraper = StackOverflowScraper(config)
```

## Monitoring and Alerting

### Log Analysis Queries

```bash
# Find all errors in the last hour
jq 'select(.level == "ERROR" and (.timestamp | fromdateiso8601) > (now - 3600))' logs/scraper.json.log

# Calculate average response times
jq 'select(.event == "http_request") | .duration_ms' logs/scraper.json.log | jq -s 'add/length'

# Find operations by correlation ID
jq 'select(.correlation_id == "a1b2c3d4-e5f6-7890-abcd-ef1234567890")' logs/scraper.json.log
```

### Performance Monitoring

```python
# Regular performance reporting
def generate_performance_report(logger):
    summary = logger.get_metrics_summary()
    
    if summary['success_rate'] < 95:
        logger.warning("Low success rate detected", summary=summary)
    
    if summary['avg_duration_ms'] > 1000:
        logger.warning("High average response time", summary=summary)
    
    return summary
```

## Troubleshooting

### Common Issues

1. **Large Log Files**: Reduce `max_file_size_mb` or increase rotation frequency
2. **Missing Context**: Ensure `set_context()` is called before operations
3. **Performance Impact**: Disable console logging in production
4. **JSON Parsing Errors**: Check for non-serializable objects in log data

### Debug Mode

```python
# Enable debug logging for troubleshooting
logger = StructuredLogger(
    name="debug_scraper",
    log_level="DEBUG",
    enable_console=True
)

# Debug specific operations
logger.debug("Detailed operation info", 
            internal_state=current_state,
            configuration=config_dict)
```

## Testing

Run the comprehensive test suite:

```bash
# Run logging tests
python -m pytest tests/test_stackoverflow_logging.py -v

# Run demonstration
python examples/stackoverflow_logging_demo.py
```

The test suite verifies:
- JSON structured logging output
- Correlation ID tracking
- Performance metrics collection
- Log rotation functionality
- Error tracking with context
- Integration with Stack Overflow scraper

## Conclusion

The StructuredLogger system provides enterprise-grade logging capabilities that enhance the Stack Overflow scraper with:

- **Observability**: Complete visibility into scraper operations
- **Debugging**: Rich context and correlation tracking
- **Performance**: Detailed metrics and analytics
- **Reliability**: Automatic rotation and error handling
- **Security**: Sensitive data sanitization
- **Integration**: Seamless integration with existing scrapers

This logging system enables production-ready deployment with comprehensive monitoring, debugging, and performance analysis capabilities.