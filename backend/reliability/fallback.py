import logging
from typing import Callable, Any

logger = logging.getLogger(__name__)


class FallbackHandler:
    """Executes a fallback function when primary handler fails."""

    @staticmethod
    def execute_with_fallback(primary_fn: Callable, fallback_fn: Callable, *args, **kwargs) -> Any:
        try:
            return primary_fn(*args, **kwargs)
        except Exception as e:
            logger.warning(f"Primary execution failed: {e}. Switching to fallback function.")
            return fallback_fn(*args, **kwargs)
