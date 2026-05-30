"""BoundaryLayer API - Open LLM Infrastructure Security Lab."""

from fastapi import FastAPI, HTTPException, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel, Field

from apps.api.metrics import (
    observe_postgres_write_storm_insert_duration,
    record_authz_denied,
    record_file_injection_blocked,
    record_file_upload_active_content_blocked,
    record_file_upload_egress_blocked,
    record_file_upload_extraction,
    record_file_upload_hidden_instruction_detected,
    record_file_upload_sandbox_applied,
    record_file_upload_untrusted_content_wrapped,
    record_governance_deletion_audit,
    record_inference_requests,
    record_inference_shed_work_units,
    record_inference_simulated_failures,
    record_lab_run,
    record_postgres_write_storm_blocked_writes,
    record_postgres_write_storm_events,
    record_prompt_cache_cross_tenant_bleed,
    record_prompt_cache_hit,
    record_prompt_cache_isolation_applied,
    record_prompt_cache_request,
    record_prompt_deletion_orphans,
    record_redis_tamper_rejected,
    record_sse_cleanup_applied,
    record_sse_rejected_streams,
    record_sse_streams,
    record_tool_injection_blocked,
    set_circuit_breaker_state,
    set_inference_p99_latency_ms,
    set_inference_queue_depth,
    set_sse_active_streams,
    set_sse_memory_pressure_mb,
    set_sse_orphaned_streams,
    set_sse_worker_pressure,
)
from labs.authz import run_authz_lab
from labs.circuit_breaker import (
    DEFAULT_REQUESTED_WORK_UNITS,
    MAX_REQUESTED_WORK_UNITS,
    MIN_REQUESTED_WORK_UNITS,
    run_circuit_breaker_lab,
)
from labs.file_upload import (
    ALLOWED_FILE_TYPES,
    DEFAULT_FILE_TYPE,
    run_file_upload_lab,
)
from labs.governance import run_governance_lab
from labs.postgres_write_storm import (
    DEFAULT_REQUESTED_WRITES,
    MAX_REQUESTED_WRITES,
    MIN_REQUESTED_WRITES,
    run_postgres_write_storm_lab,
)
from labs.prompt_cache_isolation import (
    DEFAULT_PROMPT_PREFIX,
    DEFAULT_TENANT_A,
    DEFAULT_TENANT_B,
    MAX_PREFIX_LEN,
    MAX_TENANT_LEN,
    run_prompt_cache_isolation_lab,
)
from labs.redis_state import run_redis_lab
from labs.sse_exhaustion import (
    DEFAULT_REQUESTED_STREAMS,
    DEFAULT_STREAM_DURATION_SECONDS,
    MAX_REQUESTED_STREAMS,
    MAX_STREAM_DURATION_SECONDS,
    MIN_REQUESTED_STREAMS,
    MIN_STREAM_DURATION_SECONDS,
    run_sse_exhaustion_lab,
)
from labs.tool_router import run_tool_router_lab

app = FastAPI(
    title="BoundaryLayer API",
    description="Open LLM Infrastructure Security Lab",
    version="1.0.6",
)

LABS = [
    {
        "id": "tool-router",
        "name": "Tool Router Injection Lab",
        "path": "/labs/tool-router/run",
        "description": "Poisoned retrieved content influences simulated tool requests.",
    },
    {
        "id": "redis",
        "name": "Redis State Tampering Lab",
        "path": "/labs/redis/run",
        "description": "Predictable or unsigned session values can be modified.",
    },
    {
        "id": "authz",
        "name": "Flat AuthN/AuthZ Lab",
        "path": "/labs/authz/run",
        "description": "Broad tokens access restricted tools without scope checks.",
    },
    {
        "id": "file-upload",
        "name": "File Upload Injection Lab",
        "path": "/labs/file-upload/run",
        "description": (
            "Unsafe extraction versus sandboxed extraction with content wrapping."
        ),
    },
    {
        "id": "governance",
        "name": "Prompt Governance Tracker",
        "path": "/labs/governance/run",
        "description": "Incomplete prompt deletion leaves downstream records.",
    },
    {
        "id": "postgres-write-storm",
        "name": "PostgreSQL Write Storm Lab",
        "path": "/labs/postgres-write-storm/run",
        "description": "Runaway prompt logging writes overload the PostgreSQL writer.",
    },
    {
        "id": "circuit-breaker",
        "name": "Circuit Breaker Simulation Lab",
        "path": "/labs/circuit-breaker/run",
        "description": (
            "Unbounded inference work cascades without backpressure controls."
        ),
    },
    {
        "id": "sse-exhaustion",
        "name": "SSE Exhaustion Simulation Lab",
        "path": "/labs/sse-exhaustion/run",
        "description": "Unbounded SSE streams exhaust workers and memory.",
    },
    {
        "id": "prompt-cache-isolation",
        "name": "Prompt Cache Isolation Lab",
        "path": "/labs/prompt-cache-isolation/run",
        "description": (
            "Shared prompt-prefix cache keys can bleed across tenant boundaries."
        ),
    },
]

LAB_RUNNERS = {
    "tool-router": run_tool_router_lab,
    "redis": run_redis_lab,
    "authz": run_authz_lab,
    "file-upload": run_file_upload_lab,
    "governance": run_governance_lab,
    "postgres-write-storm": run_postgres_write_storm_lab,
    "circuit-breaker": run_circuit_breaker_lab,
    "sse-exhaustion": run_sse_exhaustion_lab,
}


class LabRequest(BaseModel):
    mode: str = Field(..., pattern="^(vulnerable|hardened)$")


class FileUploadLabRequest(BaseModel):
    mode: str = Field(..., pattern="^(vulnerable|hardened)$")
    file_type: str = Field(default=DEFAULT_FILE_TYPE)
    contains_hidden_instruction: bool = Field(default=True)
    contains_active_content: bool = Field(default=True)
    egress_attempted: bool = Field(default=True)


class WriteStormLabRequest(BaseModel):
    mode: str = Field(..., pattern="^(vulnerable|hardened)$")
    requested_writes: int = Field(
        default=DEFAULT_REQUESTED_WRITES,
        ge=MIN_REQUESTED_WRITES,
        le=MAX_REQUESTED_WRITES,
    )


class CircuitBreakerLabRequest(BaseModel):
    mode: str = Field(..., pattern="^(vulnerable|hardened)$")
    requested_work_units: int = Field(
        default=DEFAULT_REQUESTED_WORK_UNITS,
        ge=MIN_REQUESTED_WORK_UNITS,
        le=MAX_REQUESTED_WORK_UNITS,
    )


class SseExhaustionLabRequest(BaseModel):
    mode: str = Field(..., pattern="^(vulnerable|hardened)$")
    requested_streams: int = Field(
        default=DEFAULT_REQUESTED_STREAMS,
        ge=MIN_REQUESTED_STREAMS,
        le=MAX_REQUESTED_STREAMS,
    )
    stream_duration_seconds: int = Field(
        default=DEFAULT_STREAM_DURATION_SECONDS,
        ge=MIN_STREAM_DURATION_SECONDS,
        le=MAX_STREAM_DURATION_SECONDS,
    )


class PromptCacheIsolationLabRequest(BaseModel):
    mode: str = Field(..., pattern="^(vulnerable|hardened)$")
    tenant_a: str = Field(
        default=DEFAULT_TENANT_A,
        min_length=1,
        max_length=MAX_TENANT_LEN,
    )
    tenant_b: str = Field(
        default=DEFAULT_TENANT_B,
        min_length=1,
        max_length=MAX_TENANT_LEN,
    )
    prompt_prefix: str = Field(
        default=DEFAULT_PROMPT_PREFIX,
        min_length=1,
        max_length=MAX_PREFIX_LEN,
    )


class LabResponse(BaseModel):
    lab: str
    mode: str
    blocked: bool
    risk: str
    control: str
    events: list[str]
    summary: str


def _record_lab_metrics(lab_id: str, mode: str, result: dict) -> None:
    blocked = result["blocked"]
    record_lab_run(lab_id, mode, blocked)

    if lab_id == "tool-router" and mode == "hardened" and blocked:
        record_tool_injection_blocked()
    elif lab_id == "redis" and mode == "hardened" and blocked:
        record_redis_tamper_rejected()
    elif lab_id == "authz" and mode == "hardened" and blocked:
        record_authz_denied()
    elif lab_id == "file-upload":
        file_type = result.get("_file_type", DEFAULT_FILE_TYPE)
        extraction_result = result.get("_extraction_result")
        if extraction_result:
            record_file_upload_extraction(mode, file_type, extraction_result)
        if result.get("_sandbox_applied"):
            record_file_upload_sandbox_applied(mode)
        if result.get("_egress_blocked"):
            record_file_upload_egress_blocked(mode)
        if result.get("_active_content_blocked"):
            record_file_upload_active_content_blocked(mode, file_type)
        if result.get("_hidden_instruction_detected"):
            record_file_upload_hidden_instruction_detected(mode, file_type)
        if result.get("_content_wrapped"):
            record_file_upload_untrusted_content_wrapped(mode)
        if mode == "hardened" and blocked:
            record_file_injection_blocked()
    elif lab_id == "governance":
        orphan_count = result.get("_orphan_count", 0)
        if orphan_count > 0:
            record_prompt_deletion_orphans(orphan_count)
        if "_audit_complete" in result:
            record_governance_deletion_audit(mode, bool(result["_audit_complete"]))
    elif lab_id == "postgres-write-storm":
        inserted = result.get("_inserted_count", 0)
        insert_result = result.get("_insert_result", "inserted")
        if inserted > 0:
            record_postgres_write_storm_events(mode, insert_result, inserted)
        blocked_writes = result.get("_blocked_writes_count", 0)
        if blocked_writes > 0:
            record_postgres_write_storm_blocked_writes(mode, blocked_writes)
        duration = result.get("_insert_duration_seconds")
        if duration is not None:
            observe_postgres_write_storm_insert_duration(mode, duration)
    elif lab_id == "circuit-breaker":
        requested = result.get("_requested_work_units", 0)
        accepted = result.get("_accepted_work_units", 0)
        if requested > 0:
            record_inference_requests(mode, "requested", requested)
        if accepted > 0:
            record_inference_requests(mode, "accepted", accepted)
        shed = result.get("_shed_work_units", 0)
        if shed > 0:
            record_inference_shed_work_units(mode, shed)
        failures = result.get("_simulated_failures", 0)
        if failures > 0:
            record_inference_simulated_failures(mode, failures)
        queue_depth = result.get("_queue_depth")
        if queue_depth is not None:
            set_inference_queue_depth(mode, queue_depth)
        p99_latency = result.get("_p99_latency_ms")
        if p99_latency is not None:
            set_inference_p99_latency_ms(mode, p99_latency)
        circuit_state = result.get("_circuit_breaker_state")
        if circuit_state is not None:
            set_circuit_breaker_state(int(circuit_state))
    elif lab_id == "sse-exhaustion":
        requested = result.get("_requested_streams", 0)
        accepted = result.get("_accepted_streams", 0)
        if requested > 0:
            record_sse_streams(mode, "requested", requested)
        if accepted > 0:
            record_sse_streams(mode, "accepted", accepted)
        rejected = result.get("_rejected_streams", 0)
        if rejected > 0:
            record_sse_rejected_streams(mode, rejected)
        active = result.get("_active_streams")
        if active is not None:
            set_sse_active_streams(mode, active)
        orphaned = result.get("_orphaned_streams")
        if orphaned is not None:
            set_sse_orphaned_streams(mode, orphaned)
        worker_pressure = result.get("_worker_pressure")
        if worker_pressure is not None:
            set_sse_worker_pressure(mode, worker_pressure)
        memory_pressure = result.get("_memory_pressure_mb")
        if memory_pressure is not None:
            set_sse_memory_pressure_mb(mode, memory_pressure)
        if result.get("_cleanup_applied"):
            record_sse_cleanup_applied(mode)
    elif lab_id == "prompt-cache-isolation":
        tenant_a = result.get("_metrics_tenant_a", DEFAULT_TENANT_A)
        tenant_b = result.get("_metrics_tenant_b", DEFAULT_TENANT_B)
        record_prompt_cache_request(mode, tenant_a, "write")
        record_prompt_cache_request(mode, tenant_b, "lookup")
        hit_type = result.get("_tenant_b_hit_type")
        if hit_type:
            record_prompt_cache_hit(mode, tenant_b, hit_type)
        if result.get("_cache_bleed_detected"):
            record_prompt_cache_cross_tenant_bleed(mode)
        if result.get("_isolation_applied"):
            record_prompt_cache_isolation_applied(mode)


@app.get("/health")
def health():
    return {"status": "ok", "service": "boundary-layer-api", "version": "1.0.6"}


@app.get("/metrics")
def metrics():
    payload = generate_latest()
    return Response(content=payload, media_type=CONTENT_TYPE_LATEST)


@app.get("/labs")
def list_labs():
    return {"labs": LABS}


CIRCUIT_BREAKER_INTERNAL_KEYS = (
    "_circuit_breaker_state",
    "_requested_work_units",
    "_accepted_work_units",
    "_shed_work_units",
    "_simulated_failures",
    "_queue_depth",
    "_p99_latency_ms",
)

SSE_EXHAUSTION_INTERNAL_KEYS = (
    "_requested_streams",
    "_accepted_streams",
    "_rejected_streams",
    "_active_streams",
    "_orphaned_streams",
    "_worker_pressure",
    "_memory_pressure_mb",
    "_cleanup_applied",
)

PROMPT_CACHE_INTERNAL_KEYS = (
    "_metrics_tenant_a",
    "_metrics_tenant_b",
    "_tenant_a_cache_key",
    "_tenant_b_cache_key",
    "_cache_key_mode",
    "_tenant_b_hit_type",
    "_cache_hit_cross_tenant",
    "_cache_bleed_detected",
    "_isolation_applied",
)

FILE_UPLOAD_INTERNAL_KEYS = (
    "_file_type",
    "_extraction_result",
    "_sandbox_applied",
    "_egress_blocked",
    "_active_content_blocked",
    "_hidden_instruction_detected",
    "_content_wrapped",
    "_context_insertion_allowed",
)


def _strip_internal_keys(result: dict, keys: tuple[str, ...]) -> None:
    for internal_key in keys:
        result.pop(internal_key, None)


def _run_lab(lab_id: str, request: LabRequest) -> LabResponse:
    runner = LAB_RUNNERS.get(lab_id)
    if runner is None:
        raise HTTPException(status_code=404, detail=f"Lab not found: {lab_id}")
    try:
        result = runner(request.mode)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    _record_lab_metrics(lab_id, request.mode, result)
    _strip_internal_keys(
        result,
        (
            "_orphan_count",
            "_audit_complete",
            "_inserted_count",
            "_blocked_writes_count",
            "_insert_duration_seconds",
            "_insert_result",
        ),
    )
    return LabResponse(**result)


@app.post("/labs/tool-router/run", response_model=LabResponse)
def run_tool_router(request: LabRequest):
    return _run_lab("tool-router", request)


@app.post("/labs/redis/run", response_model=LabResponse)
def run_redis(request: LabRequest):
    return _run_lab("redis", request)


@app.post("/labs/authz/run", response_model=LabResponse)
def run_authz(request: LabRequest):
    return _run_lab("authz", request)


@app.post("/labs/file-upload/run", response_model=LabResponse)
def run_file_upload(request: FileUploadLabRequest):
    if request.file_type not in ALLOWED_FILE_TYPES:
        allowed = ", ".join(sorted(ALLOWED_FILE_TYPES))
        raise HTTPException(
            status_code=422,
            detail=f"file_type must be one of: {allowed}",
        )
    try:
        result = run_file_upload_lab(
            request.mode,
            request.file_type,
            request.contains_hidden_instruction,
            request.contains_active_content,
            request.egress_attempted,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    _record_lab_metrics("file-upload", request.mode, result)
    _strip_internal_keys(result, FILE_UPLOAD_INTERNAL_KEYS)
    return LabResponse(**result)


@app.post("/labs/governance/run", response_model=LabResponse)
def run_governance(request: LabRequest):
    return _run_lab("governance", request)


@app.post("/labs/postgres-write-storm/run", response_model=LabResponse)
def run_postgres_write_storm(request: WriteStormLabRequest):
    runner = LAB_RUNNERS.get("postgres-write-storm")
    if runner is None:
        raise HTTPException(
            status_code=404,
            detail="Lab not found: postgres-write-storm",
        )
    try:
        result = runner(request.mode, request.requested_writes)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    _record_lab_metrics("postgres-write-storm", request.mode, result)
    _strip_internal_keys(
        result,
        (
            "_inserted_count",
            "_blocked_writes_count",
            "_insert_duration_seconds",
            "_insert_result",
        ),
    )
    return LabResponse(**result)


@app.post("/labs/circuit-breaker/run", response_model=LabResponse)
def run_circuit_breaker(request: CircuitBreakerLabRequest):
    try:
        result = run_circuit_breaker_lab(request.mode, request.requested_work_units)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    _record_lab_metrics("circuit-breaker", request.mode, result)
    _strip_internal_keys(result, CIRCUIT_BREAKER_INTERNAL_KEYS)
    return LabResponse(**result)


@app.post("/labs/sse-exhaustion/run", response_model=LabResponse)
def run_sse_exhaustion(request: SseExhaustionLabRequest):
    try:
        result = run_sse_exhaustion_lab(
            request.mode,
            request.requested_streams,
            request.stream_duration_seconds,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    _record_lab_metrics("sse-exhaustion", request.mode, result)
    _strip_internal_keys(result, SSE_EXHAUSTION_INTERNAL_KEYS)
    return LabResponse(**result)


@app.post("/labs/prompt-cache-isolation/run", response_model=LabResponse)
def run_prompt_cache_isolation(request: PromptCacheIsolationLabRequest):
    try:
        result = run_prompt_cache_isolation_lab(
            request.mode,
            request.tenant_a,
            request.tenant_b,
            request.prompt_prefix,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    _record_lab_metrics("prompt-cache-isolation", request.mode, result)
    _strip_internal_keys(result, PROMPT_CACHE_INTERNAL_KEYS)
    return LabResponse(**result)
