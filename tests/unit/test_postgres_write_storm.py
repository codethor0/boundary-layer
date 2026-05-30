"""Tests for PostgreSQL Write Storm Lab."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from labs.postgres_write_storm import (
    DEFAULT_REQUESTED_WRITES,
    HARDENED_WRITE_BUDGET,
    run_postgres_write_storm_lab,
)

client = TestClient(app)


@pytest.fixture(autouse=True)
def postgres_fallback_env(monkeypatch):
    monkeypatch.setenv("BOUNDARY_LAYER_POSTGRES_LIVE", "false")


def test_list_labs_includes_postgres_write_storm():
    response = client.get("/labs")
    assert response.status_code == 200
    lab_ids = [lab["id"] for lab in response.json()["labs"]]
    assert "postgres-write-storm" in lab_ids


def test_write_storm_fallback_vulnerable_is_deterministic():
    result = run_postgres_write_storm_lab("vulnerable")
    assert result["blocked"] is False
    assert result["_inserted_count"] == DEFAULT_REQUESTED_WRITES
    assert result["_blocked_writes_count"] == 0
    assert "fallback" in result["events"][0].lower()


def test_write_storm_fallback_hardened_blocks_excess():
    result = run_postgres_write_storm_lab("hardened")
    assert result["blocked"] is True
    assert result["_inserted_count"] == HARDENED_WRITE_BUDGET
    assert result["_blocked_writes_count"] == (
        DEFAULT_REQUESTED_WRITES - HARDENED_WRITE_BUDGET
    )


def test_write_storm_default_requested_writes():
    response = client.post(
        "/labs/postgres-write-storm/run",
        json={"mode": "vulnerable"},
    )
    assert response.status_code == 200
    assert response.json()["blocked"] is False


def test_write_storm_invalid_mode_fails_closed():
    response = client.post(
        "/labs/postgres-write-storm/run",
        json={"mode": "invalid"},
    )
    assert response.status_code == 422


def test_write_storm_invalid_requested_writes_fails_closed():
    response = client.post(
        "/labs/postgres-write-storm/run",
        json={"mode": "vulnerable", "requested_writes": 0},
    )
    assert response.status_code == 422

    response = client.post(
        "/labs/postgres-write-storm/run",
        json={"mode": "vulnerable", "requested_writes": 1001},
    )
    assert response.status_code == 422


def test_write_storm_vulnerable_endpoint():
    response = client.post(
        "/labs/postgres-write-storm/run",
        json={"mode": "vulnerable", "requested_writes": 10},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["lab"] == "postgres-write-storm"
    assert data["mode"] == "vulnerable"
    assert data["blocked"] is False


def test_write_storm_hardened_endpoint():
    response = client.post(
        "/labs/postgres-write-storm/run",
        json={"mode": "hardened", "requested_writes": 10},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["blocked"] is True


@patch("labs.postgres_write_storm.check_postgres_connection")
@patch("labs.postgres_write_storm.init_db")
@patch("labs.postgres_write_storm.reset_write_storm_events")
@patch("labs.postgres_write_storm.insert_write_storm_events")
@patch("labs.postgres_write_storm.count_write_storm_events")
def test_write_storm_live_vulnerable_inserts(
    mock_count,
    mock_insert,
    mock_reset,
    mock_init,
    mock_check,
    monkeypatch,
):
    monkeypatch.setenv("BOUNDARY_LAYER_POSTGRES_LIVE", "true")
    mock_insert.return_value = 250
    mock_count.return_value = 250

    result = run_postgres_write_storm_lab("vulnerable", requested_writes=250)

    assert result["blocked"] is False
    assert result["_inserted_count"] == 250
    assert any("PostgreSQL" in event for event in result["events"])
    mock_insert.assert_called_once()


@patch("labs.postgres_write_storm.check_postgres_connection")
@patch("labs.postgres_write_storm.init_db")
@patch("labs.postgres_write_storm.reset_write_storm_events")
@patch("labs.postgres_write_storm.insert_write_storm_events")
@patch("labs.postgres_write_storm.count_write_storm_events")
def test_write_storm_live_hardened_caps_inserts(
    mock_count,
    mock_insert,
    mock_reset,
    mock_init,
    mock_check,
    monkeypatch,
):
    monkeypatch.setenv("BOUNDARY_LAYER_POSTGRES_LIVE", "true")
    mock_insert.return_value = HARDENED_WRITE_BUDGET
    mock_count.return_value = HARDENED_WRITE_BUDGET

    result = run_postgres_write_storm_lab("hardened", requested_writes=250)

    assert result["blocked"] is True
    assert result["_inserted_count"] == HARDENED_WRITE_BUDGET
    assert result["_blocked_writes_count"] == 200
    mock_insert.assert_called_once()


def test_write_storm_live_unavailable_returns_503(monkeypatch):
    monkeypatch.setenv("BOUNDARY_LAYER_POSTGRES_LIVE", "true")

    with patch(
        "labs.postgres_write_storm.check_postgres_connection",
        side_effect=ConnectionError("connection refused"),
    ):
        response = client.post(
            "/labs/postgres-write-storm/run",
            json={"mode": "vulnerable"},
        )

    assert response.status_code == 503
    assert "BOUNDARY_LAYER_POSTGRES_LIVE=true" in response.json()["detail"]
