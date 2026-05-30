"""Tests for Redis lab live integration and fallback behavior."""

from unittest.mock import MagicMock, patch

import pytest

from labs.redis_state import run_redis_lab


@pytest.fixture(autouse=True)
def redis_fallback_env(monkeypatch):
    monkeypatch.setenv("BOUNDARY_LAYER_REDIS_LIVE", "false")


def test_redis_fallback_mode_is_deterministic():
    first = run_redis_lab("hardened")
    second = run_redis_lab("hardened")
    assert first["blocked"] is True
    assert second["blocked"] is True
    assert any("fallback" in event.lower() for event in first["events"])


def test_redis_fallback_vulnerable_allows_tampering():
    result = run_redis_lab("vulnerable")
    assert result["blocked"] is False
    assert "admin" in result["summary"]


@patch("labs.redis_state._get_redis_client")
def test_redis_live_mode_writes_to_namespaced_keys(mock_get_client, monkeypatch):
    monkeypatch.setenv("BOUNDARY_LAYER_REDIS_LIVE", "true")
    mock_client = MagicMock()
    stored: dict[str, str] = {}

    def setex(key, ttl, value):
        stored[key] = value

    def set_value(key, value):
        stored[key] = value

    def get_value(key):
        return stored.get(key)

    mock_client.setex.side_effect = setex
    mock_client.set.side_effect = set_value
    mock_client.get.side_effect = get_value
    mock_get_client.return_value = mock_client

    result = run_redis_lab("hardened")
    assert result["blocked"] is True
    assert any("boundary_layer:lab:redis:" in event for event in result["events"])
    assert mock_client.setex.called
    assert mock_client.set.called


def test_redis_live_mode_fails_clearly_when_unavailable(monkeypatch):
    monkeypatch.setenv("BOUNDARY_LAYER_REDIS_LIVE", "true")

    with patch(
        "labs.redis_state._get_redis_client",
        side_effect=ConnectionError("connection refused"),
    ):
        with pytest.raises(RuntimeError, match="BOUNDARY_LAYER_REDIS_LIVE=true"):
            run_redis_lab("hardened")
