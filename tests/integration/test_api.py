"""Integration tests for BoundaryLayer API."""

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app

client = TestClient(app)

LAB_ENDPOINTS = [
    "/labs/tool-router/run",
    "/labs/redis/run",
    "/labs/authz/run",
    "/labs/file-upload/run",
    "/labs/governance/run",
    "/labs/postgres-write-storm/run",
    "/labs/circuit-breaker/run",
    "/labs/sse-exhaustion/run",
    "/labs/prompt-cache-isolation/run",
]


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_list_labs():
    response = client.get("/labs")
    assert response.status_code == 200
    data = response.json()
    assert len(data["labs"]) == 9


@pytest.mark.parametrize("endpoint", LAB_ENDPOINTS)
@pytest.mark.parametrize("mode", ["vulnerable", "hardened"])
def test_lab_endpoints(endpoint, mode):
    response = client.post(endpoint, json={"mode": mode})
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == mode
    assert "blocked" in data
    assert "risk" in data
    assert "control" in data
    assert "events" in data
    assert "summary" in data


def test_invalid_mode_rejected():
    response = client.post("/labs/redis/run", json={"mode": "invalid"})
    assert response.status_code == 422
