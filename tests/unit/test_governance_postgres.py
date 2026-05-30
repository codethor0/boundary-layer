"""Tests for PostgreSQL-backed governance lab behavior."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from labs.governance import run_governance_lab

client = TestClient(app)


@pytest.fixture(autouse=True)
def postgres_fallback_env(monkeypatch):
    monkeypatch.setenv("BOUNDARY_LAYER_POSTGRES_LIVE", "false")


def test_governance_fallback_vulnerable_orphans():
    result = run_governance_lab("vulnerable")
    assert result["blocked"] is False
    assert result["_orphan_count"] == 7
    assert "fallback" in result["events"][0].lower()


def test_governance_fallback_hardened_audit_flag():
    result = run_governance_lab("hardened")
    assert result["blocked"] is True
    assert result["_audit_complete"] is True
    assert result["_orphan_count"] == 0


@patch("labs.governance.check_postgres_connection")
@patch("labs.governance.init_db")
@patch("labs.governance.reset_governance_lab_records")
@patch("labs.governance.create_prompt_lifecycle_records")
@patch("labs.governance.delete_primary_only")
@patch("labs.governance.count_orphan_records")
def test_governance_live_vulnerable_uses_database(
    mock_count,
    mock_delete_primary,
    mock_create,
    mock_reset,
    mock_init,
    mock_check,
    monkeypatch,
):
    monkeypatch.setenv("BOUNDARY_LAYER_POSTGRES_LIVE", "true")
    mock_create.return_value = "boundary-layer-governance-prompt-001"
    mock_count.return_value = 4

    result = run_governance_lab("vulnerable")

    assert result["blocked"] is False
    assert result["_orphan_count"] == 4
    assert any("PostgreSQL" in event for event in result["events"])
    mock_delete_primary.assert_called_once()


@patch("labs.governance.check_postgres_connection")
@patch("labs.governance.init_db")
@patch("labs.governance.reset_governance_lab_records")
@patch("labs.governance.create_prompt_lifecycle_records")
@patch("labs.governance.delete_all_prompt_lifecycle_records")
@patch("labs.governance.count_orphan_records")
@patch("labs.governance.insert_deletion_audit")
def test_governance_live_hardened_writes_audit(
    mock_audit,
    mock_count,
    mock_delete_all,
    mock_create,
    mock_reset,
    mock_init,
    mock_check,
    monkeypatch,
):
    monkeypatch.setenv("BOUNDARY_LAYER_POSTGRES_LIVE", "true")
    mock_create.return_value = "boundary-layer-governance-prompt-001"
    mock_count.return_value = 0
    mock_audit.return_value = "boundary-layer-governance-audit-test"

    result = run_governance_lab("hardened")

    assert result["blocked"] is True
    assert result["_audit_complete"] is True
    mock_audit.assert_called_once()
    assert any("deletion audit record" in event for event in result["events"])


def test_governance_live_unavailable_returns_503(monkeypatch):
    monkeypatch.setenv("BOUNDARY_LAYER_POSTGRES_LIVE", "true")

    with patch(
        "labs.governance.check_postgres_connection",
        side_effect=ConnectionError("connection refused"),
    ):
        response = client.post("/labs/governance/run", json={"mode": "hardened"})

    assert response.status_code == 503
    assert "BOUNDARY_LAYER_POSTGRES_LIVE=true" in response.json()["detail"]
