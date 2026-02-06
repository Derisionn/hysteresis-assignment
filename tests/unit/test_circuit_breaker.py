"""Unit tests for circuit breaker."""

import pytest
import time
from app.core.circuit_breaker import CircuitBreaker, CircuitBreakerError, CircuitState


def test_circuit_breaker_closed_state():
    """Test circuit breaker starts in closed state."""
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=5)
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0


def test_circuit_breaker_successful_call():
    """Test successful call through circuit breaker."""
    cb = CircuitBreaker(failure_threshold=3)
    
    def success_func():
        return "success"
    
    result = cb.call(success_func)
    assert result == "success"
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0


def test_circuit_breaker_opens_after_threshold():
    """Test circuit breaker opens after failure threshold."""
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=5)
    
    def failing_func():
        raise Exception("Service unavailable")
    
    # Fail 3 times to reach threshold
    for i in range(3):
        with pytest.raises(Exception):
            cb.call(failing_func)
    
    # Circuit should now be open
    assert cb.state == CircuitState.OPEN
    assert cb.failure_count == 3


def test_circuit_breaker_rejects_when_open():
    """Test circuit breaker rejects requests when open."""
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=5)
    
    def failing_func():
        raise Exception("Service unavailable")
    
    # Open the circuit
    for i in range(2):
        with pytest.raises(Exception):
            cb.call(failing_func)
    
    # Next call should be rejected immediately
    with pytest.raises(CircuitBreakerError) as exc_info:
        cb.call(failing_func)
    
    assert "Circuit breaker" in str(exc_info.value)
    assert "OPEN" in str(exc_info.value)


def test_circuit_breaker_half_open_after_timeout():
    """Test circuit breaker transitions to half-open after timeout."""
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=1)
    
    def failing_func():
        raise Exception("Service unavailable")
    
    # Open the circuit
    for i in range(2):
        with pytest.raises(Exception):
            cb.call(failing_func)
    
    assert cb.state == CircuitState.OPEN
    
    # Wait for recovery timeout
    time.sleep(1.1)
    
    # Next call should attempt recovery (half-open)
    with pytest.raises(Exception):
        cb.call(failing_func)
    
    # Should be open again after failed recovery
    assert cb.state == CircuitState.OPEN


def test_circuit_breaker_closes_on_success_in_half_open():
    """Test circuit breaker closes on successful call in half-open state."""
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=1)
    
    call_count = [0]
    
    def sometimes_failing_func():
        call_count[0] += 1
        if call_count[0] <= 2:
            raise Exception("Service unavailable")
        return "success"
    
    # Open the circuit
    for i in range(2):
        with pytest.raises(Exception):
            cb.call(sometimes_failing_func)
    
    assert cb.state == CircuitState.OPEN
    
    # Wait for recovery timeout
    time.sleep(1.1)
    
    # Successful call should close the circuit
    result = cb.call(sometimes_failing_func)
    assert result == "success"
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0


def test_circuit_breaker_reset():
    """Test manual circuit breaker reset."""
    cb = CircuitBreaker(failure_threshold=2)
    
    def failing_func():
        raise Exception("Service unavailable")
    
    # Open the circuit
    for i in range(2):
        with pytest.raises(Exception):
            cb.call(failing_func)
    
    assert cb.state == CircuitState.OPEN
    
    # Reset circuit
    cb.reset()
    
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0


def test_circuit_breaker_get_state():
    """Test getting circuit breaker state."""
    cb = CircuitBreaker(failure_threshold=5, name="test_circuit")
    
    state = cb.get_state()
    
    assert state["name"] == "test_circuit"
    assert state["state"] == "closed"
    assert state["failure_count"] == 0
    assert state["failure_threshold"] == 5
