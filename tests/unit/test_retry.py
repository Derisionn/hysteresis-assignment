"""Unit tests for retry logic."""

import pytest
import time
from app.core.retry import retry_with_backoff, RetryStrategy, RetryError


def test_retry_success_on_first_attempt():
    """Test successful execution on first attempt."""
    call_count = [0]
    
    @retry_with_backoff(max_attempts=3, base_delay=0.1)
    def success_func():
        call_count[0] += 1
        return "success"
    
    result = success_func()
    assert result == "success"
    assert call_count[0] == 1


def test_retry_success_after_failures():
    """Test successful execution after some failures."""
    call_count = [0]
    
    @retry_with_backoff(max_attempts=3, base_delay=0.1)
    def eventually_succeeds():
        call_count[0] += 1
        if call_count[0] < 3:
            raise Exception("Temporary failure")
        return "success"
    
    result = eventually_succeeds()
    assert result == "success"
    assert call_count[0] == 3


def test_retry_exhausts_attempts():
    """Test retry exhausts all attempts."""
    call_count = [0]
    
    @retry_with_backoff(max_attempts=3, base_delay=0.1)
    def always_fails():
        call_count[0] += 1
        raise Exception("Permanent failure")
    
    with pytest.raises(RetryError) as exc_info:
        always_fails()
    
    assert call_count[0] == 3
    assert "Failed after 3 attempts" in str(exc_info.value)


def test_retry_specific_exceptions():
    """Test retry only catches specific exceptions."""
    call_count = [0]
    
    @retry_with_backoff(max_attempts=3, base_delay=0.1, exceptions=(ValueError,))
    def raises_different_error():
        call_count[0] += 1
        raise TypeError("Wrong exception type")
    
    # Should not retry TypeError
    with pytest.raises(TypeError):
        raises_different_error()
    
    assert call_count[0] == 1


def test_retry_strategy_execute():
    """Test RetryStrategy execute method."""
    strategy = RetryStrategy(max_attempts=3, base_delay=0.1)
    call_count = [0]
    
    def eventually_succeeds():
        call_count[0] += 1
        if call_count[0] < 2:
            raise Exception("Temporary failure")
        return "success"
    
    result = strategy.execute(eventually_succeeds)
    assert result == "success"
    assert call_count[0] == 2


def test_retry_exponential_backoff():
    """Test exponential backoff timing."""
    strategy = RetryStrategy(
        max_attempts=3,
        base_delay=0.1,
        exponential_base=2.0,
        jitter=False
    )
    
    # Test delay calculation
    delay1 = strategy._calculate_delay(1)
    delay2 = strategy._calculate_delay(2)
    delay3 = strategy._calculate_delay(3)
    
    assert delay1 == 0.1  # 0.1 * 2^0
    assert delay2 == 0.2  # 0.1 * 2^1
    assert delay3 == 0.4  # 0.1 * 2^2


def test_retry_max_delay():
    """Test max delay cap."""
    strategy = RetryStrategy(
        max_attempts=5,
        base_delay=1.0,
        max_delay=5.0,
        exponential_base=2.0,
        jitter=False
    )
    
    # Delay should be capped at max_delay
    delay5 = strategy._calculate_delay(5)
    assert delay5 == 5.0  # Capped at max_delay


def test_retry_with_jitter():
    """Test jitter adds randomness."""
    strategy = RetryStrategy(
        max_attempts=3,
        base_delay=1.0,
        jitter=True
    )
    
    # With jitter, delays should vary
    delays = [strategy._calculate_delay(1) for _ in range(10)]
    
    # All delays should be between 0.5 and 1.5 (base_delay * [0.5, 1.5])
    assert all(0.5 <= d <= 1.5 for d in delays)
    
    # Should have some variation
    assert len(set(delays)) > 1
