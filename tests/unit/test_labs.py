"""Unit tests for lab modules."""

from labs.authz import run_authz_lab
from labs.file_upload import run_file_upload_lab
from labs.governance import run_governance_lab
from labs.redis_state import run_redis_lab
from labs.tool_router import run_tool_router_lab


def test_tool_router_vulnerable_not_blocked():
    result = run_tool_router_lab("vulnerable")
    assert result["lab"] == "tool-router"
    assert result["mode"] == "vulnerable"
    assert result["blocked"] is False
    assert "delete_all_records" in result["summary"]


def test_tool_router_hardened_blocked():
    result = run_tool_router_lab("hardened")
    assert result["blocked"] is True
    assert "instruction-pattern" in result["control"]


def test_redis_vulnerable_not_blocked():
    result = run_redis_lab("vulnerable")
    assert result["blocked"] is False
    assert "admin" in result["summary"]


def test_redis_hardened_blocked():
    result = run_redis_lab("hardened")
    assert result["blocked"] is True
    assert "HMAC" in result["control"]


def test_authz_vulnerable_not_blocked():
    result = run_authz_lab("vulnerable")
    assert result["blocked"] is False


def test_authz_hardened_blocked():
    result = run_authz_lab("hardened")
    assert result["blocked"] is True
    assert "scope" in result["control"]


def test_file_upload_vulnerable_not_blocked():
    result = run_file_upload_lab("vulnerable")
    assert result["blocked"] is False


def test_file_upload_hardened_blocked():
    result = run_file_upload_lab("hardened")
    assert result["blocked"] is True


def test_governance_vulnerable_not_blocked():
    result = run_governance_lab("vulnerable")
    assert result["blocked"] is False
    summary = result["summary"].lower()
    assert "orphaned" in summary or "downstream" in summary


def test_governance_hardened_blocked():
    result = run_governance_lab("hardened")
    assert result["blocked"] is True
    control = result["control"].lower()
    assert "audit" in control or "cascade" in control
