"""
Unit tests for BatchProcessor class.

Tests cover:
- Basic batch processing
- Concurrency (thread and process)
- Retry logic
- Progress tracking
- Checkpoint/resume functionality
- Error handling
- Metrics collection
"""

import pytest
import time
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

# Add src to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from research_scrapers.batch_processor import (
    BatchProcessor,
    BatchResult,
    BatchStats,
    process_batch_simple
)


class TestBatchProcessor:
    """Test suite for BatchProcessor."""
    
    def test_initialization(self):
        """Test batch processor initialization."""
        processor = BatchProcessor(
            max_workers=3,
            retry_attempts=2,
            show_progress=False
        )
        
        assert processor.max_workers == 3
        assert processor.retry_attempts == 2
        assert processor.show_progress == False
        assert isinstance(processor.stats, BatchStats)
    
    def test_basic_batch_processing(self):
        """Test basic batch processing with successful items."""
        processor = BatchProcessor(max_workers=2, show_progress=False)
        
        def process_item(x):
            return x * 2
        
        items = [1, 2, 3, 4, 5]
        results = processor.process_batch(items, process_item)
        
        assert len(results) == 5
        assert all(r.success for r in results)
        assert [r.result for r in results] == [2, 4, 6, 8, 10]
        assert processor.stats.successful_items == 5
        assert processor.stats.failed_items == 0
    
    def test_batch_processing_with_failures(self):
        """Test batch processing with some failures."""
        processor = BatchProcessor(max_workers=2, retry_attempts=0, show_progress=False)
        
        def process_item(x):
            if x == 3:
                raise ValueError("Test error")
            return x * 2
        
        items = [1, 2, 3, 4, 5]
        results = processor.process_batch(items, process_item)
        
        assert len(results) == 5
        assert processor.stats.successful_items == 4
        assert processor.stats.failed_items == 1
        
        # Check failed item
        failed = [r for r in results if not r.success]
        assert len(failed) == 1
        assert failed[0].item == 3
        assert "Test error" in failed[0].error
    
    def test_retry_logic(self):
        """Test retry logic with exponential backoff."""
        processor = BatchProcessor(
            max_workers=1,
            retry_attempts=3,
            retry_delay=0.1,
            show_progress=False
        )
        
        call_count = {}
        
        def process_item(x):
            call_count[x] = call_count.get(x, 0) + 1
            if call_count[x] < 3:  # Fail first 2 attempts
                raise ValueError("Temporary error")
            return x * 2
        
        items = [1]
        results = processor.process_batch(items, process_item)
        
        assert results[0].success
        assert results[0].retry_count == 2  # Failed 2 times before success
        assert call_count[1] == 3
    
    def test_max_retries_exceeded(self):
        """Test behavior when max retries are exceeded."""
        processor = BatchProcessor(
            max_workers=1,
            retry_attempts=2,
            retry_delay=0.05,
            show_progress=False
        )
        
        def always_fails(x):
            raise ValueError("Always fails")
        
        items = [1]
        results = processor.process_batch(items, always_fails)
        
        assert not results[0].success
        assert results[0].retry_count == 2
        assert "Always fails" in results[0].error
    
    def test_thread_executor(self):
        """Test with ThreadPoolExecutor."""
        processor = BatchProcessor(
            max_workers=3,
            executor_type='thread',
            show_progress=False
        )
        
        def process_item(x):
            time.sleep(0.01)  # Simulate work
            return x * 2
        
        items = list(range(10))
        start_time = time.time()
        results = processor.process_batch(items, process_item)
        elapsed = time.time() - start_time
        
        assert all(r.success for r in results)
        # With 3 workers, should be faster than serial processing
        assert elapsed < 0.1  # Should take < 100ms for 10 items with 0.01s each
    
    def test_process_executor(self):
        """Test with ProcessPoolExecutor."""
        processor = BatchProcessor(
            max_workers=2,
            executor_type='process',
            show_progress=False
        )
        
        def process_item(x):
            return x ** 2
        
        items = [1, 2, 3, 4]
        results = processor.process_batch(items, process_item)
        
        assert all(r.success for r in results)
        assert [r.result for r in results] == [1, 4, 9, 16]
    
    def test_checkpoint_functionality(self):
        """Test checkpoint save/resume functionality."""
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_file = Path(tmpdir) / 'checkpoint.json'
            
            # First run - process some items
            processor1 = BatchProcessor(
                max_workers=2,
                checkpoint_file=checkpoint_file,
                show_progress=False
            )
            
            def process_item(x):
                return x * 2
            
            def item_key_func(x):
                return f"item_{x}"
            
            items = [1, 2, 3]
            results1 = processor1.process_batch(
                items,
                process_item,
                item_key_func=item_key_func
            )
            
            assert all(r.success for r in results1)
            assert checkpoint_file.exists()
            
            # Second run - should skip already processed items
            processor2 = BatchProcessor(
                max_workers=2,
                checkpoint_file=checkpoint_file,
                show_progress=False
            )
            
            items = [1, 2, 3, 4, 5]  # Include previously processed items
            results2 = processor2.process_batch(
                items,
                process_item,
                item_key_func=item_key_func
            )
            
            # Should have skipped 3 items
            assert processor2.stats.skipped_items == 3
            # Should have processed 2 new items
            new_results = [r for r in results2 if r.item in [4, 5]]
            assert len(new_results) == 2
    
    def test_fail_fast(self):
        """Test fail-fast behavior."""
        processor = BatchProcessor(
            max_workers=2,
            fail_fast=True,
            retry_attempts=0,
            show_progress=False
        )
        
        def process_item(x):
            if x == 2:
                raise ValueError("Stop here")
            return x * 2
        
        items = [1, 2, 3, 4, 5]
        results = processor.process_batch(items, process_item)
        
        # Should stop after hitting failure
        assert len(results) < 5  # Not all items processed
        assert processor.stats.failed_items >= 1
    
    def test_callback(self):
        """Test callback functionality."""
        callback_results = []
        
        def callback(result):
            callback_results.append(result)
        
        processor = BatchProcessor(
            max_workers=2,
            callback=callback,
            show_progress=False
        )
        
        def process_item(x):
            return x * 2
        
        items = [1, 2, 3]
        results = processor.process_batch(items, process_item)
        
        assert len(callback_results) == 3
        assert all(isinstance(r, BatchResult) for r in callback_results)
    
    def test_get_failed_items(self):
        """Test extracting failed items."""
        processor = BatchProcessor(max_workers=2, retry_attempts=0, show_progress=False)
        
        def process_item(x):
            if x % 2 == 0:
                raise ValueError("Even number")
            return x * 2
        
        items = [1, 2, 3, 4, 5]
        results = processor.process_batch(items, process_item)
        
        failed_items = processor.get_failed_items(results)
        assert failed_items == [2, 4]
    
    def test_get_successful_results(self):
        """Test extracting successful results."""
        processor = BatchProcessor(max_workers=2, retry_attempts=0, show_progress=False)
        
        def process_item(x):
            if x == 3:
                raise ValueError("Skip this")
            return x * 2
        
        items = [1, 2, 3, 4, 5]
        results = processor.process_batch(items, process_item)
        
        successful = processor.get_successful_results(results)
        assert successful == [2, 4, 8, 10]
    
    def test_chunked_processing(self):
        """Test chunked processing."""
        processor = BatchProcessor(max_workers=2, show_progress=False)
        
        def process_chunk(chunk):
            return [x * 2 for x in chunk]
        
        items = list(range(10))
        results = processor.process_in_chunks(items, process_chunk, chunk_size=3)
        
        successful = processor.get_successful_results(results)
        assert len(successful) == 10
    
    def test_save_results(self):
        """Test saving results to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = Path(tmpdir) / 'results.json'
            
            processor = BatchProcessor(max_workers=2, show_progress=False)
            
            def process_item(x):
                return x * 2
            
            items = [1, 2, 3]
            results = processor.process_batch(items, process_item)
            
            processor.save_results(results, output_file, format='json')
            
            assert output_file.exists()
            
            # Verify content
            import json
            with open(output_file) as f:
                data = json.load(f)
            
            assert 'results' in data
            assert 'stats' in data
            assert len(data['results']) == 3
    
    def test_metrics_collection(self):
        """Test metrics collection."""
        processor = BatchProcessor(max_workers=2, retry_attempts=0, show_progress=False)
        
        def process_item(x):
            if x == 3:
                raise ValueError("Fail")
            time.sleep(0.01)  # Simulate work
            return x * 2
        
        items = [1, 2, 3, 4, 5]
        results = processor.process_batch(items, process_item)
        
        stats = processor.stats
        assert stats.total_items == 5
        assert stats.successful_items == 4
        assert stats.failed_items == 1
        assert stats.total_processing_time > 0
        assert stats.average_processing_time > 0
        assert stats.start_time is not None
        assert stats.end_time is not None


class TestBatchResult:
    """Test BatchResult dataclass."""
    
    def test_batch_result_creation(self):
        """Test creating BatchResult."""
        result = BatchResult(
            item="test_item",
            success=True,
            result="test_result",
            retry_count=2,
            processing_time=1.5
        )
        
        assert result.item == "test_item"
        assert result.success == True
        assert result.result == "test_result"
        assert result.retry_count == 2
        assert result.processing_time == 1.5
    
    def test_batch_result_to_dict(self):
        """Test converting BatchResult to dict."""
        result = BatchResult(
            item="test",
            success=True,
            result="output"
        )
        
        result_dict = result.to_dict()
        assert isinstance(result_dict, dict)
        assert result_dict['item'] == "test"
        assert result_dict['success'] == True


class TestProcessBatchSimple:
    """Test convenience function."""
    
    def test_process_batch_simple(self):
        """Test simple batch processing."""
        def process_item(x):
            return x * 2
        
        items = [1, 2, 3, 4, 5]
        results = process_batch_simple(
            items,
            process_item,
            max_workers=2,
            show_progress=False
        )
        
        assert results == [2, 4, 6, 8, 10]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
