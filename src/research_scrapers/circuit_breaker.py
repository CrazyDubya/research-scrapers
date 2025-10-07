"""
Circuit Breaker Pattern Implementation for Research Scrapers

This module provides a circuit breaker pattern implementation with:
- State management (CLOSED, OPEN, HALF_OPEN)
- Smart retry logic with exponential backoff and jitter
- Failure threshold configuration
- Automatic recovery attempts
- Metrics collection for monitoring
- Integration with existing error handling

The circuit breaker prevents cascading failures by stopping requests
to failing services and allowing time for recovery.

Author: Research Scrapers Team
"""

import logging
import random
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, Optional
from threading import Lock

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, rejecting requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerMetrics:
    """Metrics for circuit breaker monitoring."""
    
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    rejected_requests: int = 0
    state_changes: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    def get_failure_rate(self) -> float:
        """Calculate failure rate."""
        if self.total_requests == 0:
            return 0.0
        return self.failed_requests / self.total_requests * 100
    
    def get_success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_requests == 0:
            return 0.0
        return self.successful_requests / self.total_requests * 100


class CircuitBreakerError(Exception):
    """Exception raised when circuit breaker is open."""
    pass


class CircuitBreaker:
    """
    Circuit breaker implementation with state management and metrics.
    
    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, requests are rejected
    - HALF_OPEN: Testing if service recovered, limited requests allowed
    
    Features:
    - Configurable failure thresholds
    - Automatic recovery attempts
    - Exponential backoff with jitter
    - Detailed metrics collection
    - Thread-safe operation
    
    Example:
        >>> breaker = CircuitBreaker(failure_threshold=5, timeout=60)
        >>> 
        >>> @breaker
        >>> def api_call():
        >>>     return make_request()
        >>> 
        >>> try:
        >>>     result = api_call()
        >>> except CircuitBreakerError:
        >>>     print("Circuit breaker is open, service unavailable")
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout: float = 60.0,
        expected_exception: type = Exception,
        name: Optional[str] = None,
        fallback: Optional[Callable] = None
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            success_threshold: Number of successes to close circuit from half-open
            timeout: Seconds to wait before attempting recovery (half-open)
            expected_exception: Exception type to catch (defaults to all)
            name: Optional name for the circuit breaker
            fallback: Optional fallback function to call when circuit is open
        """
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception
        self.name = name or f"circuit_breaker_{id(self)}"
        self.fallback = fallback
        
        # State
        self._state = CircuitState.CLOSED
        self._opened_at: Optional[float] = None
        
        # Metrics
        self.metrics = CircuitBreakerMetrics()
        
        # Thread safety
        self._lock = Lock()
        
        logger.info(
            f"CircuitBreaker '{self.name}' initialized: "
            f"failure_threshold={failure_threshold}, timeout={timeout}s"
        )
    
    @property
    def state(self) -> CircuitState:
        """Get current state."""
        with self._lock:
            # Check if we should attempt recovery
            if (self._state == CircuitState.OPEN and
                self._opened_at is not None and
                time.time() - self._opened_at >= self.timeout):
                self._transition_to_half_open()
            
            return self._state
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Call function through circuit breaker.
        
        Args:
            func: Function to call
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerError: If circuit is open
        """
        # Check state
        current_state = self.state
        
        if current_state == CircuitState.OPEN:
            self.metrics.rejected_requests += 1
            
            # Try fallback if available
            if self.fallback:
                logger.warning(f"Circuit '{self.name}' is OPEN, using fallback")
                return self.fallback(*args, **kwargs)
            
            raise CircuitBreakerError(
                f"Circuit breaker '{self.name}' is OPEN. "
                f"Service unavailable, please try again later."
            )
        
        # Attempt the call
        with self._lock:
            self.metrics.total_requests += 1
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
            
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    def _on_success(self):
        """Handle successful call."""
        with self._lock:
            self.metrics.successful_requests += 1
            self.metrics.consecutive_successes += 1
            self.metrics.consecutive_failures = 0
            self.metrics.last_success_time = time.time()
            
            # If in half-open state, check if we can close
            if self._state == CircuitState.HALF_OPEN:
                if self.metrics.consecutive_successes >= self.success_threshold:
                    self._transition_to_closed()
    
    def _on_failure(self):
        """Handle failed call."""
        with self._lock:
            self.metrics.failed_requests += 1
            self.metrics.consecutive_failures += 1
            self.metrics.consecutive_successes = 0
            self.metrics.last_failure_time = time.time()
            
            # Check if we should open the circuit
            if self._state == CircuitState.CLOSED:
                if self.metrics.consecutive_failures >= self.failure_threshold:
                    self._transition_to_open()
            
            # If in half-open and failed, go back to open
            elif self._state == CircuitState.HALF_OPEN:
                self._transition_to_open()
    
    def _transition_to_open(self):
        """Transition to OPEN state."""
        previous_state = self._state
        self._state = CircuitState.OPEN
        self._opened_at = time.time()
        self.metrics.state_changes += 1
        
        logger.warning(
            f"Circuit '{self.name}' transitioned from {previous_state.value} to OPEN "
            f"after {self.metrics.consecutive_failures} consecutive failures"
        )
    
    def _transition_to_half_open(self):
        """Transition to HALF_OPEN state."""
        previous_state = self._state
        self._state = CircuitState.HALF_OPEN
        self.metrics.state_changes += 1
        self.metrics.consecutive_successes = 0
        self.metrics.consecutive_failures = 0
        
        logger.info(
            f"Circuit '{self.name}' transitioned from {previous_state.value} to HALF_OPEN "
            f"after timeout of {self.timeout}s"
        )
    
    def _transition_to_closed(self):
        """Transition to CLOSED state."""
        previous_state = self._state
        self._state = CircuitState.CLOSED
        self._opened_at = None
        self.metrics.state_changes += 1
        self.metrics.consecutive_failures = 0
        
        logger.info(
            f"Circuit '{self.name}' transitioned from {previous_state.value} to CLOSED "
            f"after {self.metrics.consecutive_successes} consecutive successes"
        )
    
    def reset(self):
        """Reset circuit breaker to CLOSED state."""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._opened_at = None
            self.metrics.consecutive_failures = 0
            self.metrics.consecutive_successes = 0
            
            logger.info(f"Circuit '{self.name}' manually reset to CLOSED")
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get circuit breaker metrics.
        
        Returns:
            Dictionary with metrics
        """
        with self._lock:
            metrics = self.metrics.to_dict()
            metrics.update({
                'state': self._state.value,
                'name': self.name,
                'failure_rate': self.metrics.get_failure_rate(),
                'success_rate': self.metrics.get_success_rate(),
                'opened_at': self._opened_at
            })
            return metrics
    
    def __call__(self, func: Callable) -> Callable:
        """
        Decorator for wrapping functions with circuit breaker.
        
        Args:
            func: Function to wrap
            
        Returns:
            Wrapped function
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            return self.call(func, *args, **kwargs)
        
        return wrapper
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if exc_type is not None and issubclass(exc_type, self.expected_exception):
            self._on_failure()
        return False


class ExponentialBackoff:
    """
    Exponential backoff strategy with jitter.
    
    Used with circuit breakers for retry logic.
    
    Example:
        >>> backoff = ExponentialBackoff(base_delay=1.0, max_delay=60.0)
        >>> for attempt in range(5):
        >>>     delay = backoff.get_delay(attempt)
        >>>     time.sleep(delay)
        >>>     try:
        >>>         make_request()
        >>>         break
        >>>     except Exception:
        >>>         continue
    """
    
    def __init__(
        self,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        multiplier: float = 2.0,
        jitter: bool = True
    ):
        """
        Initialize exponential backoff.
        
        Args:
            base_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            multiplier: Backoff multiplier
            jitter: Whether to add random jitter
        """
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.multiplier = multiplier
        self.jitter = jitter
    
    def get_delay(self, attempt: int) -> float:
        """
        Get delay for given attempt.
        
        Args:
            attempt: Attempt number (0-indexed)
            
        Returns:
            Delay in seconds
        """
        delay = min(
            self.base_delay * (self.multiplier ** attempt),
            self.max_delay
        )
        
        if self.jitter:
            # Add random jitter (±25%)
            jitter_range = delay * 0.25
            delay += random.uniform(-jitter_range, jitter_range)
        
        return max(0, delay)


def with_circuit_breaker(
    failure_threshold: int = 5,
    timeout: float = 60.0,
    name: Optional[str] = None
):
    """
    Decorator factory for creating circuit breaker decorators.
    
    Args:
        failure_threshold: Number of failures before opening
        timeout: Timeout before attempting recovery
        name: Optional circuit breaker name
        
    Returns:
        Decorator function
    
    Example:
        >>> @with_circuit_breaker(failure_threshold=3, timeout=30)
        >>> def api_call():
        >>>     return make_request()
    """
    breaker = CircuitBreaker(
        failure_threshold=failure_threshold,
        timeout=timeout,
        name=name
    )
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return breaker.call(func, *args, **kwargs)
        
        # Attach breaker to function for access to metrics
        wrapper.circuit_breaker = breaker
        
        return wrapper
    
    return decorator


def retry_with_backoff(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: tuple = (Exception,)
):
    """
    Decorator for retry logic with exponential backoff.
    
    Args:
        max_attempts: Maximum number of attempts
        base_delay: Initial delay between retries
        max_delay: Maximum delay between retries
        exceptions: Tuple of exceptions to catch
        
    Returns:
        Decorator function
    
    Example:
        >>> @retry_with_backoff(max_attempts=5, base_delay=2.0)
        >>> def unstable_api_call():
        >>>     return make_request()
    """
    backoff = ExponentialBackoff(base_delay=base_delay, max_delay=max_delay)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_attempts - 1:
                        delay = backoff.get_delay(attempt)
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_attempts} failed: {e}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed: {e}"
                        )
            
            raise last_exception
        
        return wrapper
    
    return decorator
