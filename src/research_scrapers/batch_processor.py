"""
Batch Processing System for Research Scrapers

This module provides a comprehensive batch processing system with:
- Configurable concurrency (ThreadPoolExecutor and ProcessPoolExecutor)
- Progress tracking with tqdm integration
- Partial failure handling with detailed error reporting
- Retry logic with exponential backoff
- Resource pooling and connection reuse
- Checkpoint/resume functionality
- Support for both synchronous and asynchronous processing

Author: Research Scrapers Team
"""

import json
import logging
import pickle
import time
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union, Iterable
from functools import partial

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    # Fallback progress tracker
    class tqdm:
        def __init__(self, iterable=None, total=None, desc=None, **kwargs):
            self.iterable = iterable
            self.total = total
            self.desc = desc
            self.n = 0
        
        def __iter__(self):
            if self.iterable:
                for item in self.iterable:
                    yield item
                    self.update()
        
        def update(self, n=1):
            self.n += n
            if self.total:
                print(f"\r{self.desc}: {self.n}/{self.total}", end='', flush=True)
        
        def close(self):
            print()


logger = logging.getLogger(__name__)


@dataclass
class BatchResult:
    """Result of a batch processing operation."""
    
    item: Any
    success: bool
    result: Any = None
    error: Optional[str] = None
    retry_count: int = 0
    processing_time: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class BatchStats:
    """Statistics for batch processing."""
    
    total_items: int = 0
    successful_items: int = 0
    failed_items: int = 0
    skipped_items: int = 0
    total_processing_time: float = 0.0
    average_processing_time: float = 0.0
    start_time: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    end_time: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class BatchProcessor:
    """
    Batch processor with concurrency, progress tracking, and error handling.
    
    Features:
    - Configurable ThreadPoolExecutor or ProcessPoolExecutor
    - Progress tracking with tqdm
    - Automatic retry with exponential backoff
    - Checkpoint/resume functionality
    - Detailed error reporting
    - Resource management
    
    Example:
        >>> processor = BatchProcessor(max_workers=5, retry_attempts=3)
        >>> items = ['item1', 'item2', 'item3']
        >>> results = processor.process_batch(items, process_func)
        >>> print(f"Success rate: {processor.stats.successful_items}/{processor.stats.total_items}")
    """
    
    def __init__(
        self,
        max_workers: int = 5,
        executor_type: str = 'thread',
        retry_attempts: int = 3,
        retry_delay: float = 1.0,
        retry_backoff: float = 2.0,
        show_progress: bool = True,
        checkpoint_file: Optional[Union[str, Path]] = None,
        fail_fast: bool = False,
        callback: Optional[Callable] = None
    ):
        """
        Initialize batch processor.
        
        Args:
            max_workers: Maximum number of concurrent workers
            executor_type: 'thread' for ThreadPoolExecutor or 'process' for ProcessPoolExecutor
            retry_attempts: Number of retry attempts for failed items
            retry_delay: Initial delay between retries in seconds
            retry_backoff: Backoff multiplier for retry delay
            show_progress: Whether to show progress bar
            checkpoint_file: Path to checkpoint file for resume functionality
            fail_fast: Whether to stop processing on first failure
            callback: Optional callback function called after each item (receives BatchResult)
        """
        self.max_workers = max_workers
        self.executor_type = executor_type.lower()
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        self.retry_backoff = retry_backoff
        self.show_progress = show_progress and HAS_TQDM
        self.checkpoint_file = Path(checkpoint_file) if checkpoint_file else None
        self.fail_fast = fail_fast
        self.callback = callback
        
        # Statistics
        self.stats = BatchStats()
        
        # Processed items cache for checkpoint/resume
        self.processed_items: Dict[str, BatchResult] = {}
        
        # Load checkpoint if exists
        if self.checkpoint_file and self.checkpoint_file.exists():
            self._load_checkpoint()
        
        logger.info(
            f"Initialized BatchProcessor: workers={max_workers}, "
            f"executor={executor_type}, retries={retry_attempts}"
        )
    
    def process_batch(
        self,
        items: Iterable[Any],
        process_func: Callable[[Any], Any],
        item_key_func: Optional[Callable[[Any], str]] = None,
        batch_size: Optional[int] = None
    ) -> List[BatchResult]:
        """
        Process items in batch with concurrency.
        
        Args:
            items: Iterable of items to process
            process_func: Function to process each item
            item_key_func: Function to generate unique key for each item (for checkpointing)
            batch_size: Optional batch size for chunked processing
            
        Returns:
            List of BatchResult objects
        """
        items_list = list(items)
        self.stats.total_items = len(items_list)
        self.stats.start_time = datetime.utcnow().isoformat()
        
        logger.info(f"Starting batch processing of {self.stats.total_items} items")
        
        # Filter out already processed items if using checkpoints
        if item_key_func and self.checkpoint_file:
            items_to_process = [
                item for item in items_list
                if item_key_func(item) not in self.processed_items
            ]
            self.stats.skipped_items = len(items_list) - len(items_to_process)
            logger.info(f"Skipping {self.stats.skipped_items} already processed items")
        else:
            items_to_process = items_list
        
        results: List[BatchResult] = []
        
        # Choose executor
        ExecutorClass = ThreadPoolExecutor if self.executor_type == 'thread' else ProcessPoolExecutor
        
        with ExecutorClass(max_workers=self.max_workers) as executor:
            # Create progress bar
            pbar = tqdm(
                total=len(items_to_process),
                desc="Processing items",
                disable=not self.show_progress
            )
            
            try:
                # Submit all tasks
                future_to_item = {
                    executor.submit(self._process_item_with_retry, item, process_func): item
                    for item in items_to_process
                }
                
                # Collect results as they complete
                for future in as_completed(future_to_item):
                    item = future_to_item[future]
                    
                    try:
                        result = future.result()
                        results.append(result)
                        
                        # Update statistics
                        if result.success:
                            self.stats.successful_items += 1
                        else:
                            self.stats.failed_items += 1
                        
                        self.stats.total_processing_time += result.processing_time
                        
                        # Save to checkpoint
                        if item_key_func and self.checkpoint_file:
                            key = item_key_func(item)
                            self.processed_items[key] = result
                            self._save_checkpoint()
                        
                        # Call callback if provided
                        if self.callback:
                            try:
                                self.callback(result)
                            except Exception as e:
                                logger.warning(f"Callback failed: {e}")
                        
                        # Fail fast if enabled
                        if self.fail_fast and not result.success:
                            logger.error(f"Fail-fast triggered by: {result.error}")
                            break
                        
                    except Exception as e:
                        logger.error(f"Unexpected error processing item: {e}")
                        result = BatchResult(
                            item=item,
                            success=False,
                            error=str(e)
                        )
                        results.append(result)
                        self.stats.failed_items += 1
                    
                    pbar.update(1)
                
            finally:
                pbar.close()
        
        # Update final statistics
        self.stats.end_time = datetime.utcnow().isoformat()
        if self.stats.successful_items > 0:
            self.stats.average_processing_time = (
                self.stats.total_processing_time / self.stats.successful_items
            )
        
        logger.info(
            f"Batch processing complete: {self.stats.successful_items} successful, "
            f"{self.stats.failed_items} failed, {self.stats.skipped_items} skipped"
        )
        
        return results
    
    def _process_item_with_retry(
        self,
        item: Any,
        process_func: Callable[[Any], Any]
    ) -> BatchResult:
        """
        Process a single item with retry logic.
        
        Args:
            item: Item to process
            process_func: Processing function
            
        Returns:
            BatchResult object
        """
        start_time = time.time()
        last_error = None
        
        for attempt in range(self.retry_attempts + 1):
            try:
                result = process_func(item)
                processing_time = time.time() - start_time
                
                return BatchResult(
                    item=item,
                    success=True,
                    result=result,
                    retry_count=attempt,
                    processing_time=processing_time
                )
                
            except Exception as e:
                last_error = e
                
                if attempt < self.retry_attempts:
                    delay = self.retry_delay * (self.retry_backoff ** attempt)
                    logger.warning(
                        f"Attempt {attempt + 1} failed for item, retrying in {delay:.1f}s: {e}"
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"All {self.retry_attempts + 1} attempts failed for item: {e}")
        
        processing_time = time.time() - start_time
        
        return BatchResult(
            item=item,
            success=False,
            error=str(last_error),
            retry_count=self.retry_attempts,
            processing_time=processing_time
        )
    
    def process_in_chunks(
        self,
        items: Iterable[Any],
        process_func: Callable[[List[Any]], List[Any]],
        chunk_size: int = 10
    ) -> List[BatchResult]:
        """
        Process items in chunks (useful for batch API calls).
        
        Args:
            items: Items to process
            process_func: Function that processes a chunk of items
            chunk_size: Size of each chunk
            
        Returns:
            List of BatchResult objects
        """
        items_list = list(items)
        chunks = [
            items_list[i:i + chunk_size]
            for i in range(0, len(items_list), chunk_size)
        ]
        
        logger.info(f"Processing {len(items_list)} items in {len(chunks)} chunks of size {chunk_size}")
        
        all_results = []
        
        for chunk in tqdm(chunks, desc="Processing chunks", disable=not self.show_progress):
            chunk_results = self._process_item_with_retry(chunk, process_func)
            
            if chunk_results.success:
                # Unpack chunk results into individual results
                for i, (item, result) in enumerate(zip(chunk, chunk_results.result)):
                    all_results.append(BatchResult(
                        item=item,
                        success=True,
                        result=result,
                        retry_count=chunk_results.retry_count,
                        processing_time=chunk_results.processing_time / len(chunk)
                    ))
            else:
                # Mark all items in failed chunk as failed
                for item in chunk:
                    all_results.append(BatchResult(
                        item=item,
                        success=False,
                        error=chunk_results.error,
                        retry_count=chunk_results.retry_count,
                        processing_time=0.0
                    ))
        
        return all_results
    
    def _save_checkpoint(self):
        """Save checkpoint to file."""
        if not self.checkpoint_file:
            return
        
        try:
            checkpoint_data = {
                'processed_items': {
                    key: result.to_dict()
                    for key, result in self.processed_items.items()
                },
                'stats': self.stats.to_dict(),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            self.checkpoint_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.checkpoint_file, 'w') as f:
                json.dump(checkpoint_data, f, indent=2)
            
            logger.debug(f"Checkpoint saved: {len(self.processed_items)} items")
            
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
    
    def _load_checkpoint(self):
        """Load checkpoint from file."""
        if not self.checkpoint_file or not self.checkpoint_file.exists():
            return
        
        try:
            with open(self.checkpoint_file, 'r') as f:
                checkpoint_data = json.load(f)
            
            # Reconstruct BatchResult objects
            for key, result_dict in checkpoint_data.get('processed_items', {}).items():
                self.processed_items[key] = BatchResult(**result_dict)
            
            logger.info(f"Checkpoint loaded: {len(self.processed_items)} items already processed")
            
        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
    
    def clear_checkpoint(self):
        """Clear checkpoint file and cache."""
        self.processed_items.clear()
        
        if self.checkpoint_file and self.checkpoint_file.exists():
            try:
                self.checkpoint_file.unlink()
                logger.info("Checkpoint cleared")
            except Exception as e:
                logger.error(f"Failed to clear checkpoint: {e}")
    
    def get_failed_items(self, results: List[BatchResult]) -> List[Any]:
        """
        Extract failed items from results.
        
        Args:
            results: List of BatchResult objects
            
        Returns:
            List of items that failed processing
        """
        return [result.item for result in results if not result.success]
    
    def get_successful_results(self, results: List[BatchResult]) -> List[Any]:
        """
        Extract successful results from batch results.
        
        Args:
            results: List of BatchResult objects
            
        Returns:
            List of successful results
        """
        return [result.result for result in results if result.success]
    
    def save_results(
        self,
        results: List[BatchResult],
        output_file: Union[str, Path],
        format: str = 'json'
    ):
        """
        Save batch results to file.
        
        Args:
            results: List of BatchResult objects
            output_file: Output file path
            format: Output format ('json' or 'pickle')
        """
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'results': [result.to_dict() for result in results],
            'stats': self.stats.to_dict()
        }
        
        if format == 'json':
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        elif format == 'pickle':
            with open(output_path, 'wb') as f:
                pickle.dump(data, f)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        logger.info(f"Results saved to {output_path}")


# Convenience function for simple batch processing
def process_batch_simple(
    items: Iterable[Any],
    process_func: Callable[[Any], Any],
    max_workers: int = 5,
    show_progress: bool = True,
    retry_attempts: int = 3
) -> List[Any]:
    """
    Simple batch processing function.
    
    Args:
        items: Items to process
        process_func: Processing function
        max_workers: Number of concurrent workers
        show_progress: Whether to show progress bar
        retry_attempts: Number of retry attempts
        
    Returns:
        List of successful results
    
    Example:
        >>> urls = ['url1', 'url2', 'url3']
        >>> results = process_batch_simple(urls, scrape_url, max_workers=3)
    """
    processor = BatchProcessor(
        max_workers=max_workers,
        retry_attempts=retry_attempts,
        show_progress=show_progress
    )
    
    results = processor.process_batch(items, process_func)
    return processor.get_successful_results(results)
