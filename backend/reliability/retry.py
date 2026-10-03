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
