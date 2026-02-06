"""Retry logic with exponential backoff."""

import time
import random
from typing import Callable, Any, Optional, Type
from functools import wraps


class RetryError(Exception):
    """Raised when all retry attempts are exhausted."""
    pass


def retry_with_backoff(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    exceptions: tuple = (Exception,)
):
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
        jitter: Add random jitter to prevent thundering herd
        exceptions: Tuple of exceptions to catch and retry
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts:
                        raise RetryError(
                            f"Failed after {max_attempts} attempts. "
                            f"Last error: {str(e)}"
                        ) from e
                    
                    # Calculate delay with exponential backoff
                    delay = min(
                        base_delay * (exponential_base ** (attempt - 1)),
                        max_delay
                    )
                    
                    # Add jitter to prevent thundering herd
                    if jitter:
                        delay = delay * (0.5 + random.random())
                    
                    print(
                        f"[Retry] Attempt {attempt}/{max_attempts} failed. "
                        f"Retrying in {delay:.2f}s... Error: {str(e)}"
                    )
                    
                    time.sleep(delay)
            
            # Should never reach here, but just in case
            raise last_exception
        
        return wrapper
    return decorator


class RetryStrategy:
    """Retry strategy with configurable backoff."""
    
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        """
        Initialize retry strategy.
        
        Args:
            max_attempts: Maximum number of retry attempts
            base_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            exponential_base: Base for exponential backoff
            jitter: Add random jitter
        """
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
    
    def execute(
        self,
        func: Callable,
        *args,
        exceptions: tuple = (Exception,),
        **kwargs
    ) -> Any:
        """
        Execute function with retry logic.
        
        Args:
            func: Function to execute
            *args: Function arguments
            exceptions: Exceptions to catch and retry
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            RetryError: If all attempts fail
        """
        last_exception = None
        
        for attempt in range(1, self.max_attempts + 1):
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                last_exception = e
                
                if attempt == self.max_attempts:
                    raise RetryError(
                        f"Failed after {self.max_attempts} attempts. "
                        f"Last error: {str(e)}"
                    ) from e
                
                delay = self._calculate_delay(attempt)
                
                print(
                    f"[Retry] Attempt {attempt}/{self.max_attempts} failed. "
                    f"Retrying in {delay:.2f}s... Error: {str(e)}"
                )
                
                time.sleep(delay)
        
        raise last_exception
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt."""
        delay = min(
            self.base_delay * (self.exponential_base ** (attempt - 1)),
            self.max_delay
        )
        
        if self.jitter:
            delay = delay * (0.5 + random.random())
        
        return delay
