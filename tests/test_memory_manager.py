"""
Unit tests for MemoryManager class.

Tests cover:
- Cache operations (set/get/delete)
- LRU eviction
- Memory monitoring
- Disk overflow
- Chunked iteration
- Context managers
- Cleanup operations
"""

import pytest
import tempfile
from pathlib import Path
import sys
import gc

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from research_scrapers.memory_manager import (
    MemoryManager,
    MemoryMonitor,
    MemoryStats,
    memory_efficient_context,
    get_memory_stats,
    force_cleanup
)


class TestMemoryMonitor:
    """Test suite for MemoryMonitor."""
    
    def test_initialization(self):
        """Test monitor initialization."""
        monitor = MemoryMonitor(
            warning_threshold=75.0,
            critical_threshold=90.0
        )
        
        assert monitor.warning_threshold == 75.0
        assert monitor.critical_threshold == 90.0
    
    def test_get_stats(self):
        """Test getting memory statistics."""
        monitor = MemoryMonitor()
        stats = monitor.get_stats()
        
        assert isinstance(stats, MemoryStats)
        assert stats.total_mb >= 0
        assert stats.percent >= 0


class TestMemoryManager:
    """Test suite for MemoryManager."""
    
    def test_initialization(self):
        """Test memory manager initialization."""
        manager = MemoryManager(
            max_cache_size_mb=10,
            overflow_to_disk=True,
            auto_cleanup=False
        )
        
        assert manager.max_cache_size_bytes == 10 * 1024 * 1024
        assert manager.overflow_to_disk == True
        assert len(manager.cache) == 0
    
    def test_set_and_get(self):
        """Test basic cache operations."""
        manager = MemoryManager(max_cache_size_mb=10)
        
        manager.set('key1', 'value1')
        manager.set('key2', 'value2')
        
        assert manager.get('key1') == 'value1'
        assert manager.get('key2') == 'value2'
        assert manager.get('key3', 'default') == 'default'
    
    def test_delete(self):
        """Test deleting cached items."""
        manager = MemoryManager(max_cache_size_mb=10)
        
        manager.set('key1', 'value1')
        assert manager.get('key1') == 'value1'
        
        manager.delete('key1')
        assert manager.get('key1') is None
    
    def test_lru_eviction(self):
        """Test LRU eviction when cache is full."""
        manager = MemoryManager(max_cache_size_mb=0.001)  # Very small cache
        
        # Fill cache
        large_data = 'x' * 1000
        manager.set('key1', large_data)
        manager.set('key2', large_data)
        
        # This should trigger eviction
        manager.set('key3', large_data)
        
        # First item should be evicted
        assert manager.get('key1') is None or len(manager.cache) < 3
    
    def test_disk_overflow(self):
        """Test disk overflow for large objects."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = MemoryManager(
                max_cache_size_mb=0.001,
                overflow_to_disk=True,
                temp_dir=tmpdir
            )
            
            large_data = 'x' * 10000
            manager.set('large_key', large_data, force_disk=True)
            
            # Should be stored on disk
            assert 'large_key' in manager.disk_files
            
            # Should still be retrievable
            retrieved = manager.get('large_key')
            assert retrieved == large_data
    
    def test_clear(self):
        """Test clearing all cache."""
        manager = MemoryManager(max_cache_size_mb=10)
        
        manager.set('key1', 'value1')
        manager.set('key2', 'value2')
        
        manager.clear()
        
        assert len(manager.cache) == 0
        assert manager.current_cache_size == 0
    
    def test_chunked_iterator(self):
        """Test chunked iteration."""
        manager = MemoryManager(max_cache_size_mb=10)
        
        items = list(range(25))
        chunks = list(manager.chunked_iterator(iter(items), chunk_size=10))
        
        assert len(chunks) == 3
        assert len(chunks[0]) == 10
        assert len(chunks[1]) == 10
        assert len(chunks[2]) == 5
    
    def test_context_manager(self):
        """Test using memory manager as context manager."""
        with MemoryManager(max_cache_size_mb=10) as manager:
            manager.set('key', 'value')
            assert manager.get('key') == 'value'
        
        # Cleanup should have been called
    
    def test_cache_stats(self):
        """Test getting cache statistics."""
        manager = MemoryManager(max_cache_size_mb=10)
        
        manager.set('key1', 'value1')
        manager.set('key2', 'value2')
        
        stats = manager.get_cache_stats()
        
        assert stats['cache_items'] == 2
        assert 'cache_size_mb' in stats
        assert 'memory_stats' in stats


class TestMemoryEfficient:
    """Test memory-efficient utilities."""
    
    def test_memory_efficient_context(self):
        """Test memory-efficient context manager."""
        with memory_efficient_context() as manager:
            manager.set('test', 'data')
            assert manager.get('test') == 'data'
    
    def test_get_memory_stats(self):
        """Test getting memory stats."""
        stats = get_memory_stats()
        assert isinstance(stats, MemoryStats)
    
    def test_force_cleanup(self):
        """Test forcing cleanup."""
        # Should not raise any errors
        force_cleanup()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
