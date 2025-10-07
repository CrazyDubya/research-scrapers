"""
Structured Logging System for Research Scrapers

This module provides comprehensive structured logging with:
- JSON format support for machine-readable logs
- Automatic log rotation by size and time
- Correlation IDs for request tracking
- Performance metrics collection
- Log levels per component
- Request/response logging with sanitization
- Error tracking with stack traces and context
- Integration-ready for external services

Author: Research Scrapers Team
"""

import json
import logging
import logging.handlers
import sys
import time
import traceback
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from functools import wraps

logger = logging.getLogger(__name__)


@dataclass
class LogContext:
    """Context information for structured logging."""
    
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    component: str = "default"
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data.update(data.pop('extra', {}))
        return data


@dataclass
class PerformanceMetrics:
    """Performance metrics for tracking."""
    
    operation: str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    memory_delta_mb: Optional[float] = None
    api_calls: int = 0
    items_processed: int = 0
    success: bool = True
    error: Optional[str] = None
    
    def complete(self):
        """Mark operation as complete and calculate duration."""
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class JSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.
    
    Outputs log records as JSON objects with consistent structure.
    """
    
    def __init__(self, include_extra: bool = True):
        """
        Initialize JSON formatter.
        
        Args:
            include_extra: Whether to include extra fields
        """
        super().__init__()
        self.include_extra = include_extra
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.
        
        Args:
            record: Log record
            
        Returns:
            JSON string
        """
        log_data = {
            'timestamp': datetime.utcfromtimestamp(record.created).isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields
        if self.include_extra:
            for key, value in record.__dict__.items():
                if key not in ['name', 'msg', 'args', 'created', 'filename', 'funcName',
                              'levelname', 'lineno', 'module', 'msecs', 'message',
                              'pathname', 'process', 'processName', 'relativeCreated',
                              'thread', 'threadName', 'exc_info', 'exc_text', 'stack_info']:
                    try:
                        json.dumps(value)  # Test if serializable
                        log_data[key] = value
                    except (TypeError, ValueError):
                        log_data[key] = str(value)
        
        return json.dumps(log_data)


class StructuredLogger:
    """
    Comprehensive structured logging system.
    
    Features:
    - JSON and text formatting
    - Automatic log rotation
    - Correlation ID tracking
    - Performance metrics
    - Component-level configuration
    - Request/response logging
    - Error tracking
    
    Example:
        >>> logger = StructuredLogger('my_app', log_dir='logs')
        >>> logger.info('Application started')
        >>> with logger.track_performance('data_processing'):
        >>>     process_data()
    """
    
    def __init__(
        self,
        name: str,
        log_dir: Optional[Union[str, Path]] = None,
        log_level: str = 'INFO',
        enable_json: bool = True,
        enable_console: bool = True,
        max_file_size_mb: int = 10,
        backup_count: int = 5,
        rotation_time: str = 'midnight',
        context: Optional[LogContext] = None
    ):
        """
        Initialize structured logger.
        
        Args:
            name: Logger name
            log_dir: Directory for log files (None = console only)
            log_level: Default log level
            enable_json: Whether to use JSON formatting
            enable_console: Whether to enable console logging
            max_file_size_mb: Maximum file size for rotation (MB)
            backup_count: Number of backup files to keep
            rotation_time: Time-based rotation ('midnight', 'H', etc.)
            context: Default log context
        """
        self.name = name
        self.log_dir = Path(log_dir) if log_dir else None
        self.enable_json = enable_json
        self.context = context or LogContext(component=name)
        
        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level.upper()))
        self.logger.handlers.clear()
        
        # Setup formatters
        if enable_json:
            self.json_formatter = JSONFormatter()
        
        self.text_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Setup handlers
        if enable_console:
            self._setup_console_handler()
        
        if self.log_dir:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            self._setup_file_handlers(max_file_size_mb, backup_count, rotation_time)
        
        # Performance tracking
        self.metrics: List[PerformanceMetrics] = []
        
        self.logger.info(f"StructuredLogger initialized: {name}")
    
    def _setup_console_handler(self):
        """Setup console handler."""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.logger.level)
        console_handler.setFormatter(self.text_formatter)
        self.logger.addHandler(console_handler)
    
    def _setup_file_handlers(self, max_size_mb: int, backup_count: int, rotation_time: str):
        """Setup file handlers with rotation."""
        # Text log file (always created)
        text_log = self.log_dir / f"{self.name}.log"
        text_handler = logging.handlers.RotatingFileHandler(
            text_log,
            maxBytes=max_size_mb * 1024 * 1024,
            backupCount=backup_count
        )
        text_handler.setLevel(self.logger.level)
        text_handler.setFormatter(self.text_formatter)
        self.logger.addHandler(text_handler)
        
        # JSON log file (if enabled)
        if self.enable_json:
            json_log = self.log_dir / f"{self.name}.json.log"
            json_handler = logging.handlers.RotatingFileHandler(
                json_log,
                maxBytes=max_size_mb * 1024 * 1024,
                backupCount=backup_count
            )
            json_handler.setLevel(self.logger.level)
            json_handler.setFormatter(self.json_formatter)
            self.logger.addHandler(json_handler)
        
        # Error log file
        error_log = self.log_dir / f"{self.name}.error.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_log,
            maxBytes=max_size_mb * 1024 * 1024,
            backupCount=backup_count
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(self.text_formatter)
        self.logger.addHandler(error_handler)
    
    def _log_with_context(self, level: int, message: str, **kwargs):
        """Log message with context."""
        extra = self.context.to_dict()
        extra.update(kwargs)
        self.logger.log(level, message, extra=extra)
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self._log_with_context(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self._log_with_context(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self._log_with_context(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, exc_info: bool = False, **kwargs):
        """Log error message."""
        self._log_with_context(logging.ERROR, message, exc_info=exc_info, **kwargs)
    
    def critical(self, message: str, exc_info: bool = False, **kwargs):
        """Log critical message."""
        self._log_with_context(logging.CRITICAL, message, exc_info=exc_info, **kwargs)
    
    def log_request(
        self,
        method: str,
        url: str,
        status_code: Optional[int] = None,
        duration_ms: Optional[float] = None,
        sanitize: bool = True,
        **kwargs
    ):
        """
        Log HTTP request/response.
        
        Args:
            method: HTTP method
            url: Request URL
            status_code: Response status code
            duration_ms: Request duration in milliseconds
            sanitize: Whether to sanitize sensitive data
            **kwargs: Additional fields
        """
        # Sanitize URL if needed
        if sanitize:
            url = self._sanitize_url(url)
        
        log_data = {
            'event': 'http_request',
            'method': method,
            'url': url,
            'status_code': status_code,
            'duration_ms': duration_ms
        }
        log_data.update(kwargs)
        
        if status_code and status_code >= 400:
            self.error("HTTP request failed", **log_data)
        else:
            self.info("HTTP request", **log_data)
    
    def log_exception(
        self,
        exception: Exception,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """
        Log exception with full context.
        
        Args:
            exception: Exception object
            context: Additional context
            **kwargs: Additional fields
        """
        error_data = {
            'event': 'exception',
            'exception_type': type(exception).__name__,
            'exception_message': str(exception),
            'traceback': traceback.format_exc()
        }
        
        if context:
            error_data['context'] = context
        
        error_data.update(kwargs)
        
        self.error(f"Exception occurred: {exception}", exc_info=True, **error_data)
    
    @contextmanager
    def track_performance(
        self,
        operation: str,
        log_on_complete: bool = True,
        **kwargs
    ):
        """
        Context manager for tracking operation performance.
        
        Args:
            operation: Operation name
            log_on_complete: Whether to log when complete
            **kwargs: Additional metrics fields
            
        Yields:
            PerformanceMetrics object
        
        Example:
            >>> with logger.track_performance('data_processing') as metrics:
            >>>     process_data()
            >>>     metrics.items_processed = 100
        """
        metrics = PerformanceMetrics(
            operation=operation,
            start_time=time.time()
        )
        
        try:
            yield metrics
            metrics.success = True
        except Exception as e:
            metrics.success = False
            metrics.error = str(e)
            raise
        finally:
            metrics.complete()
            
            # Add to metrics history
            self.metrics.append(metrics)
            
            # Log if requested
            if log_on_complete:
                log_data = metrics.to_dict()
                log_data.update(kwargs)
                
                if metrics.success:
                    self.info(
                        f"Operation completed: {operation} ({metrics.duration_ms:.1f}ms)",
                        **log_data
                    )
                else:
                    self.error(
                        f"Operation failed: {operation} ({metrics.duration_ms:.1f}ms)",
                        **log_data
                    )
    
    def set_context(self, **kwargs):
        """
        Update log context.
        
        Args:
            **kwargs: Context fields to update
        """
        for key, value in kwargs.items():
            if hasattr(self.context, key):
                setattr(self.context, key, value)
            else:
                self.context.extra[key] = value
    
    def new_correlation_id(self) -> str:
        """
        Generate new correlation ID.
        
        Returns:
            New correlation ID
        """
        correlation_id = str(uuid.uuid4())
        self.context.correlation_id = correlation_id
        return correlation_id
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Get summary of performance metrics.
        
        Returns:
            Dictionary with metrics summary
        """
        if not self.metrics:
            return {}
        
        successful = [m for m in self.metrics if m.success]
        failed = [m for m in self.metrics if not m.success]
        
        durations = [m.duration_ms for m in successful if m.duration_ms]
        
        return {
            'total_operations': len(self.metrics),
            'successful': len(successful),
            'failed': len(failed),
            'success_rate': len(successful) / len(self.metrics) * 100 if self.metrics else 0,
            'avg_duration_ms': sum(durations) / len(durations) if durations else 0,
            'min_duration_ms': min(durations) if durations else 0,
            'max_duration_ms': max(durations) if durations else 0,
            'total_api_calls': sum(m.api_calls for m in self.metrics),
            'total_items_processed': sum(m.items_processed for m in self.metrics)
        }
    
    def clear_metrics(self):
        """Clear metrics history."""
        self.metrics.clear()
    
    def _sanitize_url(self, url: str) -> str:
        """
        Sanitize URL by removing sensitive parameters.
        
        Args:
            url: URL to sanitize
            
        Returns:
            Sanitized URL
        """
        # Remove common sensitive parameters
        sensitive_params = ['token', 'api_key', 'password', 'secret', 'authorization']
        
        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
        
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        
        # Remove sensitive params
        for param in sensitive_params:
            if param in params:
                params[param] = ['***REDACTED***']
        
        # Rebuild URL
        new_query = urlencode(params, doseq=True)
        return urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            parsed.fragment
        ))


def log_execution_time(logger: StructuredLogger = None):
    """
    Decorator to log function execution time.
    
    Args:
        logger: StructuredLogger instance (uses default if None)
        
    Example:
        >>> @log_execution_time(my_logger)
        >>> def slow_function():
        >>>     time.sleep(1)
    """
    def decorator(func: callable) -> callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal logger
            if logger is None:
                logger = StructuredLogger(func.__module__)
            
            with logger.track_performance(func.__name__):
                return func(*args, **kwargs)
        
        return wrapper
    return decorator


def create_logger(
    name: str,
    log_dir: Optional[str] = None,
    level: str = 'INFO',
    json_format: bool = False
) -> StructuredLogger:
    """
    Convenience function to create structured logger.
    
    Args:
        name: Logger name
        log_dir: Log directory
        level: Log level
        json_format: Whether to use JSON format
        
    Returns:
        StructuredLogger instance
    """
    return StructuredLogger(
        name=name,
        log_dir=log_dir,
        log_level=level,
        enable_json=json_format
    )
