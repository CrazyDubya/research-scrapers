"""
Unit tests for CircuitBreaker class.

Tests cover:
- State transitions
- Failure threshold
- Timeout and recovery
- Metrics collection
- Decorator usage
- Retry with backoff
"""

import pytest
import time
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from research_scrapers.circuit_breaker import (
    CircuitBreaker,
    CircuitState,
    CircuitBreakerError,
    ExponentialBackoff,
    with_circuit_breaker,
    retry_with_backoff
)


class TestCircuitBreaker:
    """Test suite for CircuitBreaker."""
    
    def test_initialization(self):
        """Test circuit breaker initialization."""
        breaker = CircuitBreaker(
            failure_threshold=3,
            timeout=10.0
        )
        
        assert breaker.failure_threshold == 3
        assert breaker.timeout == 10.0
        assert breaker.state == CircuitState.CLOSED
    
    def test_successful_calls(self):
        """Test successful calls through circuit breaker."""
        breaker = CircuitBreaker(failure_threshold=3)
        
        def successful_func():
            return "success"
        
        for _ in range(5):
            result = breaker.call(successful_func)
            assert result == "success"
        
        assert breaker.state == CircuitState.CLOSED
        assert breaker.metrics.successful_requests == 5
        assert breaker.metrics.failed_requests == 0
    
    def test_transition_to_open(self):
        """Test circuit opens after failure threshold."""
        breaker = CircuitBreaker(failure_threshold=3, timeout=1.0)
        
        def failing_func():
            raise ValueError("Test error")
        
        # Cause failures to open circuit
        for _ in range(3):
            with pytest.raises(ValueError):
                breaker.call(failing_func)
        
        # Circuit should be open
        assert breaker.state == CircuitState.OPEN
        assert breaker.metrics.failed_requests == 3
    
    def test_reject_when_open(self):
        """Test that calls are rejected when circuit is open."""
        breaker = CircuitBreaker(failure_threshold=2, timeout=10.0)
        
        def failing_func():
            raise ValueError("Error")
        
        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                breaker.call(failing_func)
        
        # Now calls should be rejected
        def any_func():
            return "result"
        
        with pytest.raises(CircuitBreakerError):
            breaker.call(any_func)
        
        assert breaker.metrics.rejected_requests > 0
    
    def test_transition_to_half_open(self):
        """Test transition to half-open after timeout."""
        breaker = CircuitBreaker(failure_threshold=2, timeout=0.1)
        
        def failing_func():
            raise ValueError("Error")
        
        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                breaker.call(failing_func)
        
        assert breaker.state == CircuitState.OPEN
        
        # Wait for timeout
        time.sleep(0.15)
        
        # Check state (should transition to half-open)
        assert breaker.state == CircuitState.HALF_OPEN
    
    def test_transition_to_closed_from_half_open(self):
        """Test circuit closes after successful calls in half-open."""
        breaker = CircuitBreaker(
            failure_threshold=2,
            success_threshold=2,
            timeout=0.1
        )
        
        def failing_func():
            raise ValueError("Error")
        
        def successful_func():
            return "success"
        
        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                breaker.call(failing_func)
        
        # Wait for timeout
        time.sleep(0.15)
        
        # Make successful calls to close circuit
        for _ in range(2):
            result = breaker.call(successful_func)
            assert result == "success"
        
        # Circuit should be closed
        assert breaker.state == CircuitState.CLOSED
    
    def test_decorator_usage(self):
        """Test using circuit breaker as decorator."""
        breaker = CircuitBreaker(failure_threshold=3)
        
        @breaker
        def test_function():
            return "result"
        
        result = test_function()
        assert result == "result"
        assert breaker.metrics.successful_requests == 1
    
    def test_fallback_function(self):
        """Test fallback when circuit is open."""
        def fallback_func():
            return "fallback_result"
        
        breaker = CircuitBreaker(
            failure_threshold=2,
            timeout=10.0,
            fallback=fallback_func
        )
        
        def failing_func():
            raise ValueError("Error")
        
        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                breaker.call(failing_func)
        
        # Call should use fallback instead of raising CircuitBreakerError
        def any_func():
            return "normal_result"
        
        result = breaker.call(any_func)
        assert result == "fallback_result"
    
    def test_reset(self):
        """Test manually resetting circuit breaker."""
        breaker = CircuitBreaker(failure_threshold=2)
        
        def failing_func():
            raise ValueError("Error")
        
        # Open the circuit
        for _ in range(2):
            with pytest.raises(ValueError):
                breaker.call(failing_func)
        
        assert breaker.state == CircuitState.OPEN
        
        # Reset circuit
        breaker.reset()
        
        assert breaker.state == CircuitState.CLOSED
        assert breaker.metrics.consecutive_failures == 0
    
    def test_get_metrics(self):
        """Test getting circuit breaker metrics."""
        breaker = CircuitBreaker(failure_threshold=3)
        
        def test_func():
            return "result"
        
        breaker.call(test_func)
        breaker.call(test_func)
        
        metrics = breaker.get_metrics()
        
        assert metrics['state'] == CircuitState.CLOSED.value
        assert metrics['total_requests'] == 2
        assert metrics['successful_requests'] == 2
        assert metrics['success_rate'] == 100.0


class TestExponentialBackoff:
    """Test ExponentialBackoff class."""
    
    def test_initialization(self):
        """Test backoff initialization."""
        backoff = ExponentialBackoff(
            base_delay=1.0,
            max_delay=60.0,
            multiplier=2.0
        )
        
        assert backoff.base_delay == 1.0
        assert backoff.max_delay == 60.0
        assert backoff.multiplier == 2.0
    
    def test_delay_calculation(self):
        """Test delay calculation."""
        backoff = ExponentialBackoff(
            base_delay=1.0,
            max_delay=60.0,
            multiplier=2.0,
            jitter=False
        )
        
        # Test exponential growth
        assert backoff.get_delay(0) == 1.0
        assert backoff.get_delay(1) == 2.0
        assert backoff.get_delay(2) == 4.0
        assert backoff.get_delay(3) == 8.0
    
    def test_max_delay_cap(self):
        """Test that delay doesn't exceed max."""
        backoff = ExponentialBackoff(
            base_delay=10.0,
            max_delay=30.0,
            jitter=False
        )
        
        # Should cap at max_delay
        delay = backoff.get_delay(10)
        assert delay <= 30.0
    
    def test_with_jitter(self):
        """Test jitter adds randomness."""
        backoff = ExponentialBackoff(
            base_delay=10.0,
            jitter=True
        )
        
        delays = [backoff.get_delay(1) for _ in range(10)]
        
        # With jitter, delays should vary
        assert len(set(delays)) > 1


class TestDecorators:
    """Test decorator functions."""
    
    def test_with_circuit_breaker(self):
        """Test circuit breaker decorator factory."""
        @with_circuit_breaker(failure_threshold=2, timeout=1.0)
        def test_function():
            return "result"
        
        result = test_function()
        assert result == "result"
        
        # Check that breaker is attached
        assert hasattr(test_function, 'circuit_breaker')
        assert isinstance(test_function.circuit_breaker, CircuitBreaker)
    
    def test_retry_with_backoff_success(self):
        """Test retry decorator with eventual success."""
        call_count = [0]
        
        @retry_with_backoff(max_attempts=3, base_delay=0.01)
        def flaky_function():
            call_count[0] += 1
            if call_count[0] < 2:
                raise ValueError("Temporary error")
            return "success"
        
        result = flaky_function()
        
        assert result == "success"
        assert call_count[0] == 2  # Failed once, succeeded on second try
    
    def test_retry_with_backoff_failure(self):
        """Test retry decorator with all attempts failing."""
        @retry_with_backoff(max_attempts=3, base_delay=0.01)
        def always_fails():
            raise ValueError("Always fails")
        
        with pytest.raises(ValueError) as exc_info:
            always_fails()
        
        assert "Always fails" in str(exc_info.value)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
