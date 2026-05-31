# Architecture

BoundaryLayer is a local Docker Compose stack that simulates LLM application infrastructure failures. The API exposes nine security labs, each runnable in vulnerable or hardened mode, plus a Prometheus `/metrics` endpoint.

The **mock LLM service** (`mock-llm:8080`) is a deterministic companion for demos and integration tests. Lab runners simulate tool routing, authz, and retrieval behavior **in-process** today; they do not call the mock LLM HTTP API during normal lab runs. See [docs/DEMO.md](DEMO.md) for direct mock LLM examples.

For Mermaid diagrams of the system, Docker topology, lab flows, trust boundaries, observability pipeline, per-lab control paths, and CI validation, see [DIAGRAMS.md](DIAGRAMS.md).

For live Docker verification steps, see [E2E_VALIDATION.md](E2E_VALIDATION.md).

## System Overview

## Service Map

| Service | Port | Role |
|---------|------|------|
| api | 8000 | FastAPI lab orchestrator and `/metrics` exporter |
| mock-llm | 8080 | Deterministic model and tool-plan simulator |
| redis | 6379 | Live session state target for Redis lab (v0.2) |
| postgres | 5432 | Live PostgreSQL backend for governance and write storm labs |
| prometheus | 9090 | Scrapes API metrics, evaluates alert rules, sends alerts to Alertmanager |
| alertmanager | 9093 | Routes firing alerts to local webhook receiver |
| alert-webhook | 8081 | Stores Alertmanager webhook payloads in memory for local validation |

## Metrics

`GET /metrics` returns Prometheus text exposition format.

| Metric | Type | Purpose |
|--------|------|---------|
| `boundary_layer_lab_runs_total` | Counter | Lab runs by `lab`, `mode`, `result` |
| `boundary_layer_tool_injection_blocked_total` | Counter | Hardened tool-router blocks |
| `boundary_layer_redis_tamper_rejected_total` | Counter | Hardened Redis tamper rejections |
| `boundary_layer_authz_denied_total` | Counter | Hardened authz denials |
| `boundary_layer_file_injection_blocked_total` | Counter | Hardened file-upload blocks |
| `boundary_layer_file_upload_extractions_total` | Counter | Synthetic file extractions by `mode`, `file_type`, `result` |
| `boundary_layer_file_upload_sandbox_applied_total` | Counter | Sandbox policy applied in hardened file upload mode |
| `boundary_layer_file_upload_egress_blocked_total` | Counter | Simulated egress blocked in hardened file upload mode |
| `boundary_layer_file_upload_active_content_blocked_total` | Counter | Active content blocked by `mode`, `file_type` |
| `boundary_layer_file_upload_hidden_instruction_detected_total` | Counter | Hidden instruction detected by `mode`, `file_type` |
| `boundary_layer_file_upload_untrusted_content_wrapped_total` | Counter | Extracted content wrapped as untrusted data |
| `boundary_layer_prompt_deletion_orphan_records_total` | Counter | Governance orphan detections |
| `boundary_layer_governance_deletion_audits_total` | Counter | Governance deletion audit rows by `mode`, `complete` |
| `boundary_layer_postgres_write_storm_events_total` | Counter | Synthetic write storm inserts by `mode`, `result` |
| `boundary_layer_postgres_write_storm_blocked_writes_total` | Counter | Blocked excess writes in hardened write storm mode |
| `boundary_layer_postgres_write_storm_insert_duration_seconds` | Histogram | Write storm batch insert duration by `mode` |
| `boundary_layer_inference_circuit_breaker_state` | Gauge | Circuit breaker state (0=closed, 1=open), lab-driven |
| `boundary_layer_inference_requests_total` | Counter | Synthetic inference work by `mode`, `result` |
| `boundary_layer_inference_shed_work_units_total` | Counter | Shed work units in hardened circuit breaker mode |
| `boundary_layer_inference_simulated_failures_total` | Counter | Deterministic simulated failures in vulnerable mode |
| `boundary_layer_inference_simulated_queue_depth` | Gauge | Simulated inference queue depth by `mode` |
| `boundary_layer_inference_simulated_p99_latency_ms` | Gauge | Simulated p99 latency by `mode` |
| `boundary_layer_sse_streams_total` | Counter | Synthetic SSE streams by `mode`, `result` |
| `boundary_layer_sse_rejected_streams_total` | Counter | Rejected SSE streams in hardened mode |
| `boundary_layer_sse_active_streams` | Gauge | Simulated active SSE streams by `mode` |
| `boundary_layer_sse_orphaned_streams` | Gauge | Simulated orphaned SSE streams by `mode` |
| `boundary_layer_sse_worker_pressure` | Gauge | Simulated SSE worker pressure by `mode` |
| `boundary_layer_sse_memory_pressure_mb` | Gauge | Simulated SSE memory pressure by `mode` |
| `boundary_layer_sse_cleanup_applied_total` | Counter | SSE cleanup applied in hardened mode |
| `boundary_layer_prompt_cache_requests_total` | Counter | Synthetic prompt cache writes and lookups by `mode`, `tenant`, `result` |
| `boundary_layer_prompt_cache_hits_total` | Counter | Prompt cache hit outcomes by `mode`, `tenant`, `hit_type` |
| `boundary_layer_prompt_cache_cross_tenant_bleed_total` | Counter | Cross-tenant cache bleed detections in vulnerable mode |
| `boundary_layer_prompt_cache_isolation_applied_total` | Counter | Tenant-scoped cache isolation applied in hardened mode |

## Redis Live Mode

The Redis State Tampering Lab uses live Redis when `BOUNDARY_LAYER_REDIS_LIVE=true` (default in Docker Compose).

- Keys use namespace `boundary_layer:lab:redis:`
- TTLs are applied to lab keys
- Vulnerable mode stores unsigned payloads and accepts tampering
- Hardened mode stores HMAC-signed payloads and rejects tampering

Outside Docker, set `BOUNDARY_LAYER_REDIS_LIVE=false` for deterministic in-memory fallback used by unit tests.

Prometheus scrape config targets `api:8000/metrics` every 15 seconds.

## PostgreSQL Live Governance Mode

When `BOUNDARY_LAYER_POSTGRES_LIVE=true`, the governance lab initializes schema, writes lifecycle records, detects orphans via SQL joins, and inserts audit rows. Fallback mode preserves deterministic in-memory behavior for tests.

## PostgreSQL Write Storm Mode

When `BOUNDARY_LAYER_POSTGRES_LIVE=true`, the write storm lab inserts bounded synthetic rows into `write_storm_events`. Vulnerable mode inserts the full requested batch (default 250). Hardened mode caps inserts at 50 and blocks excess writes. This lab does not attempt to crash PostgreSQL.

## Circuit Breaker Simulation

The circuit breaker lab uses deterministic synthetic work units. Vulnerable mode accepts all requested work and keeps the circuit closed. Hardened mode opens the circuit breaker and sheds excess work when requests exceed safe capacity (100). This lab does not call a real LLM or require GPUs.

## SSE Exhaustion Simulation

The SSE exhaustion lab uses deterministic synthetic stream units. Vulnerable mode accepts all requested streams without caps, idle timeout, or cleanup. Hardened mode applies a tenant stream cap (50), idle timeout, and cleanup. This lab does not open real long-running SSE streams or create socket exhaustion.

## Prompt Cache Isolation Simulation

The prompt cache isolation lab uses synthetic prompt prefixes only. Vulnerable mode stores cache entries under a global key without tenant identity, allowing Tenant B to hit Tenant A's entry. Hardened mode uses per-tenant cache namespaces under `boundary_layer:lab:prompt_cache:`. Live Redis mode is enabled when `BOUNDARY_LAYER_REDIS_LIVE=true` (default in Docker Compose). This lab does not store real prompts or reproduce confirmed production cache side-channel exploits.

## File Upload Sandbox Hardening

The file upload lab uses deterministic synthetic file metadata and extracted text. Vulnerable mode simulates extraction without sandbox, allows simulated egress, and inserts extracted text directly into context. Hardened mode applies sandbox policy, blocks egress, detects active content and hidden instructions, and wraps extracted content as untrusted data. This lab does not parse real files, execute external parsers, or open network connections.

## Alert Routing

Prometheus loads rules from `detections/prometheus/alerts.yml` and sends firing alerts to Alertmanager at `alertmanager:9093`. Alertmanager routes alerts to the local webhook at `http://alert-webhook:8080/alerts`. The webhook stores payloads in memory and exposes them at `GET http://localhost:8081/alerts`.

Validation clears the webhook store, runs the hardened circuit breaker lab to set `boundary_layer_inference_circuit_breaker_state` to `1`, and polls until `BoundaryLayerInferenceCircuitBreakerOpen` is delivered.

Alertmanager integration is local-only. No PagerDuty, Slack, or email routes are configured. Alerts do not leave the Docker network.

## Trust Boundaries

1. **User/API boundary**: Lab invocation requests enter the API.
2. **Retrieval boundary**: Untrusted content from RAG, uploads, or cache crosses into tool routing and context assembly.
3. **Auth boundary**: Tokens must carry scoped claims before restricted tool access.
4. **State boundary**: Redis session blobs must be integrity-protected.
5. **Governance boundary**: Prompt deletion must cascade across downstream queues.
6. **Write path boundary**: Prompt logging volume must respect tenant write budgets.
7. **Streaming boundary**: SSE streams must respect caps, idle timeouts, and cleanup.
8. **Cache boundary**: Prompt-prefix cache keys must include tenant identity.
9. **Observability boundary**: Metrics expose lab outcomes for detection rules.
10. **Alert boundary**: Firing alerts route through Alertmanager to a local webhook only.

## Vulnerable vs Hardened Mode

Each lab implements paired behavior:

- **Vulnerable**: Demonstrates the failure mode with minimal controls.
- **Hardened**: Applies a specific control (pattern detection, HMAC, scope checks, content wrapping, cascade audit).

Modes are selected via the `mode` field in lab POST requests. Each invocation is isolated and records metrics.

## Data Flow

```
POST /labs/{name}/run
  -> lab module (labs/*.py)
  -> simulated or live infrastructure interaction
  -> control evaluation
  -> metrics recording (apps/api/metrics.py)
  -> structured JSON response
```

Detection rules in `detections/prometheus/alerts.yml` reference emitted BoundaryLayer metric names.
