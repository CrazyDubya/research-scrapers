"""
Unit tests for StructuredLogger class.

Tests cover:
- Logging levels
- JSON formatting
- Context tracking
- Performance metrics
- Request logging
- Exception logging
"""

import pytest
import tempfile
import json
import time
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from research_scrapers.structured_logging import (
    StructuredLogger,
    LogContext,
    PerformanceMetrics,
    JSONFormatter,
    create_logger,
    log_execution_time
)


class TestLogContext:
    """Test LogContext dataclass."""
    
    def test_creation(self):
        """Test creating log context."""
        context = LogContext(component="test_component")
        
        assert context.component == "test_component"
        assert context.correlation_id is not None
        assert len(context.correlation_id) > 0
    
    def test_to_dict(self):
        """Test converting context to dict."""
        context = LogContext(
            component="test",
            user_id="user123",
            extra={'custom': 'value'}
        )
        
        context_dict = context.to_dict()
        assert context_dict['component'] == 'test'
        assert context_dict['user_id'] == 'user123'
        assert context_dict['custom'] == 'value'


class TestPerformanceMetrics:
    """Test PerformanceMetrics dataclass."""
    
    def test_creation(self):
        """Test creating performance metrics."""
        metrics = PerformanceMetrics(
            operation="test_op",
            start_time=time.time()
        )
        
        assert metrics.operation == "test_op"
        assert metrics.end_time is None
    
    def test_complete(self):
        """Test completing metrics."""
        metrics = PerformanceMetrics(
            operation="test_op",
            start_time=time.time()
        )
        
        time.sleep(0.01)
        metrics.complete()
        
        assert metrics.end_time is not None
        assert metrics.duration_ms is not None
        assert metrics.duration_ms >= 10  # At least 10ms


class TestStructuredLogger:
    """Test suite for StructuredLogger."""
    
    def test_initialization(self):
        """Test logger initialization."""
        logger = StructuredLogger(
            'test_logger',
            enable_console=False,
            enable_json=True
        )
        
        assert logger.name == 'test_logger'
        assert logger.enable_json == True
    
    def test_logging_levels(self):
        """Test different logging levels."""
        logger = StructuredLogger(
            'test',
            enable_console=False
        )
        
        # These should not raise errors
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")
    
    def test_log_with_context(self):
        """Test logging with custom context."""
        logger = StructuredLogger(
            'test',
            enable_console=False
        )
        
        logger.set_context(user_id="user123", session_id="session456")
        logger.info("Test message", custom_field="custom_value")
        
        assert logger.context.user_id == "user123"
        assert logger.context.session_id == "session456"
    
    def test_log_request(self):
        """Test HTTP request logging."""
        logger = StructuredLogger(
            'test',
            enable_console=False
        )
        
        logger.log_request(
            method="GET",
            url="https://api.example.com/endpoint",
            status_code=200,
            duration_ms=150.5
        )
        
        # Should not raise errors
    
    def test_log_exception(self):
        """Test exception logging."""
        logger = StructuredLogger(
            'test',
            enable_console=False
        )
        
        try:
            raise ValueError("Test exception")
        except ValueError as e:
            logger.log_exception(
                e,
                context={'operation': 'test'}
            )
    
    def test_track_performance(self):
        """Test performance tracking."""
        logger = StructuredLogger(
            'test',
            enable_console=False
        )
        
        with logger.track_performance('test_operation') as metrics:
            time.sleep(0.01)
            metrics.items_processed = 10
        
        assert len(logger.metrics) == 1
        assert logger.metrics[0].operation == 'test_operation'
        assert logger.metrics[0].success == True
        assert logger.metrics[0].items_processed == 10
    
    def test_track_performance_with_exception(self):
        """Test performance tracking with exception."""
        logger = StructuredLogger(
            'test',
            enable_console=False
        )
        
        with pytest.raises(ValueError):
            with logger.track_performance('failing_op') as metrics:
                raise ValueError("Test error")
        
        assert len(logger.metrics) == 1
        assert logger.metrics[0].success == False
        assert "Test error" in logger.metrics[0].error
    
    def test_correlation_id(self):
        """Test correlation ID generation."""
        logger = StructuredLogger(
            'test',
            enable_console=False
        )
        
        old_id = logger.context.correlation_id
        new_id = logger.new_correlation_id()
        
        assert new_id != old_id
        assert logger.context.correlation_id == new_id
    
    def test_metrics_summary(self):
        """Test getting metrics summary."""
        logger = StructuredLogger(
            'test',
            enable_console=False
        )
        
        # Track some operations
        with logger.track_performance('op1'):
            time.sleep(0.01)
        
        with logger.track_performance('op2'):
            time.sleep(0.01)
        
        summary = logger.get_metrics_summary()
        
        assert summary['total_operations'] == 2
        assert summary['successful'] == 2
        assert summary['failed'] == 0
        assert summary['success_rate'] == 100.0
        assert summary['avg_duration_ms'] > 0
    
    def test_file_logging(self):
        """Test logging to files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = StructuredLogger(
                'test',
                log_dir=tmpdir,
                enable_json=True,
                enable_console=False
            )
            
            logger.info("Test message")
            
            # Check that log files were created
            log_dir = Path(tmpdir)
            assert (log_dir / 'test.log').exists()
            assert (log_dir / 'test.json.log').exists()


class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_create_logger(self):
        """Test creating logger with factory function."""
        logger = create_logger('test', level='DEBUG')
        
        assert isinstance(logger, StructuredLogger)
        assert logger.name == 'test'
    
    def test_log_execution_time_decorator(self):
        """Test execution time decorator."""
        logger = StructuredLogger('test', enable_console=False)
        
        @log_execution_time(logger)
        def test_function():
            time.sleep(0.01)
            return "result"
        
        result = test_function()
        
        assert result == "result"
        assert len(logger.metrics) == 1
        assert logger.metrics[0].operation == 'test_function'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
