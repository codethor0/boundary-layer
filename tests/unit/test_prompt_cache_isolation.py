"""Tests for Prompt Cache Isolation Lab."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from labs.prompt_cache_isolation import (
    global_cache_key,
    run_prompt_cache_isolation_lab,
    tenant_cache_key,
)

client = TestClient(app)


@pytest.fixture(autouse=True)
def redis_fallback_env(monkeypatch):
    monkeypatch.setenv("BOUNDARY_LAYER_REDIS_LIVE", "false")


def test_vulnerable_fallback_detects_cross_tenant_hit():
    result = run_prompt_cache_isolation_lab("vulnerable")
    assert result["blocked"] is False
    assert result["_cache_bleed_detected"] is True
    assert result["_cache_hit_cross_tenant"] is True
    assert result["_tenant_b_hit_type"] == "cross_tenant"
    assert any("Cross-tenant cache hit detected" in event for event in result["events"])


def test_hardened_fallback_prevents_cross_tenant_hit():
    result = run_prompt_cache_isolation_lab("hardened")
    assert result["blocked"] is True
    assert result["_isolation_applied"] is True
    assert result["_cache_bleed_detected"] is False
    assert result["_tenant_b_hit_type"] == "miss"
    assert any("Cache bleed prevented" in event for event in result["events"])


def test_fallback_mode_is_deterministic():
    first = run_prompt_cache_isolation_lab("vulnerable")
    second = run_prompt_cache_isolation_lab("vulnerable")
    assert first["summary"] == second["summary"]
    assert any("fallback" in event.lower() for event in first["events"])


def test_vulnerable_uses_shared_cache_key():
    result = run_prompt_cache_isolation_lab("vulnerable")
    assert result["_tenant_a_cache_key"] == result["_tenant_b_cache_key"]
    assert ":global:" in result["_tenant_a_cache_key"]


def test_hardened_uses_tenant_scoped_keys():
    result = run_prompt_cache_isolation_lab("hardened")
    assert result["_tenant_a_cache_key"] != result["_tenant_b_cache_key"]
    assert "tenant-a:" in result["_tenant_a_cache_key"]
    assert "tenant-b:" in result["_tenant_b_cache_key"]


def test_global_and_tenant_cache_key_helpers():
    prefix = "summarize confidential acquisition plan"
    assert global_cache_key(prefix).startswith(
        "boundary_layer:lab:prompt_cache:global:"
    )
    assert tenant_cache_key("tenant-a", prefix).startswith(
        "boundary_layer:lab:prompt_cache:tenant-a:"
    )


def test_invalid_tenant_fails_closed():
    with pytest.raises(ValueError, match="tenant_a"):
        run_prompt_cache_isolation_lab("vulnerable", tenant_a="   ")


def test_invalid_prompt_prefix_fails_closed():
    with pytest.raises(ValueError, match="prompt_prefix"):
        run_prompt_cache_isolation_lab("vulnerable", prompt_prefix="")


@patch("labs.prompt_cache_isolation._get_redis_client")
def test_live_mode_writes_namespaced_keys(mock_get_client, monkeypatch):
    monkeypatch.setenv("BOUNDARY_LAYER_REDIS_LIVE", "true")
    mock_client = MagicMock()
    stored: dict[str, str] = {}

    def setex(key, ttl, value):
        stored[key] = value

    mock_client.setex.side_effect = setex
    mock_client.get.side_effect = lambda key: stored.get(key)
    mock_get_client.return_value = mock_client

    result = run_prompt_cache_isolation_lab("hardened")
    assert result["blocked"] is True
    assert any("Connected to live Redis" in event for event in result["events"])
    assert mock_client.setex.called


def test_live_mode_fails_clearly_when_unavailable(monkeypatch):
    monkeypatch.setenv("BOUNDARY_LAYER_REDIS_LIVE", "true")
    with patch(
        "labs.prompt_cache_isolation._get_redis_client",
        side_effect=ConnectionError("connection refused"),
    ):
        with pytest.raises(RuntimeError, match="BOUNDARY_LAYER_REDIS_LIVE=true"):
            run_prompt_cache_isolation_lab("hardened")


def test_api_vulnerable_mode():
    response = client.post(
        "/labs/prompt-cache-isolation/run",
        json={"mode": "vulnerable"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["lab"] == "prompt-cache-isolation"
    assert data["blocked"] is False


def test_api_hardened_mode():
    response = client.post(
        "/labs/prompt-cache-isolation/run",
        json={"mode": "hardened"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["blocked"] is True


def test_api_invalid_mode_rejected():
    response = client.post(
        "/labs/prompt-cache-isolation/run",
        json={"mode": "invalid"},
    )
    assert response.status_code == 422


def test_api_invalid_tenant_rejected():
    response = client.post(
        "/labs/prompt-cache-isolation/run",
        json={"mode": "vulnerable", "tenant_a": ""},
    )
    assert response.status_code == 422


def test_api_invalid_prompt_prefix_rejected():
    response = client.post(
        "/labs/prompt-cache-isolation/run",
        json={"mode": "vulnerable", "prompt_prefix": ""},
    )
    assert response.status_code == 422


def test_api_live_redis_unavailable_returns_503(monkeypatch):
    monkeypatch.setenv("BOUNDARY_LAYER_REDIS_LIVE", "true")
    with patch(
        "labs.prompt_cache_isolation._get_redis_client",
        side_effect=ConnectionError("connection refused"),
    ):
        response = client.post(
            "/labs/prompt-cache-isolation/run",
            json={"mode": "hardened"},
        )
    assert response.status_code == 503
