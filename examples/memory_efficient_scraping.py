#!/usr/bin/env python3
"""
Memory-Efficient Scraping Example

This example demonstrates how to use the MemoryManager for efficient
memory usage when scraping large amounts of data.

Features demonstrated:
- Memory monitoring
- Caching with LRU eviction
- Streaming large files
- Chunked iteration
- Memory-efficient context managers
- Disk overflow for large objects
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from research_scrapers.memory_manager import (
    MemoryManager,
    MemoryMonitor,
    memory_efficient_context,
    get_memory_stats,
    force_cleanup
)


def example_basic_memory_monitoring():
    """Example: Basic memory monitoring."""
    print("=" * 80)
    print("Example 1: Memory Monitoring")
    print("=" * 80)
    
    monitor = MemoryMonitor(
        warning_threshold=80.0,
        critical_threshold=90.0
    )
    
    # Get current memory stats
    stats = monitor.get_stats()
    print(f"\nCurrent memory usage:")
    print(f"  Total: {stats.total_mb:.1f} MB")
    print(f"  Used: {stats.used_mb:.1f} MB")
    print(f"  Available: {stats.available_mb:.1f} MB")
    print(f"  Percent: {stats.percent:.1f}%")
    
    # Check if threshold exceeded
    if monitor.check_threshold('warning'):
        print("\n⚠ Warning threshold exceeded!")
    else:
        print("\n✓ Memory usage is normal")


def example_caching():
    """Example: Caching scraped data."""
    print("\n" + "=" * 80)
    print("Example 2: Caching Scraped Data")
    print("=" * 80)
    
    manager = MemoryManager(
        max_cache_size_mb=10,
        overflow_to_disk=True
    )
    
    # Simulate scraping and caching data
    print("\nScraping and caching data...")
    
    for i in range(5):
        url = f"https://example.com/page/{i}"
        
        # Check cache first
        cached_data = manager.get(url)
        
        if cached_data:
            print(f"  Cache HIT: {url}")
            data = cached_data
        else:
            print(f"  Cache MISS: {url} - fetching...")
            time.sleep(0.05)  # Simulate network delay
            data = {
                'url': url,
                'content': f"Page content {i}" * 100,
                'timestamp': time.time()
            }
            manager.set(url, data)
    
    # Get cache statistics
    stats = manager.get_cache_stats()
    print(f"\nCache statistics:")
    print(f"  Cached items: {stats['cache_items']}")
    print(f"  Cache size: {stats['cache_size_mb']:.2f} MB")
    print(f"  Disk files: {stats['disk_files']}")
    
    # Retrieve cached data
    print("\nRetrieving cached data...")
    for i in range(3):
        url = f"https://example.com/page/{i}"
        data = manager.get(url)
        if data:
            print(f"  ✓ Retrieved: {url}")


def example_chunked_processing():
    """Example: Processing large datasets in chunks."""
    print("\n" + "=" * 80)
    print("Example 3: Chunked Processing")
    print("=" * 80)
    
    manager = MemoryManager()
    
    # Simulate large dataset
    large_dataset = range(1000)
    
    print(f"\nProcessing {len(large_dataset)} items in chunks...")
    
    processed_count = 0
    for chunk in manager.chunked_iterator(iter(large_dataset), chunk_size=100):
        # Process chunk
        results = [x ** 2 for x in chunk]
        processed_count += len(results)
        
        # Save chunk results (in memory-efficient way)
        manager.set(f'chunk_{processed_count // 100}', results)
        
        print(f"  Processed chunk: {len(chunk)} items (total: {processed_count})")
    
    print(f"\n✓ Processed all {processed_count} items efficiently")


def example_memory_efficient_context():
    """Example: Using memory-efficient context manager."""
    print("\n" + "=" * 80)
    print("Example 4: Memory-Efficient Context Manager")
    print("=" * 80)
    
    print("\nProcessing data with automatic cleanup...")
    
    with memory_efficient_context() as manager:
        # Simulate scraping large amounts of data
        for i in range(10):
            large_data = {
                'id': i,
                'content': 'x' * 10000,  # Large content
                'metadata': {'page': i}
            }
            manager.set(f'item_{i}', large_data)
        
        # Get stats
        stats = manager.get_cache_stats()
        print(f"\nDuring processing:")
        print(f"  Cached items: {stats['cache_items']}")
        print(f"  Cache size: {stats['cache_size_mb']:.2f} MB")
    
    # Context manager automatically cleaned up
    print("\n✓ Context exited - memory automatically cleaned up")


def example_disk_overflow():
    """Example: Handling large objects with disk overflow."""
    print("\n" + "=" * 80)
    print("Example 5: Disk Overflow for Large Objects")
    print("=" * 80)
    
    import tempfile
    
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = MemoryManager(
            max_cache_size_mb=1,  # Small cache
            overflow_to_disk=True,
            temp_dir=tmpdir
        )
        
        # Store large object that exceeds cache size
        large_object = {
            'data': 'x' * 1000000,  # ~1MB
            'metadata': 'Large dataset'
        }
        
        print("\nStoring large object...")
        manager.set('large_data', large_object, force_disk=True)
        
        stats = manager.get_cache_stats()
        print(f"  Cache items: {stats['cache_items']}")
        print(f"  Disk files: {stats['disk_files']}")
        
        # Retrieve from disk
        print("\nRetrieving from disk...")
        retrieved = manager.get('large_data')
        
        if retrieved:
            print(f"  ✓ Successfully retrieved large object from disk")
            print(f"  Size: {len(retrieved['data'])} bytes")


def example_streaming():
    """Example: Streaming large files."""
    print("\n" + "=" * 80)
    print("Example 6: Streaming Large Files")
    print("=" * 80)
    
    import tempfile
    
    # Create a temporary large file
    with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
        temp_file = Path(f.name)
        # Write 10MB of data
        for i in range(10):
            f.write(b'x' * (1024 * 1024))  # 1MB chunks
    
    try:
        manager = MemoryManager()
        
        print(f"\nStreaming file: {temp_file.name}")
        print(f"File size: {temp_file.stat().st_size / 1024 / 1024:.1f} MB")
        
        # Stream file in chunks
        chunk_count = 0
        total_bytes = 0
        
        for chunk in manager.stream_large_file(temp_file, chunk_size=1024*1024):
            chunk_count += 1
            total_bytes += len(chunk)
            # Process chunk here...
        
        print(f"\n✓ Streamed {chunk_count} chunks ({total_bytes / 1024 / 1024:.1f} MB total)")
        print("  Memory usage stayed low!")
        
    finally:
        # Cleanup
        temp_file.unlink()


def example_memory_cleanup():
    """Example: Manual memory cleanup."""
    print("\n" + "=" * 80)
    print("Example 7: Memory Cleanup")
    print("=" * 80)
    
    manager = MemoryManager(max_cache_size_mb=10)
    
    # Get initial memory
    stats_before = get_memory_stats()
    print(f"\nBefore processing:")
    print(f"  Memory used: {stats_before.used_mb:.1f} MB")
    
    # Simulate processing that uses memory
    for i in range(20):
        large_data = {'data': 'x' * 100000}
        manager.set(f'item_{i}', large_data)
    
    stats_during = get_memory_stats()
    print(f"\nDuring processing:")
    print(f"  Memory used: {stats_during.used_mb:.1f} MB")
    print(f"  Cached items: {len(manager.cache)}")
    
    # Force cleanup
    print("\nCleaning up...")
    manager.cleanup()
    
    stats_after = get_memory_stats()
    print(f"\nAfter cleanup:")
    print(f"  Memory used: {stats_after.used_mb:.1f} MB")
    print(f"  Freed: {(stats_during.used_mb - stats_after.used_mb):.1f} MB")


def example_practical_scraping():
    """Example: Practical memory-efficient scraping."""
    print("\n" + "=" * 80)
    print("Example 8: Practical Memory-Efficient Scraping")
    print("=" * 80)
    
    # Simulate scraping multiple pages with memory management
    def scrape_page(url, manager):
        """Scrape a page with caching."""
        # Check cache first
        cached = manager.get(url)
        if cached:
            return cached
        
        # Simulate scraping
        time.sleep(0.05)
        data = {
            'url': url,
            'title': f'Page for {url}',
            'content': 'Lorem ipsum ' * 1000
        }
        
        # Cache result
        manager.set(url, data)
        return data
    
    with MemoryManager(max_cache_size_mb=5) as manager:
        urls = [f"https://example.com/article/{i}" for i in range(20)]
        
        print(f"\nScraping {len(urls)} pages...")
        results = []
        
        for url in urls:
            result = scrape_page(url, manager)
            results.append(result)
        
        print(f"\n✓ Scraped {len(results)} pages")
        
        # Check memory usage
        stats = manager.get_cache_stats()
        print(f"\nMemory stats:")
        print(f"  Cached: {stats['cache_items']} pages")
        print(f"  Size: {stats['cache_size_mb']:.2f} MB")
        print(f"  Overflow to disk: {stats['disk_files']} files")


def main():
    """Run all examples."""
    print("\nMemory-Efficient Scraping Examples")
    print("=" * 80)
    
    try:
        example_basic_memory_monitoring()
        example_caching()
        example_chunked_processing()
        example_memory_efficient_context()
        example_memory_cleanup()
        example_practical_scraping()
        
        # These might create large temp files
        # example_disk_overflow()
        # example_streaming()
        
        print("\n" + "=" * 80)
        print("All examples completed successfully!")
        print("=" * 80)
        
    except KeyboardInterrupt:
        print("\n\nExamples interrupted by user")
    except Exception as e:
        print(f"\n\nError running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
