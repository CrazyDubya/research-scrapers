# Batch Processing Guide

## Overview

The `BatchProcessor` class provides a powerful system for processing large numbers of items efficiently with:

- **Configurable Concurrency**: Use ThreadPoolExecutor or ProcessPoolExecutor
- **Progress Tracking**: Built-in tqdm integration
- **Retry Logic**: Automatic retry with exponential backoff
- **Checkpoint/Resume**: Save progress and resume interrupted jobs
- **Error Handling**: Detailed error reporting and partial failure handling

## Quick Start

```python
from research_scrapers import BatchProcessor

# Create processor
processor = BatchProcessor(
    max_workers=5,
    retry_attempts=3,
    show_progress=True
)

# Define processing function
def process_item(url):
    return scrape_url(url)

# Process items
urls = ['url1', 'url2', 'url3', ...]
results = processor.process_batch(urls, process_item)

# Check results
print(f"Success: {processor.stats.successful_items}/{processor.stats.total_items}")
```

## Features

### 1. Concurrent Processing

Process items concurrently using threads or processes:

```python
# Thread-based (good for I/O-bound tasks like web scraping)
processor = BatchProcessor(
    max_workers=10,
    executor_type='thread'
)

# Process-based (good for CPU-bound tasks)
processor = BatchProcessor(
    max_workers=4,
    executor_type='process'
)
```

### 2. Automatic Retry

Failed items are automatically retried with exponential backoff:

```python
processor = BatchProcessor(
    max_workers=5,
    retry_attempts=3,        # Try up to 3 times
    retry_delay=1.0,         # Start with 1 second delay
    retry_backoff=2.0        # Double delay each retry
)
```

### 3. Progress Tracking

Built-in progress bar shows processing status:

```python
processor = BatchProcessor(
    max_workers=5,
    show_progress=True  # Shows tqdm progress bar
)
```

### 4. Checkpoint/Resume

Save progress and resume interrupted jobs:

```python
processor = BatchProcessor(
    max_workers=5,
    checkpoint_file='progress.json'
)

# First run - processes 100 items
results = processor.process_batch(
    items[:100],
    process_func,
    item_key_func=lambda x: x.id
)

# Second run - skips already processed items
results = processor.process_batch(
    items,  # All items
    process_func,
    item_key_func=lambda x: x.id
)
print(f"Skipped: {processor.stats.skipped_items}")
```

### 5. Error Handling

Handle errors gracefully:

```python
processor = BatchProcessor(
    max_workers=5,
    fail_fast=True,  # Stop on first failure
    callback=lambda result: print(f"Processed: {result.item}")
)

results = processor.process_batch(items, process_func)

# Get failed items
failed = processor.get_failed_items(results)
for item in failed:
    print(f"Failed: {item}")

# Get successful results
successful = processor.get_successful_results(results)
```

### 6. Chunked Processing

Process items in batches (useful for batch APIs):

```python
def process_chunk(items):
    """Process multiple items in one API call."""
    return batch_api_call(items)

results = processor.process_in_chunks(
    items,
    process_chunk,
    chunk_size=50
)
```

## Simple Usage

For simple cases, use the convenience function:

```python
from research_scrapers import process_batch_simple

results = process_batch_simple(
    items,
    process_func,
    max_workers=5,
    show_progress=True
)
```

## Best Practices

1. **Choose the right executor type:**
   - Use `'thread'` for I/O-bound tasks (web scraping, file operations)
   - Use `'process'` for CPU-bound tasks (data processing, computation)

2. **Set appropriate worker count:**
   - For threads: Can use more workers (10-50)
   - For processes: Use CPU count or slightly more

3. **Use checkpoints for long-running jobs:**
   - Always use checkpoints for jobs that take > 1 hour
   - Provides resume capability if interrupted

4. **Monitor resources:**
   - Watch memory usage with many concurrent workers
   - Adjust `max_workers` based on available resources

5. **Handle failures gracefully:**
   - Set reasonable retry attempts (2-3 is usually good)
   - Use callbacks to log progress
   - Save results periodically

## Examples

### Example 1: Scrape Multiple URLs

```python
from research_scrapers import BatchProcessor
import requests

def scrape_url(url):
    response = requests.get(url)
    return {
        'url': url,
        'status': response.status_code,
        'content': response.text
    }

processor = BatchProcessor(max_workers=10, retry_attempts=3)
urls = ['https://example.com/page1', 'https://example.com/page2', ...]
results = processor.process_batch(urls, scrape_url)

# Save results
processor.save_results(results, 'scraping_results.json')
```

### Example 2: Download and Process Files

```python
def download_and_process(file_info):
    # Download file
    data = download_file(file_info['url'])
    
    # Process data
    processed = process_data(data)
    
    # Save to disk
    save_result(file_info['id'], processed)
    
    return {'id': file_info['id'], 'status': 'success'}

files = [
    {'id': 1, 'url': 'https://example.com/file1.csv'},
    {'id': 2, 'url': 'https://example.com/file2.csv'},
    ...
]

processor = BatchProcessor(
    max_workers=5,
    checkpoint_file='download_progress.json'
)

results = processor.process_batch(
    files,
    download_and_process,
    item_key_func=lambda x: x['id']
)
```

## API Reference

### BatchProcessor

```python
BatchProcessor(
    max_workers: int = 5,
    executor_type: str = 'thread',
    retry_attempts: int = 3,
    retry_delay: float = 1.0,
    retry_backoff: float = 2.0,
    show_progress: bool = True,
    checkpoint_file: Optional[Path] = None,
    fail_fast: bool = False,
    callback: Optional[Callable] = None
)
```

**Methods:**

- `process_batch(items, process_func, item_key_func=None, batch_size=None)` - Process items
- `process_in_chunks(items, process_func, chunk_size=10)` - Process in chunks
- `get_failed_items(results)` - Extract failed items
- `get_successful_results(results)` - Extract successful results
- `save_results(results, output_file, format='json')` - Save results to file
- `clear_checkpoint()` - Clear checkpoint file

**Properties:**

- `stats` - BatchStats object with processing statistics

### BatchResult

Dataclass representing the result of processing one item:

- `item` - The original item
- `success` - Whether processing succeeded
- `result` - The result (if successful)
- `error` - Error message (if failed)
- `retry_count` - Number of retries attempted
- `processing_time` - Time taken to process
- `timestamp` - When processing completed

### BatchStats

Statistics about batch processing:

- `total_items` - Total number of items
- `successful_items` - Number of successful items
- `failed_items` - Number of failed items
- `skipped_items` - Number of skipped items (from checkpoint)
- `total_processing_time` - Total time spent processing
- `average_processing_time` - Average time per successful item
- `start_time` - When processing started
- `end_time` - When processing completed

## See Also

- [Memory Management Guide](MEMORY_MANAGEMENT.md) - For memory-efficient batch processing
- [examples/batch_processing_example.py](../examples/batch_processing_example.py) - Complete examples
