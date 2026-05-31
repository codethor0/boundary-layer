# BoundaryLayer Metrics Catalog

Prometheus metrics are exposed at `GET http://localhost:8000/metrics`. Scrape interval in dev is 15 seconds. Alert rules live in `detections/prometheus/alerts.yml`.

## Core lab runs

| Metric | Type | Labels | Emitted by | Meaning | How to trigger | Related alert | Example PromQL |
|--------|------|--------|------------|---------|----------------|---------------|----------------|
| `boundary_layer_lab_runs_total` | Counter | `lab`, `mode`, `result` | All labs via `record_lab_run` | Count of lab executions (`result` = `allowed` or `blocked`) | Any `POST /labs/{lab}/run` | — | `increase(boundary_layer_lab_runs_total[5m])` |

## Tool / router

| Metric | Type | Labels | Emitted by | Meaning | How to trigger | Related alert | Example PromQL |
|--------|------|--------|------------|---------|----------------|---------------|----------------|
| `boundary_layer_tool_injection_blocked_total` | Counter | — | Tool router hardened | Injection-pattern blocks | `POST /labs/tool-router/run` hardened | `BoundaryLayerToolInjectionBlockedSpike` | `increase(boundary_layer_tool_injection_blocked_total[5m])` |

## Redis

| Metric | Type | Labels | Emitted by | Meaning | How to trigger | Related alert | Example PromQL |
|--------|------|--------|------------|---------|----------------|---------------|----------------|
| `boundary_layer_redis_tamper_rejected_total` | Counter | — | Redis lab hardened | HMAC tamper rejections | `POST /labs/redis/run` hardened | `BoundaryLayerRedisTamperRejected` | `increase(boundary_layer_redis_tamper_rejected_total[5m])` |

## Authz

| Metric | Type | Labels | Emitted by | Meaning | How to trigger | Related alert | Example PromQL |
|--------|------|--------|------------|---------|----------------|---------------|----------------|
| `boundary_layer_authz_denied_total` | Counter | — | Authz lab hardened | Restricted tool denials | `POST /labs/authz/run` hardened | `BoundaryLayerAuthzDenied` | `increase(boundary_layer_authz_denied_total[5m])` |

## File upload

| Metric | Type | Labels | Emitted by | Meaning | How to trigger | Related alert | Example PromQL |
|--------|------|--------|------------|---------|----------------|---------------|----------------|
| `boundary_layer_file_injection_blocked_total` | Counter | — | File upload hardened | Legacy injection block counter | File upload hardened runs | — | `increase(boundary_layer_file_injection_blocked_total[5m])` |
| `boundary_layer_file_upload_extractions_total` | Counter | `mode`, `file_type`, `result` | File upload lab | Synthetic extraction outcomes | `POST /labs/file-upload/run` | — | `sum by (result)(increase(boundary_layer_file_upload_extractions_total[5m]))` |
| `boundary_layer_file_upload_sandbox_applied_total` | Counter | `mode` | File upload hardened | Sandbox policy applied | File upload hardened | — | `increase(boundary_layer_file_upload_sandbox_applied_total[5m])` |
| `boundary_layer_file_upload_egress_blocked_total` | Counter | `mode` | File upload hardened | Simulated egress blocks | File upload hardened | `BoundaryLayerFileUploadEgressBlocked` | `increase(boundary_layer_file_upload_egress_blocked_total[5m])` |
| `boundary_layer_file_upload_active_content_blocked_total` | Counter | `mode`, `file_type` | File upload hardened | Active content blocked | File upload hardened | `BoundaryLayerFileUploadActiveContentBlocked` | `increase(boundary_layer_file_upload_active_content_blocked_total[5m])` |
| `boundary_layer_file_upload_hidden_instruction_detected_total` | Counter | `mode`, `file_type` | File upload hardened | Hidden instruction detections | File upload hardened with hint | `BoundaryLayerFileUploadHiddenInstructionDetected` | `increase(boundary_layer_file_upload_hidden_instruction_detected_total[5m])` |
| `boundary_layer_file_upload_untrusted_content_wrapped_total` | Counter | `mode` | File upload hardened | Untrusted wrapping applied | File upload hardened | `BoundaryLayerFileUploadContentWrapped` | `increase(boundary_layer_file_upload_untrusted_content_wrapped_total[5m])` |

## Governance

| Metric | Type | Labels | Emitted by | Meaning | How to trigger | Related alert | Example PromQL |
|--------|------|--------|------------|---------|----------------|---------------|----------------|
| `boundary_layer_prompt_deletion_orphan_records_total` | Counter | — | Governance vulnerable | Orphan records detected | `POST /labs/governance/run` vulnerable | `BoundaryLayerPromptDeletionIncomplete` | `increase(boundary_layer_prompt_deletion_orphan_records_total[5m])` |
| `boundary_layer_governance_deletion_audits_total` | Counter | `mode`, `complete` | Governance lab | Deletion audit writes | Governance runs | — | `increase(boundary_layer_governance_deletion_audits_total[5m])` |

## PostgreSQL write storm

| Metric | Type | Labels | Emitted by | Meaning | How to trigger | Related alert | Example PromQL |
|--------|------|--------|------------|---------|----------------|---------------|----------------|
| `boundary_layer_postgres_write_storm_events_total` | Counter | `mode`, `result` | Write storm lab | Synthetic inserts | `POST /labs/postgres-write-storm/run` | `BoundaryLayerPostgresWriteStormDetected` | `increase(boundary_layer_postgres_write_storm_events_total[5m])` |
| `boundary_layer_postgres_write_storm_blocked_writes_total` | Counter | `mode` | Write storm hardened | Budget-blocked writes | Write storm hardened | `BoundaryLayerPostgresWriteStormMitigated` | `increase(boundary_layer_postgres_write_storm_blocked_writes_total[5m])` |
| `boundary_layer_postgres_write_storm_insert_duration_seconds` | Histogram | `mode` | Write storm lab | Batch insert duration | Write storm runs | — | `histogram_quantile(0.99, sum(rate(boundary_layer_postgres_write_storm_insert_duration_seconds_bucket[5m])) by (le))` |

## Circuit breaker

| Metric | Type | Labels | Emitted by | Meaning | How to trigger | Related alert | Example PromQL |
|--------|------|--------|------------|---------|----------------|---------------|----------------|
| `boundary_layer_inference_circuit_breaker_state` | Gauge | — | Circuit breaker lab | 0=closed, 1=open | Circuit breaker hardened (default 250 units) | `BoundaryLayerInferenceCircuitBreakerOpen` | `boundary_layer_inference_circuit_breaker_state` |
| `boundary_layer_inference_requests_total` | Counter | `mode`, `result` | Circuit breaker lab | Work units requested/accepted | Circuit breaker runs | — | `increase(boundary_layer_inference_requests_total[5m])` |
| `boundary_layer_inference_shed_work_units_total` | Counter | `mode` | Circuit breaker hardened | Shed work units | Circuit breaker hardened | `BoundaryLayerInferenceWorkShed` | `increase(boundary_layer_inference_shed_work_units_total[5m])` |
| `boundary_layer_inference_simulated_failures_total` | Counter | `mode` | Circuit breaker vulnerable | Simulated failures | Circuit breaker vulnerable | — | `increase(boundary_layer_inference_simulated_failures_total[5m])` |
| `boundary_layer_inference_simulated_queue_depth` | Gauge | `mode` | Circuit breaker lab | Simulated queue depth | Circuit breaker runs | `BoundaryLayerInferenceQueueDepthHigh` | `boundary_layer_inference_simulated_queue_depth` |
| `boundary_layer_inference_simulated_p99_latency_ms` | Gauge | `mode` | Circuit breaker lab | Simulated p99 latency | Circuit breaker runs | — | `boundary_layer_inference_simulated_p99_latency_ms` |

## SSE exhaustion

| Metric | Type | Labels | Emitted by | Meaning | How to trigger | Related alert | Example PromQL |
|--------|------|--------|------------|---------|----------------|---------------|----------------|
| `boundary_layer_sse_streams_total` | Counter | `mode`, `result` | SSE lab | Stream requests | `POST /labs/sse-exhaustion/run` | — | `increase(boundary_layer_sse_streams_total[5m])` |
| `boundary_layer_sse_rejected_streams_total` | Counter | `mode` | SSE hardened | Rejected by cap | SSE hardened | — | `increase(boundary_layer_sse_rejected_streams_total[5m])` |
| `boundary_layer_sse_active_streams` | Gauge | `mode` | SSE lab | Active simulated streams | SSE runs | — | `boundary_layer_sse_active_streams` |
| `boundary_layer_sse_orphaned_streams` | Gauge | `mode` | SSE lab | Orphaned streams | SSE vulnerable | `BoundaryLayerSSEOrphanedStreamsDetected` | `boundary_layer_sse_orphaned_streams` |
| `boundary_layer_sse_worker_pressure` | Gauge | `mode` | SSE lab | Worker pressure | SSE runs | — | `boundary_layer_sse_worker_pressure` |
| `boundary_layer_sse_memory_pressure_mb` | Gauge | `mode` | SSE lab | Memory pressure MB | SSE runs | — | `boundary_layer_sse_memory_pressure_mb` |
| `boundary_layer_sse_cleanup_applied_total` | Counter | `mode` | SSE hardened | Cleanup applied | SSE hardened | `BoundaryLayerSSECleanupApplied` | `increase(boundary_layer_sse_cleanup_applied_total[5m])` |

## Prompt cache isolation

| Metric | Type | Labels | Emitted by | Meaning | How to trigger | Related alert | Example PromQL |
|--------|------|--------|------------|---------|----------------|---------------|----------------|
| `boundary_layer_prompt_cache_requests_total` | Counter | `mode`, `tenant`, `result` | Prompt cache lab | Cache operations | Prompt cache runs | — | `increase(boundary_layer_prompt_cache_requests_total[5m])` |
| `boundary_layer_prompt_cache_hits_total` | Counter | `mode`, `tenant`, `hit_type` | Prompt cache lab | Cache hits | Prompt cache runs | — | `increase(boundary_layer_prompt_cache_hits_total[5m])` |
| `boundary_layer_prompt_cache_cross_tenant_bleed_total` | Counter | `mode` | Prompt cache vulnerable | Cross-tenant bleed | Prompt cache vulnerable | `BoundaryLayerPromptCacheCrossTenantBleed` | `increase(boundary_layer_prompt_cache_cross_tenant_bleed_total[5m])` |
| `boundary_layer_prompt_cache_isolation_applied_total` | Counter | `mode` | Prompt cache hardened | Isolation applied | Prompt cache hardened | `BoundaryLayerPromptCacheIsolationApplied` | `increase(boundary_layer_prompt_cache_isolation_applied_total[5m])` |

## Alert / webhook (local)

Alertmanager POSTs firing alerts to the local webhook. The webhook does not export Prometheus metrics; inspect delivery with:

```bash
curl -sf http://localhost:8081/health
curl -sf http://localhost:8081/alerts
curl -sf -X DELETE http://localhost:8081/alerts
```

Run `make validate-alerts` to automate end-to-end delivery for six deterministic alerts:

| Alert | Lab trigger |
|-------|-------------|
| `BoundaryLayerInferenceCircuitBreakerOpen` | Circuit breaker hardened |
| `BoundaryLayerAuthzDenied` | Authz hardened |
| `BoundaryLayerRedisTamperRejected` | Redis hardened |
| `BoundaryLayerPostgresWriteStormMitigated` | Write storm hardened (`requested_writes: 250`) |
| `BoundaryLayerSSEBackpressureTriggered` | SSE exhaustion hardened default |
| `BoundaryLayerPromptDeletionIncomplete` | Governance vulnerable |

## Related

- [OBSERVABILITY_WALKTHROUGH.md](OBSERVABILITY_WALKTHROUGH.md)
- [CONTROLS_MAP.md](CONTROLS_MAP.md)
- [LIVE_VS_SIMULATED.md](LIVE_VS_SIMULATED.md)
