#!/usr/bin/env python3
"""
Batch Processing Example

This example demonstrates how to use the BatchProcessor for efficient
concurrent processing of multiple items with retry logic, progress tracking,
and error handling.

Features demonstrated:
- Basic batch processing with concurrency
- Retry logic for failed items
- Progress tracking
- Checkpoint/resume functionality
- Error reporting
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src' / 'research_scrapers'))

from batch_processor import BatchProcessor, process_batch_simple


def simulate_api_call(url: str) -> dict:
    """
    Simulate an API call that might fail sometimes.
    
    Args:
        url: URL to fetch
        
    Returns:
        Dictionary with results
    """
    # Simulate network delay
    time.sleep(0.1)
    
    # Simulate occasional failures
    import random
    if random.random() < 0.2:  # 20% failure rate
        raise ValueError(f"Failed to fetch {url}")
    
    return {
        'url': url,
        'status': 200,
        'data': f"Data from {url}",
        'timestamp': time.time()
    }


def example_basic_batch_processing():
    """Example: Basic batch processing with retry."""
    print("=" * 80)
    print("Example 1: Basic Batch Processing")
    print("=" * 80)
    
    urls = [
        "https://api.example.com/users/1",
        "https://api.example.com/users/2",
        "https://api.example.com/users/3",
        "https://api.example.com/users/4",
        "https://api.example.com/users/5",
    ]
    
    # Create batch processor
    processor = BatchProcessor(
        max_workers=3,
        retry_attempts=2,
        retry_delay=0.5,
        show_progress=True
    )
    
    # Process items
    results = processor.process_batch(urls, simulate_api_call)
    
    # Print results
    print(f"\nProcessing complete!")
    print(f"Total items: {processor.stats.total_items}")
    print(f"Successful: {processor.stats.successful_items}")
    print(f"Failed: {processor.stats.failed_items}")
    print(f"Average processing time: {processor.stats.average_processing_time:.2f}s")
    
    # Show successful results
    successful_results = processor.get_successful_results(results)
    print(f"\nSuccessful results: {len(successful_results)}")
    
    # Show failed items
    failed_items = processor.get_failed_items(results)
    if failed_items:
        print(f"\nFailed items: {failed_items}")


def example_with_checkpoint():
    """Example: Batch processing with checkpoint/resume."""
    print("\n" + "=" * 80)
    print("Example 2: Batch Processing with Checkpoint/Resume")
    print("=" * 80)
    
    import tempfile
    
    urls = [f"https://api.example.com/items/{i}" for i in range(1, 11)]
    
    with tempfile.TemporaryDirectory() as tmpdir:
        checkpoint_file = Path(tmpdir) / 'checkpoint.json'
        
        # First run - process some items
        print("\nFirst run: Processing 10 items...")
        processor1 = BatchProcessor(
            max_workers=2,
            checkpoint_file=checkpoint_file,
            show_progress=True,
            retry_attempts=1
        )
        
        results1 = processor1.process_batch(
            urls[:7],  # Process only first 7
            simulate_api_call,
            item_key_func=lambda url: url
        )
        
        print(f"First run complete: {processor1.stats.successful_items} successful")
        
        # Second run - resume and process remaining
        print("\nSecond run: Resuming from checkpoint...")
        processor2 = BatchProcessor(
            max_workers=2,
            checkpoint_file=checkpoint_file,
            show_progress=True,
            retry_attempts=1
        )
        
        results2 = processor2.process_batch(
            urls,  # All items, but will skip already processed
            simulate_api_call,
            item_key_func=lambda url: url
        )
        
        print(f"Second run complete:")
        print(f"  Skipped (already processed): {processor2.stats.skipped_items}")
        print(f"  Newly processed: {len([r for r in results2 if r.item not in urls[:7]])}")


def example_simple_processing():
    """Example: Simple batch processing without detailed setup."""
    print("\n" + "=" * 80)
    print("Example 3: Simple Batch Processing")
    print("=" * 80)
    
    def square(x):
        return x ** 2
    
    numbers = list(range(1, 21))
    
    # Use the simple convenience function
    results = process_batch_simple(
        numbers,
        square,
        max_workers=4,
        show_progress=True,
        retry_attempts=2
    )
    
    print(f"\nProcessed {len(results)} numbers")
    print(f"Results: {results[:10]}...")  # Show first 10


def example_with_callback():
    """Example: Batch processing with custom callback."""
    print("\n" + "=" * 80)
    print("Example 4: Batch Processing with Callback")
    print("=" * 80)
    
    progress_log = []
    
    def progress_callback(result):
        """Custom callback to track progress."""
        if result.success:
            progress_log.append(f"✓ {result.item}")
        else:
            progress_log.append(f"✗ {result.item}: {result.error}")
    
    processor = BatchProcessor(
        max_workers=2,
        callback=progress_callback,
        show_progress=True,
        retry_attempts=1
    )
    
    items = [f"task_{i}" for i in range(1, 6)]
    
    def process_task(task):
        time.sleep(0.05)
        return f"Result for {task}"
    
    results = processor.process_batch(items, process_task)
    
    print("\nProgress log:")
    for log_entry in progress_log:
        print(f"  {log_entry}")


def example_chunked_processing():
    """Example: Processing items in chunks (useful for batch APIs)."""
    print("\n" + "=" * 80)
    print("Example 5: Chunked Processing")
    print("=" * 80)
    
    def batch_api_call(items_chunk):
        """
        Simulate a batch API call that processes multiple items at once.
        
        Args:
            items_chunk: List of items to process
            
        Returns:
            List of results
        """
        time.sleep(0.1)  # Simulate API call
        return [f"Processed: {item}" for item in items_chunk]
    
    items = [f"item_{i}" for i in range(1, 26)]
    
    processor = BatchProcessor(
        max_workers=3,
        show_progress=True
    )
    
    results = processor.process_in_chunks(
        items,
        batch_api_call,
        chunk_size=5
    )
    
    print(f"\nProcessed {len(results)} items in chunks of 5")
    print(f"Successful: {len([r for r in results if r.success])}")


def example_save_results():
    """Example: Saving results to a file."""
    print("\n" + "=" * 80)
    print("Example 6: Saving Results")
    print("=" * 80)
    
    import tempfile
    
    processor = BatchProcessor(max_workers=2, show_progress=False)
    
    def process_item(x):
        return {'number': x, 'square': x ** 2}
    
    items = list(range(1, 11))
    results = processor.process_batch(items, process_item)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_file = Path(tmpdir) / 'results.json'
        
        # Save results
        processor.save_results(results, output_file, format='json')
        
        print(f"\nResults saved to: {output_file}")
        print(f"File size: {output_file.stat().st_size} bytes")
        
        # Show file contents
        import json
        with open(output_file) as f:
            data = json.load(f)
        
        print(f"Saved {len(data['results'])} results")
        print(f"Statistics: {data['stats']}")


def main():
    """Run all examples."""
    print("\nBatch Processing Examples")
    print("=" * 80)
    
    try:
        example_basic_batch_processing()
        example_simple_processing()
        example_with_callback()
        example_chunked_processing()
        example_save_results()
        
        # This one might take a bit longer
        # example_with_checkpoint()
        
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
