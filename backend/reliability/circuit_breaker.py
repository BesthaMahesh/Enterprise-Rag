import time
import functools
import logging
from typing import Callable, Any

logger = logging.getLogger(__name__)


def retry_with_backoff(
    retries: int = 3,
    initial_delay: float = 0.5,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """Decorator to retry function execution with exponential backoff."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            delay = initial_delay
            last_exc = None
            for attempt in range(1, retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exc = e
                    logger.warning(
                        f"Attempt {attempt}/{retries} for {func.__name__} failed: {e}. Retrying in {delay:.2f}s..."
                    )
                    if attempt == retries:
                        break
                    time.sleep(delay)
                    delay *= backoff_factor
            raise last_exc
        return wrapper
    return decorator


class CircuitBreakerOpenException(Exception):
    pass


class CircuitBreaker:
    """Circuit breaker pattern preventing continuous cascading failures."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 30.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF-OPEN

    def record_success(self):
        self.failure_count = 0
        self.state = "CLOSED"

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.error(f"CircuitBreaker OPENED: {self.failure_count} consecutive failures recorded.")

    def allow_request(self) -> bool:
        if self.state == "CLOSED":
            return True
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF-OPEN"
                logger.info("CircuitBreaker transitioned to HALF-OPEN.")
                return True
            return False
        if self.state == "HALF-OPEN":
            return True
        return False
