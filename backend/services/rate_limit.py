import logging
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from datetime import date

from fastapi import HTTPException, status

from config import settings

logger = logging.getLogger(__name__)


class RateLimitStore(ABC):
    @abstractmethod
    def count_in_window(self, key: str, window_seconds: int) -> int:
        pass

    @abstractmethod
    def record(self, key: str, window_seconds: int) -> int:
        pass

    @abstractmethod
    def add_daily_tokens(self, key: str, tokens: int) -> int:
        pass


class MemoryStore(RateLimitStore):
    def __init__(self) -> None:
        self._calls: dict[str, list[float]] = defaultdict(list)
        self._daily_tokens: dict[str, int] = defaultdict(int)
        self._daily_date: dict[str, str] = {}

    def count_in_window(self, key: str, window_seconds: int) -> int:
        now = time.time()
        window_start = now - window_seconds
        self._calls[key] = [t for t in self._calls[key] if t > window_start]
        return len(self._calls[key])

    def record(self, key: str, window_seconds: int) -> int:
        now = time.time()
        window_start = now - window_seconds
        self._calls[key] = [t for t in self._calls[key] if t > window_start]
        self._calls[key].append(now)
        return len(self._calls[key])

    def add_daily_tokens(self, key: str, tokens: int) -> int:
        today = date.today().isoformat()
        if self._daily_date.get(key) != today:
            self._daily_date[key] = today
            self._daily_tokens[key] = 0
        self._daily_tokens[key] += tokens
        return self._daily_tokens[key]


class RedisStore(RateLimitStore):
    def __init__(self, client) -> None:
        self._redis = client

    def count_in_window(self, key: str, window_seconds: int) -> int:
        raw = self._redis.get(key)
        return int(raw) if raw else 0

    def record(self, key: str, window_seconds: int) -> int:
        pipe = self._redis.pipeline()
        pipe.incr(key)
        pipe.expire(key, window_seconds)
        count, _ = pipe.execute()
        return int(count)

    def add_daily_tokens(self, key: str, tokens: int) -> int:
        total = int(self._redis.incrby(key, tokens))
        if total == tokens:
            self._redis.expire(key, 86_400)
        return total


def _create_store() -> RateLimitStore:
    url = getattr(settings, "redis_url", "") or ""
    if not url:
        return MemoryStore()
    try:
        import redis

        client = redis.from_url(url, decode_responses=True)
        client.ping()
        logger.info("Rate limits: using Redis")
        return RedisStore(client)
    except Exception as exc:
        logger.warning("Redis unavailable (%s); using in-memory rate limits", exc)
        return MemoryStore()


class RateLimiter:
    def __init__(self) -> None:
        self._store = _create_store()

    def check(self, key: str, max_calls: int, window_seconds: int) -> None:
        if self._store.count_in_window(key, window_seconds) >= max_calls:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Max {max_calls} requests per {window_seconds}s.",
            )
        self._store.record(key, window_seconds)

    def record_tokens(self, user_id: str, tokens: int) -> None:
        if tokens <= 0 or not user_id:
            return
        limit = settings.rate_limit_daily_tokens
        if limit <= 0:
            return
        key = f"tokens:{user_id}:{date.today().isoformat()}"
        total = self._store.add_daily_tokens(key, tokens)
        if total > limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    f"Daily token limit exceeded ({limit} tokens per day). "
                    "Try again tomorrow or contact support."
                ),
            )


rate_limiter = RateLimiter()
