"""Prometheus metrics for BoundaryLayer lab events."""

from prometheus_client import Counter, Gauge, Histogram

LAB_RUNS_TOTAL = Counter(
    "boundary_layer_lab_runs_total",
    "Total BoundaryLayer lab runs",
    ["lab", "mode", "result"],
)

TOOL_INJECTION_BLOCKED_TOTAL = Counter(
    "boundary_layer_tool_injection_blocked_total",
    "Tool router blocks due to injection patterns",
)

REDIS_TAMPER_REJECTED_TOTAL = Counter(
    "boundary_layer_redis_tamper_rejected_total",
    "Redis tamper attempts rejected by HMAC verification",
)

AUTHZ_DENIED_TOTAL = Counter(
    "boundary_layer_authz_denied_total",
    "Authorization denials for restricted tools",
)

FILE_INJECTION_BLOCKED_TOTAL = Counter(
    "boundary_layer_file_injection_blocked_total",
    "File upload injection blocks in hardened mode",
)

FILE_UPLOAD_EXTRACTIONS_TOTAL = Counter(
    "boundary_layer_file_upload_extractions_total",
    "Synthetic file upload extraction outcomes",
    ["mode", "file_type", "result"],
)

FILE_UPLOAD_SANDBOX_APPLIED_TOTAL = Counter(
    "boundary_layer_file_upload_sandbox_applied_total",
    "File upload sandbox policy applied in hardened mode",
    ["mode"],
)

FILE_UPLOAD_EGRESS_BLOCKED_TOTAL = Counter(
    "boundary_layer_file_upload_egress_blocked_total",
    "Simulated file upload egress attempts blocked in hardened mode",
    ["mode"],
)

FILE_UPLOAD_ACTIVE_CONTENT_BLOCKED_TOTAL = Counter(
    "boundary_layer_file_upload_active_content_blocked_total",
    "Simulated active file content blocked in hardened mode",
    ["mode", "file_type"],
)

FILE_UPLOAD_HIDDEN_INSTRUCTION_DETECTED_TOTAL = Counter(
    "boundary_layer_file_upload_hidden_instruction_detected_total",
    "Hidden instruction-like content detected in hardened file upload mode",
    ["mode", "file_type"],
)

FILE_UPLOAD_UNTRUSTED_CONTENT_WRAPPED_TOTAL = Counter(
    "boundary_layer_file_upload_untrusted_content_wrapped_total",
    "Extracted file content wrapped as untrusted data in hardened mode",
    ["mode"],
)

PROMPT_DELETION_ORPHAN_RECORDS_TOTAL = Counter(
    "boundary_layer_prompt_deletion_orphan_records_total",
    "Orphaned downstream records detected during governance checks",
)

GOVERNANCE_DELETION_AUDITS_TOTAL = Counter(
    "boundary_layer_governance_deletion_audits_total",
    "Governance deletion audit records written",
    ["mode", "complete"],
)

POSTGRES_WRITE_STORM_EVENTS_TOTAL = Counter(
    "boundary_layer_postgres_write_storm_events_total",
    "Synthetic PostgreSQL write storm events inserted",
    ["mode", "result"],
)

POSTGRES_WRITE_STORM_BLOCKED_WRITES_TOTAL = Counter(
    "boundary_layer_postgres_write_storm_blocked_writes_total",
    "Synthetic PostgreSQL write storm events blocked by budget",
    ["mode"],
)

POSTGRES_WRITE_STORM_INSERT_DURATION_SECONDS = Histogram(
    "boundary_layer_postgres_write_storm_insert_duration_seconds",
    "Duration of synthetic write storm insert batches",
    ["mode"],
)

INFERENCE_CIRCUIT_BREAKER_STATE = Gauge(
    "boundary_layer_inference_circuit_breaker_state",
    "Inference circuit breaker state (0=closed, 1=open)",
)

INFERENCE_REQUESTS_TOTAL = Counter(
    "boundary_layer_inference_requests_total",
    "Synthetic inference work units requested or accepted",
    ["mode", "result"],
)

INFERENCE_SHED_WORK_UNITS_TOTAL = Counter(
    "boundary_layer_inference_shed_work_units_total",
    "Synthetic inference work units shed by circuit breaker",
    ["mode"],
)

INFERENCE_SIMULATED_FAILURES_TOTAL = Counter(
    "boundary_layer_inference_simulated_failures_total",
    "Deterministic simulated inference failures",
    ["mode"],
)

INFERENCE_SIMULATED_QUEUE_DEPTH = Gauge(
    "boundary_layer_inference_simulated_queue_depth",
    "Simulated inference queue depth",
    ["mode"],
)

INFERENCE_SIMULATED_P99_LATENCY_MS = Gauge(
    "boundary_layer_inference_simulated_p99_latency_ms",
    "Simulated inference p99 latency in milliseconds",
    ["mode"],
)

SSE_STREAMS_TOTAL = Counter(
    "boundary_layer_sse_streams_total",
    "Synthetic SSE streams requested or accepted",
    ["mode", "result"],
)

SSE_REJECTED_STREAMS_TOTAL = Counter(
    "boundary_layer_sse_rejected_streams_total",
    "Synthetic SSE streams rejected by tenant cap",
    ["mode"],
)

SSE_ACTIVE_STREAMS = Gauge(
    "boundary_layer_sse_active_streams",
    "Simulated active SSE streams",
    ["mode"],
)

SSE_ORPHANED_STREAMS = Gauge(
    "boundary_layer_sse_orphaned_streams",
    "Simulated orphaned SSE streams",
    ["mode"],
)

SSE_WORKER_PRESSURE = Gauge(
    "boundary_layer_sse_worker_pressure",
    "Simulated SSE worker pressure",
    ["mode"],
)

SSE_MEMORY_PRESSURE_MB = Gauge(
    "boundary_layer_sse_memory_pressure_mb",
    "Simulated SSE memory pressure in megabytes",
    ["mode"],
)

SSE_CLEANUP_APPLIED_TOTAL = Counter(
    "boundary_layer_sse_cleanup_applied_total",
    "SSE cleanup controls applied in hardened mode",
    ["mode"],
)

PROMPT_CACHE_REQUESTS_TOTAL = Counter(
    "boundary_layer_prompt_cache_requests_total",
    "Synthetic prompt cache write and lookup operations",
    ["mode", "tenant", "result"],
)

PROMPT_CACHE_HITS_TOTAL = Counter(
    "boundary_layer_prompt_cache_hits_total",
    "Synthetic prompt cache hit outcomes",
    ["mode", "tenant", "hit_type"],
)

PROMPT_CACHE_CROSS_TENANT_BLEED_TOTAL = Counter(
    "boundary_layer_prompt_cache_cross_tenant_bleed_total",
    "Cross-tenant prompt cache bleed detections in vulnerable mode",
    ["mode"],
)

PROMPT_CACHE_ISOLATION_APPLIED_TOTAL = Counter(
    "boundary_layer_prompt_cache_isolation_applied_total",
    "Tenant-scoped prompt cache isolation applied in hardened mode",
    ["mode"],
)

INFERENCE_CIRCUIT_BREAKER_STATE.set(0)


def record_lab_run(lab: str, mode: str, blocked: bool) -> None:
    result = "blocked" if blocked else "allowed"
    LAB_RUNS_TOTAL.labels(lab=lab, mode=mode, result=result).inc()


def record_tool_injection_blocked() -> None:
    TOOL_INJECTION_BLOCKED_TOTAL.inc()


def record_redis_tamper_rejected() -> None:
    REDIS_TAMPER_REJECTED_TOTAL.inc()


def record_authz_denied() -> None:
    AUTHZ_DENIED_TOTAL.inc()


def record_file_injection_blocked() -> None:
    FILE_INJECTION_BLOCKED_TOTAL.inc()


def record_file_upload_extraction(mode: str, file_type: str, result: str) -> None:
    FILE_UPLOAD_EXTRACTIONS_TOTAL.labels(
        mode=mode,
        file_type=file_type,
        result=result,
    ).inc()


def record_file_upload_sandbox_applied(mode: str) -> None:
    FILE_UPLOAD_SANDBOX_APPLIED_TOTAL.labels(mode=mode).inc()


def record_file_upload_egress_blocked(mode: str) -> None:
    FILE_UPLOAD_EGRESS_BLOCKED_TOTAL.labels(mode=mode).inc()


def record_file_upload_active_content_blocked(mode: str, file_type: str) -> None:
    FILE_UPLOAD_ACTIVE_CONTENT_BLOCKED_TOTAL.labels(
        mode=mode,
        file_type=file_type,
    ).inc()


def record_file_upload_hidden_instruction_detected(mode: str, file_type: str) -> None:
    FILE_UPLOAD_HIDDEN_INSTRUCTION_DETECTED_TOTAL.labels(
        mode=mode,
        file_type=file_type,
    ).inc()


def record_file_upload_untrusted_content_wrapped(mode: str) -> None:
    FILE_UPLOAD_UNTRUSTED_CONTENT_WRAPPED_TOTAL.labels(mode=mode).inc()


def record_prompt_deletion_orphans(count: int) -> None:
    if count > 0:
        PROMPT_DELETION_ORPHAN_RECORDS_TOTAL.inc(count)


def record_governance_deletion_audit(mode: str, complete: bool) -> None:
    GOVERNANCE_DELETION_AUDITS_TOTAL.labels(
        mode=mode,
        complete=str(complete).lower(),
    ).inc()


def record_postgres_write_storm_events(mode: str, result: str, count: int) -> None:
    if count > 0:
        POSTGRES_WRITE_STORM_EVENTS_TOTAL.labels(mode=mode, result=result).inc(count)


def record_postgres_write_storm_blocked_writes(mode: str, count: int) -> None:
    if count > 0:
        POSTGRES_WRITE_STORM_BLOCKED_WRITES_TOTAL.labels(mode=mode).inc(count)


def observe_postgres_write_storm_insert_duration(mode: str, seconds: float) -> None:
    POSTGRES_WRITE_STORM_INSERT_DURATION_SECONDS.labels(mode=mode).observe(seconds)


def set_circuit_breaker_state(value: int) -> None:
    INFERENCE_CIRCUIT_BREAKER_STATE.set(value)


def record_inference_requests(mode: str, result: str, count: int) -> None:
    if count > 0:
        INFERENCE_REQUESTS_TOTAL.labels(mode=mode, result=result).inc(count)


def record_inference_shed_work_units(mode: str, count: int) -> None:
    if count > 0:
        INFERENCE_SHED_WORK_UNITS_TOTAL.labels(mode=mode).inc(count)


def record_inference_simulated_failures(mode: str, count: int) -> None:
    if count > 0:
        INFERENCE_SIMULATED_FAILURES_TOTAL.labels(mode=mode).inc(count)


def set_inference_queue_depth(mode: str, value: int) -> None:
    INFERENCE_SIMULATED_QUEUE_DEPTH.labels(mode=mode).set(value)


def set_inference_p99_latency_ms(mode: str, value: int) -> None:
    INFERENCE_SIMULATED_P99_LATENCY_MS.labels(mode=mode).set(value)


def record_sse_streams(mode: str, result: str, count: int) -> None:
    if count > 0:
        SSE_STREAMS_TOTAL.labels(mode=mode, result=result).inc(count)


def record_sse_rejected_streams(mode: str, count: int) -> None:
    if count > 0:
        SSE_REJECTED_STREAMS_TOTAL.labels(mode=mode).inc(count)


def set_sse_active_streams(mode: str, value: int) -> None:
    SSE_ACTIVE_STREAMS.labels(mode=mode).set(value)


def set_sse_orphaned_streams(mode: str, value: int) -> None:
    SSE_ORPHANED_STREAMS.labels(mode=mode).set(value)


def set_sse_worker_pressure(mode: str, value: int) -> None:
    SSE_WORKER_PRESSURE.labels(mode=mode).set(value)


def set_sse_memory_pressure_mb(mode: str, value: int) -> None:
    SSE_MEMORY_PRESSURE_MB.labels(mode=mode).set(value)


def record_sse_cleanup_applied(mode: str) -> None:
    SSE_CLEANUP_APPLIED_TOTAL.labels(mode=mode).inc()


def record_prompt_cache_request(mode: str, tenant: str, result: str) -> None:
    PROMPT_CACHE_REQUESTS_TOTAL.labels(
        mode=mode,
        tenant=tenant,
        result=result,
    ).inc()


def record_prompt_cache_hit(mode: str, tenant: str, hit_type: str) -> None:
    PROMPT_CACHE_HITS_TOTAL.labels(
        mode=mode,
        tenant=tenant,
        hit_type=hit_type,
    ).inc()


def record_prompt_cache_cross_tenant_bleed(mode: str) -> None:
    PROMPT_CACHE_CROSS_TENANT_BLEED_TOTAL.labels(mode=mode).inc()


def record_prompt_cache_isolation_applied(mode: str) -> None:
    PROMPT_CACHE_ISOLATION_APPLIED_TOTAL.labels(mode=mode).inc()
