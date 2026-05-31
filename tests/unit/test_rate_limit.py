"""Rate limiter backend tests."""

from unittest.mock import MagicMock

import pytest
from starlette.requests import Request

from apps.api import config
from apps.api.middleware import RateLimitMiddleware
from apps.api.rate_limit import (
    InMemoryRateLimiter,
    RateLimitUnavailable,
    RedisRateLimiter,
    build_rate_limiter,
)


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


def test_redis_rate_limiter_fail_open_for_local_lab():
    redis_client = MagicMock()
    redis_client.pipeline.side_effect = ConnectionError("redis unavailable")
    limiter = RedisRateLimiter(redis_client, fail_open=True)

    allowed, remaining = limiter.allow("client-a", limit=10, window=60)

    assert allowed is True
    assert remaining == 10


def test_redis_rate_limiter_fail_closed_when_configured():
    redis_client = MagicMock()
    redis_client.pipeline.side_effect = ConnectionError("redis unavailable")
    limiter = RedisRateLimiter(redis_client, fail_open=False)

    with pytest.raises(RateLimitUnavailable, match="redis unavailable"):
        limiter.allow("client-a", limit=10, window=60)


def test_build_rate_limiter_fail_closed_raises_when_redis_unavailable(monkeypatch):
    def _raise_connection_error():
        raise ConnectionError("redis unavailable")

    monkeypatch.setattr(
        "apps.api.redis_client.get_redis_client",
        _raise_connection_error,
    )
    with pytest.raises(RateLimitUnavailable, match="redis unavailable"):
        build_rate_limiter("redis", fail_open=False)


def _request_with_client(host: str, xff: str | None = None) -> Request:
    headers = []
    if xff is not None:
        headers.append((b"x-forwarded-for", xff.encode()))
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/labs",
        "headers": headers,
        "client": (host, 12345),
    }
    return Request(scope)


def test_client_key_ignores_spoofed_xff_by_default():
    middleware = RateLimitMiddleware(app=MagicMock())
    settings = config.Settings.model_construct(
        trust_proxy_headers=False,
        boundary_layer_env="development",
    )
    request = _request_with_client("10.0.0.5", "1.2.3.4, 203.0.113.9")

    assert middleware._client_key(request, settings) == "10.0.0.5"


def test_client_key_uses_rightmost_xff_when_trusted():
    middleware = RateLimitMiddleware(app=MagicMock())
    settings = config.Settings.model_construct(
        trust_proxy_headers=True,
        boundary_layer_env="production",
    )
    request = _request_with_client("172.18.0.8", "1.2.3.4, 203.0.113.9")

    assert middleware._client_key(request, settings) == "203.0.113.9"


def test_spoofed_leftmost_xff_does_not_isolate_rate_limit_buckets():
    limiter = InMemoryRateLimiter()
    settings = config.Settings.model_construct(trust_proxy_headers=False)
    middleware = RateLimitMiddleware(app=MagicMock())
    direct_host = "10.0.0.5"

    for spoofed in ("1.2.3.4", "5.6.7.8", "9.9.9.9"):
        request = _request_with_client(direct_host, spoofed)
        key = middleware._client_key(request, settings)
        assert key == direct_host
        limiter.allow(key, limit=2, window=60)

    request = _request_with_client(direct_host, "1.2.3.4")
    key = middleware._client_key(request, settings)
    allowed, _ = limiter.allow(key, limit=2, window=60)
    assert allowed is False
