import time
from collections import defaultdict

from fastapi import HTTPException, status


class RateLimiter:
    def __init__(self) -> None:
        self._calls: dict[str, list[float]] = defaultdict(list)

    def check(self, key: str, max_calls: int, window_seconds: int) -> None:
        now = time.time()
        window_start = now - window_seconds
        self._calls[key] = [t for t in self._calls[key] if t > window_start]

        if len(self._calls[key]) >= max_calls:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Max {max_calls} requests per {window_seconds}s.",
            )

        self._calls[key].append(now)


rate_limiter = RateLimiter()
