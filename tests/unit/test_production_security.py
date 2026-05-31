"""Production security and configuration tests."""

from unittest.mock import patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from apps.api import config
from apps.api.config import get_settings
from apps.api.main import app
from apps.api.security import enforce_vulnerable_allowed, verify_api_access


@pytest.fixture(autouse=True)
def reset_settings_cache():
    config.get_settings.cache_clear()
    yield
    config.get_settings.cache_clear()


def test_production_settings_require_secrets(monkeypatch):
    monkeypatch.setenv("BOUNDARY_LAYER_ENV", "production")
    with pytest.raises(ValueError, match="BOUNDARY_LAYER_API_KEY"):
        config.Settings()


def test_production_settings_apply_secure_defaults(monkeypatch):
    monkeypatch.setenv("BOUNDARY_LAYER_ENV", "production")
    monkeypatch.setenv("BOUNDARY_LAYER_API_KEY", "a" * 32)
    monkeypatch.setenv("BOUNDARY_LAYER_METRICS_TOKEN", "b" * 32)
    monkeypatch.setenv("POSTGRES_PASSWORD", "postgres-secret-16")
    monkeypatch.setenv("REDIS_PASSWORD", "redis-secret-16chars")
    monkeypatch.setenv("SESSION_HMAC_SECRET", "session-hmac-secret")
    settings = config.Settings()
    assert settings.auth_enabled is True
    assert settings.allow_vulnerable is False
    assert settings.metrics_auth_required is True
    assert settings.rate_limit_enabled is True
    assert settings.rate_limit_backend == "redis"
    assert settings.expose_openapi is False


def test_verify_api_access_rejects_missing_key():
    settings = config.Settings.model_construct(
        auth_enabled=True,
        api_key="c" * 32,
        boundary_layer_env="development",
    )
    with pytest.raises(HTTPException) as exc:
        verify_api_access(
            authorization=None,
            x_api_key=None,
            settings=settings,
        )
    assert exc.value.status_code == 401


def test_verify_api_access_accepts_bearer_token():
    api_key = "d" * 32
    settings = config.Settings.model_construct(
        auth_enabled=True,
        api_key=api_key,
        boundary_layer_env="development",
    )
    verify_api_access(
        authorization=f"Bearer {api_key}",
        x_api_key=None,
        settings=settings,
    )


def test_enforce_vulnerable_allowed_blocks_when_disabled():
    settings = config.Settings.model_construct(
        allow_vulnerable=False,
        boundary_layer_env="production",
    )
    with pytest.raises(HTTPException) as exc:
        enforce_vulnerable_allowed("vulnerable", settings)
    assert exc.value.status_code == 403


def _test_settings(**overrides):
    defaults = {
        "boundary_layer_env": "development",
        "auth_enabled": False,
        "api_key": "",
        "metrics_auth_required": False,
        "metrics_token": "",
        "allow_vulnerable": True,
        "rate_limit_enabled": False,
        "rate_limit_requests": 120,
        "rate_limit_window_seconds": 60,
        "rate_limit_backend": "memory",
        "expose_openapi": True,
        "app_version": "1.3.2",
    }
    defaults.update(overrides)
    return config.Settings.model_construct(**defaults)


def _patch_settings(monkeypatch, settings):
    monkeypatch.setattr(config, "get_settings", lambda: settings)
    monkeypatch.setattr("apps.api.security.get_settings", lambda: settings)
    monkeypatch.setattr("apps.api.middleware.get_settings", lambda: settings)
    monkeypatch.setattr("apps.api.main.get_settings", lambda: settings)
    app.dependency_overrides[get_settings] = lambda: settings


@pytest.fixture(autouse=True)
def clear_dependency_overrides():
    yield
    app.dependency_overrides.clear()


def test_labs_require_auth_when_enabled(monkeypatch):
    api_key = "e" * 32
    _patch_settings(
        monkeypatch,
        _test_settings(auth_enabled=True, api_key=api_key),
    )
    client = TestClient(app)
    response = client.post("/labs/redis/run", json={"mode": "hardened"})
    assert response.status_code == 401

    authed = client.post(
        "/labs/redis/run",
        json={"mode": "hardened"},
        headers={"Authorization": f"Bearer {api_key}"},
    )
    assert authed.status_code == 200


def test_metrics_require_token_when_enabled(monkeypatch):
    metrics_token = "f" * 32
    _patch_settings(
        monkeypatch,
        _test_settings(
            metrics_auth_required=True,
            metrics_token=metrics_token,
        ),
    )
    client = TestClient(app)
    denied = client.get("/metrics")
    assert denied.status_code == 401

    allowed = client.get(
        "/metrics",
        headers={"Authorization": f"Bearer {metrics_token}"},
    )
    assert allowed.status_code == 200


def test_vulnerable_mode_blocked_when_disabled(monkeypatch):
    _patch_settings(
        monkeypatch,
        _test_settings(allow_vulnerable=False),
    )
    client = TestClient(app)
    response = client.post("/labs/redis/run", json={"mode": "vulnerable"})
    assert response.status_code == 403


def test_health_stays_unauthenticated(monkeypatch):
    _patch_settings(
        monkeypatch,
        _test_settings(auth_enabled=True, api_key="g" * 32),
    )
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_rate_limit_returns_429(monkeypatch):
    _patch_settings(
        monkeypatch,
        _test_settings(
            rate_limit_enabled=True,
            rate_limit_requests=2,
            rate_limit_window_seconds=60,
            rate_limit_backend="memory",
        ),
    )
    client = TestClient(app)
    assert client.get("/labs").status_code == 200
    assert client.get("/labs").status_code == 200
    limited = client.get("/labs")
    assert limited.status_code == 429


def test_production_settings_require_data_store_secrets(monkeypatch):
    monkeypatch.setenv("BOUNDARY_LAYER_ENV", "production")
    monkeypatch.setenv("BOUNDARY_LAYER_API_KEY", "a" * 32)
    monkeypatch.setenv("BOUNDARY_LAYER_METRICS_TOKEN", "b" * 32)
    monkeypatch.setenv("POSTGRES_PASSWORD", "short")
    with pytest.raises(ValueError, match="POSTGRES_PASSWORD"):
        config.Settings()


def test_openapi_disabled_in_production(monkeypatch):
    _patch_settings(
        monkeypatch,
        _test_settings(
            boundary_layer_env="production",
            expose_openapi=False,
        ),
    )
    client = TestClient(app)
    assert client.get("/docs").status_code == 404
    assert client.get("/openapi.json").status_code == 404


def test_ready_requires_metrics_token_when_enabled(monkeypatch):
    metrics_token = "h" * 32
    _patch_settings(
        monkeypatch,
        _test_settings(
            metrics_auth_required=True,
            metrics_token=metrics_token,
        ),
    )
    client = TestClient(app)
    denied = client.get("/ready")
    assert denied.status_code == 401

    with (
        patch("apps.api.readiness._check_postgres", return_value=(True, "connected")),
        patch("apps.api.readiness._check_redis", return_value=(True, "connected")),
    ):
        allowed = client.get(
            "/ready",
            headers={"Authorization": f"Bearer {metrics_token}"},
        )
    assert allowed.status_code == 200
