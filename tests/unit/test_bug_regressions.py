"""Regression tests from bug-hunting passes."""

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from apps.alert_webhook.main import _stored_alerts
from apps.alert_webhook.main import app as webhook_app
from apps.api.rate_limit import RateLimitUnavailable, RedisRateLimiter

webhook_client = TestClient(webhook_app)


@pytest.fixture(autouse=True)
def clear_webhook_alerts():
    _stored_alerts.clear()
    yield
    _stored_alerts.clear()


def test_redis_rate_limiter_fail_open_in_local_lab_mode():
    redis_client = MagicMock()
    redis_client.pipeline.side_effect = ConnectionError("redis unavailable")
    limiter = RedisRateLimiter(redis_client, fail_open=True)

    allowed, remaining = limiter.allow("client-a", limit=10, window=60)

    assert allowed is True
    assert remaining == 10


def test_redis_rate_limiter_fail_closed_in_production_like_mode():
    redis_client = MagicMock()
    redis_client.pipeline.side_effect = ConnectionError("redis unavailable")
    limiter = RedisRateLimiter(redis_client, fail_open=False)

    with pytest.raises(RateLimitUnavailable):
        limiter.allow("client-a", limit=10, window=60)


def test_webhook_rejects_batches_when_store_is_full(monkeypatch):
    from apps.alert_webhook import config

    settings = config.WebhookSettings.model_construct(
        auth_enabled=False,
        auth_token="",
        max_stored_alerts=2,
        boundary_layer_env="development",
    )
    monkeypatch.setattr(config, "get_webhook_settings", lambda: settings)
    monkeypatch.setattr(
        "apps.alert_webhook.main.get_webhook_settings", lambda: settings
    )

    first = webhook_client.post("/alerts", json={"alerts": [{"labels": {"a": "1"}}]})
    assert first.status_code == 200

    second = webhook_client.post("/alerts", json={"alerts": [{"labels": {"a": "2"}}]})
    assert second.status_code == 200

    full = webhook_client.post("/alerts", json={"alerts": [{"labels": {"a": "3"}}]})
    assert full.status_code == 413


def test_webhook_rejects_oversized_batch(monkeypatch):
    from apps.alert_webhook import config

    settings = config.WebhookSettings.model_construct(
        auth_enabled=False,
        auth_token="",
        max_stored_alerts=100,
        boundary_layer_env="development",
    )
    monkeypatch.setattr(config, "get_webhook_settings", lambda: settings)
    monkeypatch.setattr(
        "apps.alert_webhook.main.get_webhook_settings", lambda: settings
    )

    response = webhook_client.post(
        "/alerts",
        json={"alerts": [{"labels": {"a": str(i)}} for i in range(101)]},
    )
    assert response.status_code == 413


def test_list_labs_ok_when_trusted_hosts_set_in_development(monkeypatch):
    """TrustedHostMiddleware must not break TestClient in development."""
    from apps.api import config
    from apps.api.main import app as api_app

    dev_settings = config.Settings.model_construct(
        boundary_layer_env="development",
        trusted_hosts="boundary-layer.local,nginx,localhost,api",
        auth_enabled=False,
        api_key="",
        metrics_auth_required=False,
        metrics_token="",
        allow_vulnerable=True,
        expose_openapi=True,
    )
    monkeypatch.setattr(config, "get_settings", lambda: dev_settings)
    monkeypatch.setattr("apps.api.main.get_settings", lambda: dev_settings)
    api_app.dependency_overrides[config.get_settings] = lambda: dev_settings

    client = TestClient(api_app)
    assert client.get("/labs").status_code == 200

    api_app.dependency_overrides.clear()
