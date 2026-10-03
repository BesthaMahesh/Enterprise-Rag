import time
from typing import Dict, Tuple
from collections import defaultdict


class RateLimiter:
    """Sliding-window in-memory rate limiter per IP / User."""

    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list] = defaultdict(list)

    def is_allowed(self, key: str) -> Tuple[bool, int]:
        now = time.time()
        window_start = now - self.window_seconds
        
        # Clean expired timestamps
        self.requests[key] = [t for t in self.requests[key] if t > window_start]

        if len(self.requests[key]) < self.max_requests:
            self.requests[key].append(now)
            remaining = self.max_requests - len(self.requests[key])
            return True, remaining
        
        return False, 0


rate_limiter = RateLimiter()
