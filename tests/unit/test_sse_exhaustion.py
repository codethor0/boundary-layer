"""Tests for SSE Exhaustion Simulation Lab."""

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from labs.sse_exhaustion import (
    MAX_STREAMS_PER_TENANT,
    run_sse_exhaustion_lab,
)

client = TestClient(app)


def test_list_labs_includes_sse_exhaustion():
    response = client.get("/labs")
    assert response.status_code == 200
    lab_ids = [lab["id"] for lab in response.json()["labs"]]
    assert "sse-exhaustion" in lab_ids


def test_sse_vulnerable_accepts_all_streams():
    result = run_sse_exhaustion_lab("vulnerable", requested_streams=250)
    assert result["blocked"] is False
    assert result["_accepted_streams"] == 250
    assert result["_rejected_streams"] == 0
    assert result["_orphaned_streams"] == 200


def test_sse_vulnerable_reports_orphaned_streams():
    result = run_sse_exhaustion_lab("vulnerable", requested_streams=100)
    assert result["_orphaned_streams"] == 50
    assert any("orphaned" in event.lower() for event in result["events"])


def test_sse_hardened_rejects_excess_streams():
    result = run_sse_exhaustion_lab("hardened", requested_streams=250)
    assert result["blocked"] is True
    assert result["_accepted_streams"] == MAX_STREAMS_PER_TENANT
    assert result["_rejected_streams"] == 200
    assert result["_orphaned_streams"] == 0


def test_sse_hardened_accepts_within_cap():
    result = run_sse_exhaustion_lab("hardened", requested_streams=25)
    assert result["blocked"] is False
    assert result["_accepted_streams"] == 25
    assert result["_rejected_streams"] == 0


def test_sse_hardened_applies_cleanup():
    result = run_sse_exhaustion_lab("hardened", requested_streams=250)
    assert result["_cleanup_applied"] is True
    assert any("cleanup" in event.lower() for event in result["events"])


def test_sse_default_requested_streams():
    response = client.post(
        "/labs/sse-exhaustion/run",
        json={"mode": "vulnerable"},
    )
    assert response.status_code == 200
    assert response.json()["blocked"] is False


def test_sse_invalid_mode_fails_closed():
    response = client.post(
        "/labs/sse-exhaustion/run",
        json={"mode": "invalid"},
    )
    assert response.status_code == 422


def test_sse_invalid_requested_streams_fails_closed():
    response = client.post(
        "/labs/sse-exhaustion/run",
        json={"mode": "vulnerable", "requested_streams": 0},
    )
    assert response.status_code == 422

    response = client.post(
        "/labs/sse-exhaustion/run",
        json={"mode": "vulnerable", "requested_streams": 1001},
    )
    assert response.status_code == 422


def test_sse_invalid_stream_duration_fails_closed():
    response = client.post(
        "/labs/sse-exhaustion/run",
        json={"mode": "vulnerable", "stream_duration_seconds": 0},
    )
    assert response.status_code == 422

    response = client.post(
        "/labs/sse-exhaustion/run",
        json={"mode": "vulnerable", "stream_duration_seconds": 3601},
    )
    assert response.status_code == 422


def test_sse_vulnerable_endpoint():
    response = client.post(
        "/labs/sse-exhaustion/run",
        json={"mode": "vulnerable", "requested_streams": 10},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["lab"] == "sse-exhaustion"
    assert data["blocked"] is False


def test_sse_hardened_endpoint():
    response = client.post(
        "/labs/sse-exhaustion/run",
        json={"mode": "hardened", "requested_streams": 250},
    )
    assert response.status_code == 200
    assert response.json()["blocked"] is True


def test_sse_module_validation_errors():
    with pytest.raises(ValueError, match="requested_streams"):
        run_sse_exhaustion_lab("vulnerable", requested_streams=0)

    with pytest.raises(ValueError, match="stream_duration_seconds"):
        run_sse_exhaustion_lab("vulnerable", stream_duration_seconds=0)
