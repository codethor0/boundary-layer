"""Rate limiter backend tests."""

from unittest.mock import MagicMock

from apps.api.rate_limit import InMemoryRateLimiter, RedisRateLimiter


def test_in_memory_rate_limiter_blocks_after_limit():
    limiter = InMemoryRateLimiter()
    assert limiter.allow("client-a", limit=2, window=60) == (True, 1)
    assert limiter.allow("client-a", limit=2, window=60) == (True, 0)
    assert limiter.allow("client-a", limit=2, window=60) == (False, 0)


def test_in_memory_rate_limiter_isolated_by_key():
    limiter = InMemoryRateLimiter()
    assert limiter.allow("client-a", limit=1, window=60)[0] is True
    assert limiter.allow("client-b", limit=1, window=60)[0] is True


def test_redis_rate_limiter_uses_sorted_set_pipeline():
    redis_client = MagicMock()
    first_pipe = MagicMock()
    second_pipe = MagicMock()
    redis_client.pipeline.side_effect = [first_pipe, second_pipe]
    first_pipe.execute.return_value = [0, 1]
    second_pipe.execute.return_value = [True, True, 2]

    limiter = RedisRateLimiter(redis_client)
    allowed, remaining = limiter.allow("client-a", limit=3, window=60)

    assert allowed is True
    assert remaining == 1
    assert redis_client.pipeline.call_count == 2


def test_redis_rate_limiter_blocks_at_limit():
    redis_client = MagicMock()
    pipe = MagicMock()
    redis_client.pipeline.return_value = pipe
    pipe.execute.return_value = [0, 3]

    limiter = RedisRateLimiter(redis_client)
    allowed, remaining = limiter.allow("client-a", limit=3, window=60)

    assert allowed is False
    assert remaining == 0
