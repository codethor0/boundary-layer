"""Rate limiting backends for BoundaryLayer API."""

from __future__ import annotations

import logging
import time
import uuid
from collections import defaultdict, deque

logger = logging.getLogger("boundary_layer.api")


class InMemoryRateLimiter:
    """Sliding-window limiter keyed by client identifier."""

    def __init__(self) -> None:
        self._events: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str, limit: int, window: int) -> tuple[bool, int]:
        now = time.monotonic()
        bucket = self._events[key]

        while bucket and now - bucket[0] > window:
            bucket.popleft()

        if len(bucket) >= limit:
            return False, 0

        bucket.append(now)
        return True, max(limit - len(bucket), 0)


class RedisRateLimiter:
    """Distributed sliding-window limiter backed by Redis sorted sets."""

    def __init__(self, redis_client) -> None:
        self._redis = redis_client
        self._prefix = "boundary_layer:rate_limit:"

    def allow(self, key: str, limit: int, window: int) -> tuple[bool, int]:
        now = time.time()
        window_start = now - window
        redis_key = f"{self._prefix}{key}"
        member = f"{now}:{uuid.uuid4().hex}"

        pipe = self._redis.pipeline()
        pipe.zremrangebyscore(redis_key, 0, window_start)
        pipe.zcard(redis_key)
        _, count = pipe.execute()

        if count >= limit:
            return False, 0

        pipe = self._redis.pipeline()
        pipe.zadd(redis_key, {member: now})
        pipe.expire(redis_key, window + 1)
        pipe.zcard(redis_key)
        _, _, count = pipe.execute()
        return True, max(limit - count, 0)


def build_rate_limiter(backend: str):
    if backend != "redis":
        return InMemoryRateLimiter()

    try:
        from apps.api.redis_client import get_redis_client

        return RedisRateLimiter(get_redis_client())
    except Exception as exc:
        logger.warning(
            "Redis rate limit backend unavailable; falling back to in-memory limiter",
            extra={"error": str(exc)},
        )
        return InMemoryRateLimiter()
