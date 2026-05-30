"""Tests for Circuit Breaker Simulation Lab."""

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from labs.circuit_breaker import (
    SAFE_CAPACITY,
    run_circuit_breaker_lab,
)

client = TestClient(app)


def test_list_labs_includes_circuit_breaker():
    response = client.get("/labs")
    assert response.status_code == 200
    lab_ids = [lab["id"] for lab in response.json()["labs"]]
    assert "circuit-breaker" in lab_ids


def test_circuit_breaker_vulnerable_accepts_all_work():
    result = run_circuit_breaker_lab("vulnerable", requested_work_units=250)
    assert result["blocked"] is False
    assert result["_accepted_work_units"] == 250
    assert result["_shed_work_units"] == 0
    assert result["_circuit_breaker_state"] == 0


def test_circuit_breaker_hardened_opens_when_over_capacity():
    result = run_circuit_breaker_lab("hardened", requested_work_units=250)
    assert result["blocked"] is True
    assert result["_accepted_work_units"] == SAFE_CAPACITY
    assert result["_shed_work_units"] == 150
    assert result["_circuit_breaker_state"] == 1


def test_circuit_breaker_hardened_closed_within_capacity():
    result = run_circuit_breaker_lab("hardened", requested_work_units=50)
    assert result["blocked"] is False
    assert result["_accepted_work_units"] == 50
    assert result["_shed_work_units"] == 0
    assert result["_circuit_breaker_state"] == 0


def test_circuit_breaker_default_requested_work_units():
    response = client.post(
        "/labs/circuit-breaker/run",
        json={"mode": "vulnerable"},
    )
    assert response.status_code == 200
    assert response.json()["blocked"] is False


def test_circuit_breaker_invalid_mode_fails_closed():
    response = client.post(
        "/labs/circuit-breaker/run",
        json={"mode": "invalid"},
    )
    assert response.status_code == 422


def test_circuit_breaker_invalid_requested_work_units_fails_closed():
    response = client.post(
        "/labs/circuit-breaker/run",
        json={"mode": "vulnerable", "requested_work_units": 0},
    )
    assert response.status_code == 422

    response = client.post(
        "/labs/circuit-breaker/run",
        json={"mode": "vulnerable", "requested_work_units": 1001},
    )
    assert response.status_code == 422


def test_circuit_breaker_vulnerable_endpoint():
    response = client.post(
        "/labs/circuit-breaker/run",
        json={"mode": "vulnerable", "requested_work_units": 10},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["lab"] == "circuit-breaker"
    assert data["mode"] == "vulnerable"
    assert data["blocked"] is False


def test_circuit_breaker_hardened_endpoint():
    response = client.post(
        "/labs/circuit-breaker/run",
        json={"mode": "hardened", "requested_work_units": 250},
    )
    assert response.status_code == 200
    assert response.json()["blocked"] is True


def test_circuit_breaker_invalid_work_units_module_validation():
    with pytest.raises(ValueError, match="requested_work_units"):
        run_circuit_breaker_lab("vulnerable", requested_work_units=0)
