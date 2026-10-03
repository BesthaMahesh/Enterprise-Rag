import concurrent.futures
import functools
import logging
from typing import Callable, Any

logger = logging.getLogger(__name__)


class TimeoutException(Exception):
    pass


def with_timeout(seconds: float):
    """Decorator to enforce a maximum execution timeout on functions using thread pool executor."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(func, *args, **kwargs)
                try:
                    return future.result(timeout=seconds)
                except concurrent.futures.TimeoutError:
                    logger.error(f"Function {func.__name__} timed out after {seconds} seconds.")
                    raise TimeoutException(f"Function '{func.__name__}' timed out after {seconds}s")
        return wrapper
    return decorator
