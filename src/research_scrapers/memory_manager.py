"""
Memory Management System for Research Scrapers

This module provides comprehensive memory management utilities:
- Streaming support for large datasets using generators
- Memory monitoring with configurable thresholds
- Chunked processing for large files and API responses
- Automatic memory cleanup and garbage collection
- Memory profiling utilities
- Context managers for automatic resource cleanup
- Cache management with LRU eviction
- Large object handling with disk-based overflow

Author: Research Scrapers Team
"""

import gc
import logging
import os
import pickle
import tempfile
import weakref
from collections import OrderedDict
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Generator, Iterator, List, Optional, Union

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

logger = logging.getLogger(__name__)


@dataclass
class MemoryStats:
    """Memory usage statistics."""
    
    total_mb: float
    available_mb: float
    used_mb: float
    percent: float
    
    def __str__(self) -> str:
        return (
            f"Memory: {self.used_mb:.1f}MB used / {self.total_mb:.1f}MB total "
            f"({self.percent:.1f}%)"
        )


class MemoryMonitor:
    """
    Monitor memory usage with configurable thresholds and alerts.
    
    Example:
        >>> monitor = MemoryMonitor(warning_threshold=80.0, critical_threshold=90.0)
        >>> stats = monitor.get_stats()
        >>> if monitor.check_threshold():
        >>>     print("Memory threshold exceeded!")
    """
    
    def __init__(
        self,
        warning_threshold: float = 80.0,
        critical_threshold: float = 90.0,
        callback: Optional[Callable[[MemoryStats], None]] = None
    ):
        """
        Initialize memory monitor.
        
        Args:
            warning_threshold: Percentage threshold for warnings (0-100)
            critical_threshold: Percentage threshold for critical alerts (0-100)
            callback: Optional callback function called when threshold exceeded
        """
        if not HAS_PSUTIL:
            logger.warning("psutil not available, memory monitoring will be limited")
        
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self.callback = callback
    
    def get_stats(self) -> MemoryStats:
        """
        Get current memory statistics.
        
        Returns:
            MemoryStats object
        """
        if HAS_PSUTIL:
            mem = psutil.virtual_memory()
            return MemoryStats(
                total_mb=mem.total / 1024 / 1024,
                available_mb=mem.available / 1024 / 1024,
                used_mb=mem.used / 1024 / 1024,
                percent=mem.percent
            )
        else:
            # Fallback: basic estimation
            return MemoryStats(
                total_mb=0.0,
                available_mb=0.0,
                used_mb=0.0,
                percent=0.0
            )
    
    def check_threshold(self, level: str = 'warning') -> bool:
        """
        Check if memory usage exceeds threshold.
        
        Args:
            level: 'warning' or 'critical'
            
        Returns:
            True if threshold exceeded
        """
        stats = self.get_stats()
        threshold = self.critical_threshold if level == 'critical' else self.warning_threshold
        
        if stats.percent >= threshold:
            logger.warning(f"Memory {level}: {stats}")
            
            if self.callback:
                try:
                    self.callback(stats)
                except Exception as e:
                    logger.error(f"Memory callback failed: {e}")
            
            return True
        
        return False
    
    def log_stats(self):
        """Log current memory statistics."""
        stats = self.get_stats()
        logger.info(f"Memory usage: {stats}")


class MemoryManager:
    """
    Comprehensive memory manager with caching, cleanup, and monitoring.
    
    Features:
    - LRU cache with size limits
    - Automatic memory cleanup
    - Disk-based overflow for large objects
    - Memory profiling
    - Context managers for resource cleanup
    
    Example:
        >>> manager = MemoryManager(max_cache_size_mb=100)
        >>> manager.set('key', large_data)
        >>> data = manager.get('key')
        >>> manager.cleanup()
    """
    
    def __init__(
        self,
        max_cache_size_mb: float = 500.0,
        overflow_to_disk: bool = True,
        temp_dir: Optional[Union[str, Path]] = None,
        auto_cleanup: bool = True,
        warning_threshold: float = 80.0
    ):
        """
        Initialize memory manager.
        
        Args:
            max_cache_size_mb: Maximum cache size in megabytes
            overflow_to_disk: Whether to overflow large objects to disk
            temp_dir: Directory for temporary files (None = system temp)
            auto_cleanup: Whether to auto-cleanup on threshold
            warning_threshold: Memory warning threshold percentage
        """
        self.max_cache_size_bytes = int(max_cache_size_mb * 1024 * 1024)
        self.overflow_to_disk = overflow_to_disk
        self.temp_dir = Path(temp_dir) if temp_dir else Path(tempfile.gettempdir())
        self.auto_cleanup = auto_cleanup
        
        # LRU cache
        self.cache: OrderedDict[str, Any] = OrderedDict()
        self.cache_sizes: Dict[str, int] = {}
        self.current_cache_size = 0
        
        # Disk overflow tracking
        self.disk_files: Dict[str, Path] = {}
        
        # Memory monitor
        self.monitor = MemoryMonitor(warning_threshold=warning_threshold)
        
        # Weak references for cleanup
        self.tracked_objects: weakref.WeakSet = weakref.WeakSet()
        
        logger.info(
            f"MemoryManager initialized: max_cache={max_cache_size_mb}MB, "
            f"overflow={overflow_to_disk}"
        )
    
    def set(self, key: str, value: Any, force_disk: bool = False) -> bool:
        """
        Store value in cache or disk.
        
        Args:
            key: Cache key
            value: Value to store
            force_disk: Force storage to disk
            
        Returns:
            True if stored successfully
        """
        # Estimate size
        try:
            size = self._estimate_size(value)
        except Exception as e:
            logger.warning(f"Failed to estimate size: {e}")
            size = 1024  # Default estimate
        
        # Check if value is too large for cache or force_disk
        if force_disk or size > self.max_cache_size_bytes / 2:
            return self._store_to_disk(key, value)
        
        # Evict items if necessary
        while (self.current_cache_size + size > self.max_cache_size_bytes and
               len(self.cache) > 0):
            self._evict_lru()
        
        # Store in cache
        if key in self.cache:
            # Update existing
            self.current_cache_size -= self.cache_sizes.get(key, 0)
            del self.cache[key]
        
        self.cache[key] = value
        self.cache_sizes[key] = size
        self.current_cache_size += size
        
        logger.debug(f"Cached '{key}': {size / 1024:.1f}KB")
        
        # Check memory threshold
        if self.auto_cleanup and self.monitor.check_threshold():
            self.cleanup()
        
        return True
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieve value from cache or disk.
        
        Args:
            key: Cache key
            default: Default value if key not found
            
        Returns:
            Cached value or default
        """
        # Check cache first
        if key in self.cache:
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            return self.cache[key]
        
        # Check disk overflow
        if key in self.disk_files:
            return self._load_from_disk(key)
        
        return default
    
    def delete(self, key: str) -> bool:
        """
        Delete value from cache or disk.
        
        Args:
            key: Cache key
            
        Returns:
            True if deleted
        """
        deleted = False
        
        # Remove from cache
        if key in self.cache:
            self.current_cache_size -= self.cache_sizes.get(key, 0)
            del self.cache[key]
            del self.cache_sizes[key]
            deleted = True
        
        # Remove from disk
        if key in self.disk_files:
            try:
                self.disk_files[key].unlink()
                del self.disk_files[key]
                deleted = True
            except Exception as e:
                logger.error(f"Failed to delete disk file for '{key}': {e}")
        
        return deleted
    
    def clear(self):
        """Clear all cache and disk files."""
        self.cache.clear()
        self.cache_sizes.clear()
        self.current_cache_size = 0
        
        for path in self.disk_files.values():
            try:
                path.unlink()
            except Exception as e:
                logger.error(f"Failed to delete {path}: {e}")
        
        self.disk_files.clear()
        logger.info("Memory cache cleared")
    
    def cleanup(self, force_gc: bool = True):
        """
        Perform memory cleanup.
        
        Args:
            force_gc: Whether to force garbage collection
        """
        logger.info("Performing memory cleanup...")
        
        # Clear weak references
        self.tracked_objects.clear()
        
        # Force garbage collection
        if force_gc:
            gc.collect()
        
        stats_before = self.monitor.get_stats()
        logger.info(f"Before cleanup: {stats_before}")
        
        if force_gc:
            gc.collect()
            stats_after = self.monitor.get_stats()
            logger.info(f"After cleanup: {stats_after}")
            logger.info(
                f"Freed: {(stats_before.used_mb - stats_after.used_mb):.1f}MB"
            )
    
    def stream_large_file(
        self,
        file_path: Union[str, Path],
        chunk_size: int = 8192
    ) -> Generator[bytes, None, None]:
        """
        Stream large file in chunks.
        
        Args:
            file_path: Path to file
            chunk_size: Size of each chunk in bytes
            
        Yields:
            Chunks of file data
        """
        file_path = Path(file_path)
        
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                yield chunk
    
    def chunked_iterator(
        self,
        iterable: Iterator[Any],
        chunk_size: int = 100
    ) -> Generator[List[Any], None, None]:
        """
        Iterate over data in chunks to manage memory.
        
        Args:
            iterable: Iterable to chunk
            chunk_size: Size of each chunk
            
        Yields:
            Lists of items
        """
        chunk = []
        
        for item in iterable:
            chunk.append(item)
            
            if len(chunk) >= chunk_size:
                yield chunk
                chunk = []
        
        # Yield remaining items
        if chunk:
            yield chunk
    
    @contextmanager
    def managed_resource(self, resource: Any):
        """
        Context manager for automatic resource cleanup.
        
        Args:
            resource: Resource to manage
            
        Yields:
            Managed resource
        """
        try:
            self.tracked_objects.add(resource)
            yield resource
        finally:
            # Cleanup
            if hasattr(resource, 'close'):
                try:
                    resource.close()
                except Exception as e:
                    logger.error(f"Failed to close resource: {e}")
            
            # Remove from tracking
            try:
                self.tracked_objects.remove(resource)
            except KeyError:
                pass
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        return {
            'cache_items': len(self.cache),
            'cache_size_mb': self.current_cache_size / 1024 / 1024,
            'max_cache_size_mb': self.max_cache_size_bytes / 1024 / 1024,
            'disk_files': len(self.disk_files),
            'memory_stats': self.monitor.get_stats().__dict__
        }
    
    def _evict_lru(self):
        """Evict least recently used item from cache."""
        if not self.cache:
            return
        
        key, _ = self.cache.popitem(last=False)  # FIFO: remove first item
        size = self.cache_sizes.pop(key, 0)
        self.current_cache_size -= size
        
        logger.debug(f"Evicted '{key}' from cache: {size / 1024:.1f}KB")
    
    def _store_to_disk(self, key: str, value: Any) -> bool:
        """Store value to disk."""
        if not self.overflow_to_disk:
            logger.warning(f"Cannot store '{key}' to disk: overflow disabled")
            return False
        
        try:
            # Create temp file
            self.temp_dir.mkdir(parents=True, exist_ok=True)
            temp_file = self.temp_dir / f"cache_{key}.pkl"
            
            with open(temp_file, 'wb') as f:
                pickle.dump(value, f)
            
            self.disk_files[key] = temp_file
            logger.debug(f"Stored '{key}' to disk: {temp_file}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to store '{key}' to disk: {e}")
            return False
    
    def _load_from_disk(self, key: str) -> Any:
        """Load value from disk."""
        if key not in self.disk_files:
            return None
        
        try:
            with open(self.disk_files[key], 'rb') as f:
                value = pickle.load(f)
            
            logger.debug(f"Loaded '{key}' from disk")
            return value
            
        except Exception as e:
            logger.error(f"Failed to load '{key}' from disk: {e}")
            return None
    
    def _estimate_size(self, obj: Any) -> int:
        """
        Estimate size of object in bytes.
        
        Args:
            obj: Object to measure
            
        Returns:
            Estimated size in bytes
        """
        # Try pickle size first (most accurate)
        try:
            return len(pickle.dumps(obj))
        except Exception:
            pass
        
        # Fallback to sys.getsizeof
        import sys
        return sys.getsizeof(obj)
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()
        return False
    
    def __del__(self):
        """Destructor."""
        try:
            self.clear()
        except Exception:
            pass


# Convenience functions
def get_memory_stats() -> MemoryStats:
    """
    Get current memory statistics.
    
    Returns:
        MemoryStats object
    """
    monitor = MemoryMonitor()
    return monitor.get_stats()


def force_cleanup():
    """Force garbage collection and memory cleanup."""
    gc.collect()
    logger.info("Forced memory cleanup completed")


@contextmanager
def memory_efficient_context(cleanup_on_exit: bool = True):
    """
    Context manager for memory-efficient operations.
    
    Args:
        cleanup_on_exit: Whether to cleanup memory on exit
        
    Yields:
        MemoryManager instance
    
    Example:
        >>> with memory_efficient_context() as manager:
        >>>     large_data = load_large_file()
        >>>     manager.set('data', large_data)
        >>>     process_data(manager.get('data'))
    """
    manager = MemoryManager(auto_cleanup=True)
    
    try:
        yield manager
    finally:
        if cleanup_on_exit:
            manager.cleanup()
