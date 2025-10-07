# Memory Management Guide

## Overview

The `MemoryManager` class provides comprehensive memory management for scraping operations:

- **LRU Caching**: Efficient memory-based caching with automatic eviction
- **Memory Monitoring**: Track memory usage with configurable thresholds
- **Disk Overflow**: Automatically spill large objects to disk
- **Streaming Support**: Process large files without loading into memory
- **Chunked Iteration**: Process large datasets in manageable chunks
- **Automatic Cleanup**: Context managers for resource management

## Quick Start

```python
from research_scrapers import MemoryManager

# Create memory manager
manager = MemoryManager(
    max_cache_size_mb=500,
    overflow_to_disk=True
)

# Cache scraped data
manager.set('page_1', scraped_data)

# Retrieve from cache
data = manager.get('page_1')

# Cleanup when done
manager.cleanup()
```

## Features

### 1. Smart Caching

Cache frequently accessed data with automatic LRU eviction:

```python
manager = MemoryManager(max_cache_size_mb=100)

# Cache data
for url in urls:
    data = scrape_url(url)
    manager.set(url, data)

# Retrieve cached data (fast!)
data = manager.get(url)

# Check what's cached
stats = manager.get_cache_stats()
print(f"Cached: {stats['cache_items']} items ({stats['cache_size_mb']:.1f} MB)")
```

### 2. Memory Monitoring

Monitor memory usage and prevent out-of-memory errors:

```python
from research_scrapers import MemoryMonitor, get_memory_stats

# Create monitor
monitor = MemoryMonitor(
    warning_threshold=80.0,    # Warn at 80%
    critical_threshold=90.0    # Critical at 90%
)

# Check current memory
stats = get_memory_stats()
print(f"Memory: {stats.used_mb:.1f} / {stats.total_mb:.1f} MB ({stats.percent:.1f}%)")

# Check thresholds
if monitor.check_threshold('warning'):
    print("Warning: High memory usage!")
    cleanup_caches()
```

### 3. Disk Overflow

Automatically store large objects on disk:

```python
manager = MemoryManager(
    max_cache_size_mb=100,
    overflow_to_disk=True,
    temp_dir='/tmp/scraper_cache'
)

# Store large dataset (auto-overflows to disk)
large_data = scrape_large_dataset()
manager.set('large_dataset', large_data, force_disk=True)

# Still retrieved transparently
data = manager.get('large_dataset')  # Loads from disk
```

### 4. Streaming Large Files

Process large files without loading into memory:

```python
# Stream file in chunks
for chunk in manager.stream_large_file('large_file.csv', chunk_size=8192):
    process_chunk(chunk)
```

### 5. Chunked Iteration

Process large datasets in chunks:

```python
# Process million items without loading all into memory
large_dataset = load_dataset()  # Returns iterator

for chunk in manager.chunked_iterator(large_dataset, chunk_size=1000):
    results = process_batch(chunk)
    save_results(results)
```

### 6. Context Managers

Automatic cleanup with context managers:

```python
from research_scrapers import memory_efficient_context

with memory_efficient_context() as manager:
    # Scrape data
    for url in urls:
        data = scrape_url(url)
        manager.set(url, data)
    
    # Process cached data
    results = process_all_cached_data(manager)

# Automatically cleaned up when context exits
```

## Best Practices

### 1. Cache Scraped Pages

```python
def scrape_with_cache(url, manager):
    """Scrape URL with caching."""
    # Check cache first
    cached = manager.get(url)
    if cached:
        return cached
    
    # Scrape and cache
    data = scrape_url(url)
    manager.set(url, data)
    return data

manager = MemoryManager(max_cache_size_mb=200)

for url in urls:
    data = scrape_with_cache(url, manager)
    process_data(data)
```

### 2. Monitor Memory During Long Jobs

```python
monitor = MemoryMonitor(warning_threshold=75.0)

for i, item in enumerate(large_dataset):
    process_item(item)
    
    # Check memory every 100 items
    if i % 100 == 0:
        if monitor.check_threshold('warning'):
            print(f"High memory at item {i}, cleaning up...")
            force_cleanup()
```

### 3. Use Chunking for Large Datasets

```python
manager = MemoryManager()

# Instead of: results = [process(item) for item in million_items]
# Use chunking:

all_results = []
for chunk in manager.chunked_iterator(million_items, chunk_size=1000):
    chunk_results = [process(item) for item in chunk]
    all_results.extend(chunk_results)
    
    # Save periodically
    if len(all_results) % 10000 == 0:
        save_checkpoint(all_results)
```

### 4. Combine with Batch Processing

```python
from research_scrapers import BatchProcessor, MemoryManager

manager = MemoryManager(max_cache_size_mb=500)
processor = BatchProcessor(max_workers=10)

def process_with_cache(item):
    # Check cache
    cached = manager.get(item.id)
    if cached:
        return cached
    
    # Process and cache
    result = process_item(item)
    manager.set(item.id, result)
    return result

results = processor.process_batch(items, process_with_cache)
```

## Examples

### Example 1: Memory-Efficient Web Scraping

```python
from research_scrapers import MemoryManager

def scrape_many_pages():
    manager = MemoryManager(max_cache_size_mb=100)
    
    urls = [f"https://example.com/page/{i}" for i in range(1000)]
    
    for url in urls:
        # Check cache
        cached = manager.get(url)
        if cached:
            continue
        
        # Scrape
        data = scrape_page(url)
        
        # Cache for later use
        manager.set(url, data)
        
        # Process
        process_data(data)
    
    # Cleanup
    manager.cleanup()
```

### Example 2: Processing Large CSV Files

```python
def process_large_csv(file_path):
    manager = MemoryManager()
    
    # Stream file instead of loading all at once
    results = []
    
    for chunk in manager.stream_large_file(file_path):
        lines = chunk.decode('utf-8').split('\n')
        for line in lines:
            result = process_line(line)
            results.append(result)
        
        # Save periodically
        if len(results) >= 1000:
            save_results(results)
            results = []
    
    # Save remaining
    if results:
        save_results(results)
```

### Example 3: Caching API Responses

```python
from research_scrapers import MemoryManager
import requests

class APIScraper:
    def __init__(self):
        self.manager = MemoryManager(max_cache_size_mb=50)
        self.session = requests.Session()
    
    def fetch(self, endpoint):
        """Fetch with caching."""
        # Check cache
        cached = self.manager.get(endpoint)
        if cached:
            return cached
        
        # Fetch from API
        response = self.session.get(f"https://api.example.com/{endpoint}")
        data = response.json()
        
        # Cache response
        self.manager.set(endpoint, data)
        
        return data
    
    def cleanup(self):
        self.manager.cleanup()
        self.session.close()

# Usage
scraper = APIScraper()
data = scraper.fetch('users/123')  # First call - fetches from API
data = scraper.fetch('users/123')  # Second call - returns from cache
scraper.cleanup()
```

## API Reference

### MemoryManager

```python
MemoryManager(
    max_cache_size_mb: float = 500.0,
    overflow_to_disk: bool = True,
    temp_dir: Optional[Path] = None,
    auto_cleanup: bool = True,
    warning_threshold: float = 80.0
)
```

**Methods:**

- `set(key, value, force_disk=False)` - Store value in cache
- `get(key, default=None)` - Retrieve value from cache
- `delete(key)` - Delete cached value
- `clear()` - Clear all cache
- `cleanup(force_gc=True)` - Force memory cleanup
- `get_cache_stats()` - Get cache statistics
- `stream_large_file(file_path, chunk_size=8192)` - Stream file in chunks
- `chunked_iterator(iterable, chunk_size=100)` - Iterate in chunks

### MemoryMonitor

```python
MemoryMonitor(
    warning_threshold: float = 80.0,
    critical_threshold: float = 90.0,
    callback: Optional[Callable] = None
)
```

**Methods:**

- `get_stats()` - Get current memory statistics
- `check_threshold(level='warning')` - Check if threshold exceeded
- `log_stats()` - Log current memory usage

### MemoryStats

Memory usage statistics:

- `total_mb` - Total system memory in MB
- `available_mb` - Available memory in MB
- `used_mb` - Used memory in MB
- `percent` - Memory usage percentage

### Utility Functions

- `get_memory_stats()` - Get current memory statistics
- `force_cleanup()` - Force garbage collection
- `memory_efficient_context(cleanup_on_exit=True)` - Context manager for efficient operations

## Configuration

### Adjust Cache Size

```python
# Small cache for limited memory
manager = MemoryManager(max_cache_size_mb=50)

# Large cache for high-memory systems
manager = MemoryManager(max_cache_size_mb=2000)
```

### Disable Disk Overflow

```python
# Keep everything in memory (faster but risky)
manager = MemoryManager(
    max_cache_size_mb=1000,
    overflow_to_disk=False
)
```

### Custom Temp Directory

```python
manager = MemoryManager(
    overflow_to_disk=True,
    temp_dir='/mnt/fast-ssd/cache'
)
```

## See Also

- [Batch Processing Guide](BATCH_PROCESSING.md) - For concurrent processing
- [examples/memory_efficient_scraping.py](../examples/memory_efficient_scraping.py) - Complete examples
