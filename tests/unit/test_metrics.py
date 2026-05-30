"""Tests for Prometheus metrics integration."""

import re

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app

client = TestClient(app)


def _metrics_text() -> str:
    response = client.get("/metrics")
    assert response.status_code == 200
    return response.text


def _counter_total(body: str, name: str) -> float:
    total = 0.0
    pattern = re.compile(rf"^{re.escape(name)}(?:\{{[^}}]*\}})? (\d+(?:\.\d+)?)$")
    for line in body.splitlines():
        match = pattern.match(line)
        if match:
            total += float(match.group(1))
    return total


def test_metrics_endpoint_returns_prometheus_text():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    body = response.text
    assert "boundary_layer_lab_runs_total" in body
    assert "boundary_layer_inference_circuit_breaker_state" in body


def test_required_metric_names_present():
    body = _metrics_text()
    required = [
        "boundary_layer_lab_runs_total",
        "boundary_layer_tool_injection_blocked_total",
        "boundary_layer_redis_tamper_rejected_total",
        "boundary_layer_authz_denied_total",
        "boundary_layer_file_injection_blocked_total",
        "boundary_layer_prompt_deletion_orphan_records_total",
        "boundary_layer_governance_deletion_audits_total",
        "boundary_layer_postgres_write_storm_events_total",
        "boundary_layer_postgres_write_storm_blocked_writes_total",
        "boundary_layer_postgres_write_storm_insert_duration_seconds",
        "boundary_layer_inference_circuit_breaker_state",
        "boundary_layer_inference_requests_total",
        "boundary_layer_inference_shed_work_units_total",
        "boundary_layer_inference_simulated_failures_total",
        "boundary_layer_inference_simulated_queue_depth",
        "boundary_layer_inference_simulated_p99_latency_ms",
        "boundary_layer_sse_streams_total",
        "boundary_layer_sse_rejected_streams_total",
        "boundary_layer_sse_active_streams",
        "boundary_layer_sse_orphaned_streams",
        "boundary_layer_sse_worker_pressure",
        "boundary_layer_sse_memory_pressure_mb",
        "boundary_layer_sse_cleanup_applied_total",
        "boundary_layer_prompt_cache_requests_total",
        "boundary_layer_prompt_cache_hits_total",
        "boundary_layer_prompt_cache_cross_tenant_bleed_total",
        "boundary_layer_prompt_cache_isolation_applied_total",
        "boundary_layer_file_upload_extractions_total",
        "boundary_layer_file_upload_sandbox_applied_total",
        "boundary_layer_file_upload_egress_blocked_total",
        "boundary_layer_file_upload_active_content_blocked_total",
        "boundary_layer_file_upload_hidden_instruction_detected_total",
        "boundary_layer_file_upload_untrusted_content_wrapped_total",
    ]
    for metric in required:
        assert metric in body


def test_lab_run_increments_lab_runs_total():
    before = _counter_total(_metrics_text(), "boundary_layer_lab_runs_total")
    response = client.post("/labs/redis/run", json={"mode": "vulnerable"})
    assert response.status_code == 200
    after = _counter_total(_metrics_text(), "boundary_layer_lab_runs_total")
    assert after == before + 1


def test_hardened_tool_router_increments_tool_injection_blocked():
    before = _counter_total(
        _metrics_text(), "boundary_layer_tool_injection_blocked_total"
    )
    response = client.post("/labs/tool-router/run", json={"mode": "hardened"})
    assert response.status_code == 200
    assert response.json()["blocked"] is True
    after = _counter_total(
        _metrics_text(), "boundary_layer_tool_injection_blocked_total"
    )
    assert after == before + 1


def test_hardened_redis_increments_redis_tamper_rejected():
    before = _counter_total(
        _metrics_text(), "boundary_layer_redis_tamper_rejected_total"
    )
    response = client.post("/labs/redis/run", json={"mode": "hardened"})
    assert response.status_code == 200
    assert response.json()["blocked"] is True
    after = _counter_total(
        _metrics_text(), "boundary_layer_redis_tamper_rejected_total"
    )
    assert after == before + 1


def test_hardened_authz_increments_authz_denied():
    before = _counter_total(_metrics_text(), "boundary_layer_authz_denied_total")
    response = client.post("/labs/authz/run", json={"mode": "hardened"})
    assert response.status_code == 200
    assert response.json()["blocked"] is True
    after = _counter_total(_metrics_text(), "boundary_layer_authz_denied_total")
    assert after == before + 1


def test_hardened_file_upload_increments_file_injection_blocked():
    before = _counter_total(
        _metrics_text(), "boundary_layer_file_injection_blocked_total"
    )
    response = client.post("/labs/file-upload/run", json={"mode": "hardened"})
    assert response.status_code == 200
    assert response.json()["blocked"] is True
    after = _counter_total(
        _metrics_text(), "boundary_layer_file_injection_blocked_total"
    )
    assert after == before + 1


def test_governance_vulnerable_increments_orphan_records():
    before = _counter_total(
        _metrics_text(), "boundary_layer_prompt_deletion_orphan_records_total"
    )
    response = client.post("/labs/governance/run", json={"mode": "vulnerable"})
    assert response.status_code == 200
    assert response.json()["blocked"] is False
    after = _counter_total(
        _metrics_text(), "boundary_layer_prompt_deletion_orphan_records_total"
    )
    delta = after - before
    assert delta == 7


def test_invalid_mode_does_not_increment_lab_runs():
    before = _counter_total(_metrics_text(), "boundary_layer_lab_runs_total")
    response = client.post("/labs/redis/run", json={"mode": "invalid"})
    assert response.status_code == 422
    after = _counter_total(_metrics_text(), "boundary_layer_lab_runs_total")
    assert after == before


def test_governance_hardened_increments_audit_metric():
    before_body = _metrics_text()
    response = client.post("/labs/governance/run", json={"mode": "hardened"})
    assert response.status_code == 200
    after_body = _metrics_text()
    assert "boundary_layer_governance_deletion_audits_total" in after_body
    before_audit = _counter_total(
        before_body, "boundary_layer_governance_deletion_audits_total"
    )
    after_audit = _counter_total(
        after_body, "boundary_layer_governance_deletion_audits_total"
    )
    assert after_audit >= before_audit + 1


def test_write_storm_vulnerable_increments_events_metric():
    before = _counter_total(
        _metrics_text(), "boundary_layer_postgres_write_storm_events_total"
    )
    response = client.post(
        "/labs/postgres-write-storm/run",
        json={"mode": "vulnerable", "requested_writes": 5},
    )
    assert response.status_code == 200
    after = _counter_total(
        _metrics_text(), "boundary_layer_postgres_write_storm_events_total"
    )
    assert after == before + 5


def test_write_storm_hardened_increments_blocked_writes_metric():
    before = _counter_total(
        _metrics_text(), "boundary_layer_postgres_write_storm_blocked_writes_total"
    )
    response = client.post(
        "/labs/postgres-write-storm/run",
        json={"mode": "hardened", "requested_writes": 250},
    )
    assert response.status_code == 200
    assert response.json()["blocked"] is True
    after = _counter_total(
        _metrics_text(), "boundary_layer_postgres_write_storm_blocked_writes_total"
    )
    assert after == before + 200


def test_write_storm_metrics_include_histogram():
    client.post(
        "/labs/postgres-write-storm/run",
        json={"mode": "vulnerable", "requested_writes": 3},
    )
    body = _metrics_text()
    assert "boundary_layer_postgres_write_storm_insert_duration_seconds" in body


def _gauge_value(body: str, name: str) -> float | None:
    pattern = re.compile(rf"^{re.escape(name)}(?:\{{[^}}]*\}})? (\d+(?:\.\d+)?)$")
    for line in body.splitlines():
        match = pattern.match(line)
        if match:
            return float(match.group(1))
    return None


def test_circuit_breaker_hardened_sets_open_state_metric():
    response = client.post(
        "/labs/circuit-breaker/run",
        json={"mode": "hardened", "requested_work_units": 250},
    )
    assert response.status_code == 200
    body = _metrics_text()
    assert _gauge_value(body, "boundary_layer_inference_circuit_breaker_state") == 1.0


def test_circuit_breaker_hardened_within_capacity_keeps_closed_state():
    response = client.post(
        "/labs/circuit-breaker/run",
        json={"mode": "hardened", "requested_work_units": 50},
    )
    assert response.status_code == 200
    assert response.json()["blocked"] is False
    body = _metrics_text()
    assert _gauge_value(body, "boundary_layer_inference_circuit_breaker_state") == 0.0


def test_circuit_breaker_hardened_increments_shed_work_units():
    before = _counter_total(
        _metrics_text(), "boundary_layer_inference_shed_work_units_total"
    )
    response = client.post(
        "/labs/circuit-breaker/run",
        json={"mode": "hardened", "requested_work_units": 250},
    )
    assert response.status_code == 200
    after = _counter_total(
        _metrics_text(), "boundary_layer_inference_shed_work_units_total"
    )
    assert after == before + 150


def test_circuit_breaker_sets_queue_depth_and_latency_gauges():
    client.post(
        "/labs/circuit-breaker/run",
        json={"mode": "vulnerable", "requested_work_units": 25},
    )
    body = _metrics_text()
    assert "boundary_layer_inference_simulated_queue_depth" in body
    assert "boundary_layer_inference_simulated_p99_latency_ms" in body
    assert _gauge_value(body, "boundary_layer_inference_simulated_queue_depth") == 25.0


def test_circuit_breaker_vulnerable_increments_simulated_failures():
    before = _counter_total(
        _metrics_text(), "boundary_layer_inference_simulated_failures_total"
    )
    response = client.post(
        "/labs/circuit-breaker/run",
        json={"mode": "vulnerable", "requested_work_units": 250},
    )
    assert response.status_code == 200
    after = _counter_total(
        _metrics_text(), "boundary_layer_inference_simulated_failures_total"
    )
    assert after == before + 50


def test_sse_vulnerable_sets_active_and_orphaned_streams():
    client.post(
        "/labs/sse-exhaustion/run",
        json={"mode": "vulnerable", "requested_streams": 250},
    )
    body = _metrics_text()
    assert _gauge_value(body, "boundary_layer_sse_active_streams") == 250.0
    assert _gauge_value(body, "boundary_layer_sse_orphaned_streams") == 200.0


def test_sse_hardened_increments_rejected_streams():
    before = _counter_total(
        _metrics_text(), "boundary_layer_sse_rejected_streams_total"
    )
    response = client.post(
        "/labs/sse-exhaustion/run",
        json={"mode": "hardened", "requested_streams": 250},
    )
    assert response.status_code == 200
    after = _counter_total(_metrics_text(), "boundary_layer_sse_rejected_streams_total")
    assert after == before + 200


def test_sse_hardened_increments_cleanup_metric():
    before = _counter_total(_metrics_text(), "boundary_layer_sse_cleanup_applied_total")
    response = client.post(
        "/labs/sse-exhaustion/run",
        json={"mode": "hardened", "requested_streams": 250},
    )
    assert response.status_code == 200
    after = _counter_total(_metrics_text(), "boundary_layer_sse_cleanup_applied_total")
    assert after == before + 1


def test_sse_streams_total_increments_on_accept():
    before = _counter_total(_metrics_text(), "boundary_layer_sse_streams_total")
    client.post(
        "/labs/sse-exhaustion/run",
        json={"mode": "vulnerable", "requested_streams": 5},
    )
    after = _counter_total(_metrics_text(), "boundary_layer_sse_streams_total")
    assert after == before + 10


def test_sse_sets_worker_and_memory_pressure_gauges():
    client.post(
        "/labs/sse-exhaustion/run",
        json={
            "mode": "vulnerable",
            "requested_streams": 60,
            "stream_duration_seconds": 120,
        },
    )
    body = _metrics_text()
    assert _gauge_value(body, "boundary_layer_sse_worker_pressure") == 60.0
    assert _gauge_value(body, "boundary_layer_sse_memory_pressure_mb") == 120.0


def test_prompt_cache_vulnerable_increments_cross_tenant_bleed():
    before = _counter_total(
        _metrics_text(), "boundary_layer_prompt_cache_cross_tenant_bleed_total"
    )
    response = client.post(
        "/labs/prompt-cache-isolation/run",
        json={"mode": "vulnerable"},
    )
    assert response.status_code == 200
    after = _counter_total(
        _metrics_text(), "boundary_layer_prompt_cache_cross_tenant_bleed_total"
    )
    assert after == before + 1


def test_prompt_cache_hardened_increments_isolation_applied():
    before = _counter_total(
        _metrics_text(), "boundary_layer_prompt_cache_isolation_applied_total"
    )
    response = client.post(
        "/labs/prompt-cache-isolation/run",
        json={"mode": "hardened"},
    )
    assert response.status_code == 200
    after = _counter_total(
        _metrics_text(), "boundary_layer_prompt_cache_isolation_applied_total"
    )
    assert after == before + 1


def test_prompt_cache_increments_requests_and_hits():
    before_requests = _counter_total(
        _metrics_text(), "boundary_layer_prompt_cache_requests_total"
    )
    before_hits = _counter_total(
        _metrics_text(), "boundary_layer_prompt_cache_hits_total"
    )
    response = client.post(
        "/labs/prompt-cache-isolation/run",
        json={"mode": "vulnerable"},
    )
    assert response.status_code == 200
    after_requests = _counter_total(
        _metrics_text(), "boundary_layer_prompt_cache_requests_total"
    )
    after_hits = _counter_total(
        _metrics_text(), "boundary_layer_prompt_cache_hits_total"
    )
    assert after_requests == before_requests + 2
    assert after_hits == before_hits + 1


def test_file_upload_hardened_increments_sandbox_metrics():
    before_sandbox = _counter_total(
        _metrics_text(), "boundary_layer_file_upload_sandbox_applied_total"
    )
    before_egress = _counter_total(
        _metrics_text(), "boundary_layer_file_upload_egress_blocked_total"
    )
    before_active = _counter_total(
        _metrics_text(), "boundary_layer_file_upload_active_content_blocked_total"
    )
    before_hidden = _counter_total(
        _metrics_text(), "boundary_layer_file_upload_hidden_instruction_detected_total"
    )
    before_wrapped = _counter_total(
        _metrics_text(), "boundary_layer_file_upload_untrusted_content_wrapped_total"
    )
    response = client.post("/labs/file-upload/run", json={"mode": "hardened"})
    assert response.status_code == 200
    after_sandbox = _counter_total(
        _metrics_text(), "boundary_layer_file_upload_sandbox_applied_total"
    )
    after_egress = _counter_total(
        _metrics_text(), "boundary_layer_file_upload_egress_blocked_total"
    )
    after_active = _counter_total(
        _metrics_text(), "boundary_layer_file_upload_active_content_blocked_total"
    )
    after_hidden = _counter_total(
        _metrics_text(), "boundary_layer_file_upload_hidden_instruction_detected_total"
    )
    after_wrapped = _counter_total(
        _metrics_text(), "boundary_layer_file_upload_untrusted_content_wrapped_total"
    )
    assert after_sandbox == before_sandbox + 1
    assert after_egress == before_egress + 1
    assert after_active == before_active + 1
    assert after_hidden == before_hidden + 1
    assert after_wrapped == before_wrapped + 1


def test_file_upload_vulnerable_increments_unsafe_extraction_metric():
    before = _counter_total(
        _metrics_text(), "boundary_layer_file_upload_extractions_total"
    )
    response = client.post("/labs/file-upload/run", json={"mode": "vulnerable"})
    assert response.status_code == 200
    after = _counter_total(
        _metrics_text(), "boundary_layer_file_upload_extractions_total"
    )
    assert after == before + 1


@pytest.fixture(autouse=True)
def postgres_fallback_env(monkeypatch):
    monkeypatch.setenv("BOUNDARY_LAYER_POSTGRES_LIVE", "false")


@pytest.fixture(autouse=True)
def redis_fallback_env(monkeypatch):
    monkeypatch.setenv("BOUNDARY_LAYER_REDIS_LIVE", "false")
