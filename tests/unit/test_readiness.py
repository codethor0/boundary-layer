"""Readiness endpoint tests."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from apps.api.main import app

client = TestClient(app)


def test_ready_when_dependencies_available():
    with (
        patch("apps.api.readiness._check_postgres", return_value=(True, "connected")),
        patch("apps.api.readiness._check_redis", return_value=(True, "connected")),
    ):
        response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["checks"]["postgres"]["ok"] is True
    assert data["checks"]["redis"]["ok"] is True


def test_ready_returns_503_when_postgres_unavailable():
    with (
        patch(
            "apps.api.readiness._check_postgres",
            return_value=(False, "connection refused"),
        ),
        patch("apps.api.readiness._check_redis", return_value=(True, "connected")),
    ):
        response = client.get("/ready")
    assert response.status_code == 503
    detail = response.json()["detail"]
    assert detail["status"] == "not_ready"
    assert detail["checks"]["postgres"]["ok"] is False
