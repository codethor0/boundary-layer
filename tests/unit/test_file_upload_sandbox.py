"""Tests for File Upload Sandbox Hardening Lab."""

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from labs.file_upload import run_file_upload_lab

client = TestClient(app)


def test_vulnerable_mode_still_works():
    result = run_file_upload_lab("vulnerable")
    assert result["blocked"] is False
    assert result["lab"] == "file-upload"


def test_hardened_mode_still_works_with_defaults():
    result = run_file_upload_lab("hardened")
    assert result["blocked"] is True


def test_vulnerable_simulates_unsafe_extraction():
    result = run_file_upload_lab("vulnerable")
    assert any("without sandbox" in event for event in result["events"])
    assert result["_extraction_result"] == "unsafe"


def test_vulnerable_allows_egress_when_attempted():
    result = run_file_upload_lab("vulnerable", egress_attempted=True)
    assert any(
        "egress was not restricted" in event.lower() for event in result["events"]
    )


def test_vulnerable_allows_active_content():
    result = run_file_upload_lab("vulnerable", contains_active_content=True)
    assert any("Active content was not blocked" in event for event in result["events"])


def test_vulnerable_allows_hidden_instruction_into_context():
    result = run_file_upload_lab("vulnerable", contains_hidden_instruction=True)
    assert result["_context_insertion_allowed"] is True
    assert any("entered model context directly" in event for event in result["events"])


def test_hardened_applies_sandbox():
    result = run_file_upload_lab("hardened")
    assert result["_sandbox_applied"] is True
    assert any("Sandbox policy applied" in event for event in result["events"])


def test_hardened_blocks_egress_when_attempted():
    result = run_file_upload_lab("hardened", egress_attempted=True)
    assert result["_egress_blocked"] is True
    assert any("Network egress blocked" in event for event in result["events"])


def test_hardened_blocks_active_content_when_present():
    result = run_file_upload_lab("hardened", contains_active_content=True)
    assert result["_active_content_blocked"] is True
    assert any(
        "Active content detected and blocked" in event for event in result["events"]
    )


def test_hardened_detects_hidden_instruction_when_present():
    result = run_file_upload_lab("hardened", contains_hidden_instruction=True)
    assert result["_hidden_instruction_detected"] is True
    assert any("Hidden instruction detected" in event for event in result["events"])


def test_hardened_wraps_extracted_content():
    result = run_file_upload_lab("hardened")
    assert result["_content_wrapped"] is True
    assert any("wrapped as untrusted data" in event for event in result["events"])


def test_hardened_without_risk_fields_not_blocked():
    result = run_file_upload_lab(
        "hardened",
        contains_hidden_instruction=False,
        contains_active_content=False,
        egress_attempted=False,
    )
    assert result["blocked"] is False
    assert result["_sandbox_applied"] is True
    assert result["_extraction_result"] == "sandboxed"


def test_invalid_file_type_fails_closed():
    with pytest.raises(ValueError, match="file_type"):
        run_file_upload_lab("vulnerable", file_type="exe")


def test_api_invalid_file_type_rejected():
    response = client.post(
        "/labs/file-upload/run",
        json={"mode": "vulnerable", "file_type": "exe"},
    )
    assert response.status_code == 422


def test_api_vulnerable_endpoint():
    response = client.post("/labs/file-upload/run", json={"mode": "vulnerable"})
    assert response.status_code == 200
    assert response.json()["blocked"] is False


def test_api_hardened_endpoint():
    response = client.post("/labs/file-upload/run", json={"mode": "hardened"})
    assert response.status_code == 200
    assert response.json()["blocked"] is True


def test_api_hardened_safe_fields_endpoint():
    response = client.post(
        "/labs/file-upload/run",
        json={
            "mode": "hardened",
            "contains_hidden_instruction": False,
            "contains_active_content": False,
            "egress_attempted": False,
        },
    )
    assert response.status_code == 200
    assert response.json()["blocked"] is False
