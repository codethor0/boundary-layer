# BoundaryLayer Examples

Copy-paste curl examples for all nine labs. Stack must be running (`make up`).

Examples are abbreviated. Exact event text may vary slightly as validation scripts evolve.

Current API version (from `GET /health`): `1.3.5` (or read live from `/health` instead of hardcoding).

## Health

```bash
curl -sf http://localhost:8000/health
```

```json
{"status":"ok","service":"boundary-layer-api","version":"1.3.5","environment":"development"}
```

## List labs

```bash
curl -sf http://localhost:8000/labs
```

## Tool Router Injection

**Infrastructure:** deterministic in-process simulation.

```bash
curl -sf -X POST http://localhost:8000/labs/tool-router/run \
  -H "Content-Type: application/json" -d '{"mode":"vulnerable"}'
curl -sf -X POST http://localhost:8000/labs/tool-router/run \
  -H "Content-Type: application/json" -d '{"mode":"hardened"}'
```

| Mode | Notice | Metric | Alert |
|------|--------|--------|-------|
| vulnerable | Poisoned retrieval routes to destructive tool | `boundary_layer_lab_runs_total{lab="tool-router",result="allowed"}` | — |
| hardened | Injection pattern blocked before tool dispatch | `boundary_layer_tool_injection_blocked_total` | `BoundaryLayerToolInjectionBlockedSpike` (on sustained increase) |

Excerpt (hardened): `"blocked": true`, `"control"` mentions tool allowlist or injection filtering.

## Redis State Tampering

**Infrastructure:** live Redis plus deterministic fallback.

```bash
curl -sf -X POST http://localhost:8000/labs/redis/run \
  -H "Content-Type: application/json" -d '{"mode":"vulnerable"}'
curl -sf -X POST http://localhost:8000/labs/redis/run \
  -H "Content-Type: application/json" -d '{"mode":"hardened"}'
```

| Mode | Notice | Metric | Alert |
|------|--------|--------|-------|
| vulnerable | Tampered session blob accepted; role escalates | `boundary_layer_lab_runs_total{lab="redis",result="allowed"}` | — |
| hardened | HMAC verification rejects tamper | `boundary_layer_redis_tamper_rejected_total` | `BoundaryLayerRedisTamperRejected` |

Excerpt (vulnerable): `"blocked": false`, summary mentions privilege escalation.

Excerpt (hardened): `"blocked": true`, `"control": "HMAC session integrity verification"`.

## Flat AuthN/AuthZ

**Infrastructure:** deterministic in-process simulation.

```bash
curl -sf -X POST http://localhost:8000/labs/authz/run \
  -H "Content-Type: application/json" -d '{"mode":"vulnerable"}'
curl -sf -X POST http://localhost:8000/labs/authz/run \
  -H "Content-Type: application/json" -d '{"mode":"hardened"}'
```

| Mode | Notice | Metric | Alert |
|------|--------|--------|-------|
| vulnerable | Broad token invokes restricted admin tool | `boundary_layer_lab_runs_total{lab="authz",result="allowed"}` | — |
| hardened | Restricted tool denied for token scope | `boundary_layer_authz_denied_total` | `BoundaryLayerAuthzDenied` |

Excerpt (hardened): `"blocked": true`, summary mentions authorization denial.

## File Upload Injection

**Infrastructure:** deterministic metadata/content simulation (not real parser sandboxing).

```bash
curl -sf -X POST http://localhost:8000/labs/file-upload/run \
  -H "Content-Type: application/json" \
  -d '{"mode":"vulnerable","file_type":"pdf","content_hint":"hidden instruction"}'
curl -sf -X POST http://localhost:8000/labs/file-upload/run \
  -H "Content-Type: application/json" \
  -d '{"mode":"hardened","file_type":"pdf","content_hint":"hidden instruction"}'
```

| Mode | Notice | Metric | Alert |
|------|--------|--------|-------|
| vulnerable | Unsafe extraction path accepts hidden instruction | `boundary_layer_file_upload_extractions_total` | — |
| hardened | Sandbox, wrapping, or egress block applied | `boundary_layer_file_upload_hidden_instruction_detected_total` | `BoundaryLayerFileUploadHiddenInstructionDetected` |

Excerpt (hardened): `"blocked": true`, control mentions sandbox or untrusted wrapping.

## Prompt Governance

**Infrastructure:** live PostgreSQL plus fallback.

```bash
curl -sf -X POST http://localhost:8000/labs/governance/run \
  -H "Content-Type: application/json" -d '{"mode":"vulnerable"}'
curl -sf -X POST http://localhost:8000/labs/governance/run \
  -H "Content-Type: application/json" -d '{"mode":"hardened"}'
```

| Mode | Notice | Metric | Alert |
|------|--------|--------|-------|
| vulnerable | Deletion leaves orphan downstream records | `boundary_layer_prompt_deletion_orphan_records_total` | `BoundaryLayerPromptDeletionIncomplete` |
| hardened | Deletion audit completes with cascade checks | `boundary_layer_governance_deletion_audits_total` | — |

Excerpt (vulnerable): `"blocked": false`, summary mentions orphaned records.

## PostgreSQL Write Storm

**Infrastructure:** live PostgreSQL bounded synthetic inserts.

```bash
curl -sf -X POST http://localhost:8000/labs/postgres-write-storm/run \
  -H "Content-Type: application/json" -d '{"mode":"vulnerable","requested_writes":50}'
curl -sf -X POST http://localhost:8000/labs/postgres-write-storm/run \
  -H "Content-Type: application/json" -d '{"mode":"hardened","requested_writes":50}'
```

| Mode | Notice | Metric | Alert |
|------|--------|--------|-------|
| vulnerable | Unbounded synthetic writes accepted | `boundary_layer_postgres_write_storm_events_total` | `BoundaryLayerPostgresWriteStormDetected` |
| hardened | Write budget blocks excess inserts | `boundary_layer_postgres_write_storm_blocked_writes_total` | `BoundaryLayerPostgresWriteStormMitigated` |

Excerpt (hardened): `"blocked": true`, control mentions write budget.

## Circuit Breaker

**Infrastructure:** deterministic synthetic work units.

```bash
curl -sf -X POST http://localhost:8000/labs/circuit-breaker/run \
  -H "Content-Type: application/json" -d '{"mode":"vulnerable"}'
curl -sf -X POST http://localhost:8000/labs/circuit-breaker/run \
  -H "Content-Type: application/json" -d '{"mode":"hardened"}'
```

| Mode | Notice | Metric | Alert |
|------|--------|--------|-------|
| vulnerable | High load accepted; simulated failures rise | `boundary_layer_inference_simulated_failures_total` | — |
| hardened | Circuit opens; work shed at safe capacity | `boundary_layer_inference_circuit_breaker_state` = 1 | `BoundaryLayerInferenceCircuitBreakerOpen` |

Excerpt (hardened): `"blocked": true`, events mention load shedding.

Trigger alert delivery (clear webhook first):

```bash
curl -sf -X DELETE http://localhost:8081/alerts
curl -sf -X POST http://localhost:8000/labs/circuit-breaker/run \
  -H "Content-Type: application/json" -d '{"mode":"hardened"}'
# Wait up to 60 seconds
curl -sf http://localhost:8081/alerts
```

## SSE Exhaustion

**Infrastructure:** deterministic synthetic stream units (no real sockets).

Default request uses `requested_streams: 250`. Use explicit counts to contrast within-cap vs over-cap behavior.

**Default contrast (250 streams — mitigation visible):**

```bash
curl -sf -X POST http://localhost:8000/labs/sse-exhaustion/run \
  -H "Content-Type: application/json" -d '{"mode":"vulnerable"}'
curl -sf -X POST http://localhost:8000/labs/sse-exhaustion/run \
  -H "Content-Type: application/json" -d '{"mode":"hardened"}'
```

| Mode | Default (250 streams) | `blocked` | Accepted | Rejected |
|------|----------------------|-----------|----------|----------|
| vulnerable | No cap | `false` | 250 | 0 |
| hardened | Cap 50 + cleanup | `true` | 50 | 200 |

**Within-cap hardened (no rejection):**

```bash
curl -sf -X POST http://localhost:8000/labs/sse-exhaustion/run \
  -H "Content-Type: application/json" -d '{"mode":"hardened","requested_streams":25}'
```

| Mode | Notice | Metric | Alert |
|------|--------|--------|-------|
| vulnerable | Streams exceed tenant cap; pressure rises | `boundary_layer_sse_active_streams` | `BoundaryLayerSSEStreamExhaustionDetected` |
| hardened (default 250) | Excess streams rejected; cleanup applied | `boundary_layer_sse_rejected_streams_total` | `BoundaryLayerSSEBackpressureTriggered` |
| hardened (within cap) | All requested streams accepted | `boundary_layer_sse_cleanup_applied_total` | — |

Excerpt (hardened default): `"blocked": true`, events mention rejected streams. Within-cap hardened returns `"blocked": false`.

## Prompt Cache Isolation

**Infrastructure:** live Redis plus fallback.

```bash
curl -sf -X POST http://localhost:8000/labs/prompt-cache-isolation/run \
  -H "Content-Type: application/json" -d '{"mode":"vulnerable"}'
curl -sf -X POST http://localhost:8000/labs/prompt-cache-isolation/run \
  -H "Content-Type: application/json" -d '{"mode":"hardened"}'
```

| Mode | Notice | Metric | Alert |
|------|--------|--------|-------|
| vulnerable | Shared cache key allows cross-tenant bleed | `boundary_layer_prompt_cache_cross_tenant_bleed_total` | `BoundaryLayerPromptCacheCrossTenantBleed` |
| hardened | Tenant-scoped namespace enforced | `boundary_layer_prompt_cache_isolation_applied_total` | `BoundaryLayerPromptCacheIsolationApplied` |

Excerpt (vulnerable): `"blocked": false`, summary mentions cross-tenant bleed.

Excerpt (hardened): `"blocked": true`, control mentions tenant-scoped isolation.

## Metrics snapshot

```bash
curl -sf http://localhost:8000/metrics | grep boundary_layer_ | head -30
```

See [docs/METRICS.md](METRICS.md) for the full catalog.

## Related

- [WORKSHOP.md](WORKSHOP.md) — facilitator walkthrough
- [LIVE_VS_SIMULATED.md](LIVE_VS_SIMULATED.md) — realism matrix
- [OBSERVABILITY_WALKTHROUGH.md](OBSERVABILITY_WALKTHROUGH.md) — Prometheus and Alertmanager
