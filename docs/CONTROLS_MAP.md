# Controls Map

Maps each lab to article gap, risk, control, detection, and validation.

## Lab 01: Tool Router Injection

| Field | Value |
|-------|-------|
| Article gap | Post-model tool routing trusts untrusted retrieval |
| Risk | Indirect prompt injection executes destructive tools |
| Control | Instruction-pattern detection and tool execution block |
| Detection | `BoundaryLayerToolInjectionBlockedSpike` on `boundary_layer_tool_injection_blocked_total` |
| Validation | `POST /labs/tool-router/run` in both modes; metric increment on hardened block |

## Lab 02: Redis State Tampering

| Field | Value |
|-------|-------|
| Article gap | Cache session blobs lack integrity protection |
| Risk | Privilege escalation via tampered session state |
| Control | HMAC session integrity verification |
| Detection | `BoundaryLayerRedisTamperRejected` on `boundary_layer_redis_tamper_rejected_total` |
| Validation | `POST /labs/redis/run` in both modes; live Redis keys under `boundary_layer:lab:redis:` |

## Lab 03: Flat AuthN/AuthZ

| Field | Value |
|-------|-------|
| Article gap | Authentication conflated with authorization |
| Risk | Restricted tools accessible with broad tokens |
| Control | Explicit scope and tenant match |
| Detection | `BoundaryLayerAuthzDenied` on `boundary_layer_authz_denied_total` |
| Validation | `POST /labs/authz/run` in both modes |

## Lab 04: File Upload Injection

| Field | Value |
|-------|-------|
| Article gap | Extracted file text treated as trusted context |
| Risk | Instruction injection via document content and unsafe extraction paths |
| Control | Sandbox policy, egress blocking, active content detection, instruction detection, untrusted wrapping |
| Detection | `BoundaryLayerFileUploadHiddenInstructionDetected`, `BoundaryLayerFileUploadEgressBlocked`, `BoundaryLayerFileUploadActiveContentBlocked`, `BoundaryLayerFileUploadContentWrapped` |
| Validation | `POST /labs/file-upload/run` in both modes; sandbox, egress, active content, hidden instruction, and wrapped content metrics |

## Lab 05: Prompt Governance

| Field | Value |
|-------|-------|
| Article gap | Prompt deletion ignores downstream artifacts |
| Risk | Orphaned records in eval/training pipelines |
| Control | Downstream dependency audit and cascade deletion |
| Detection | `BoundaryLayerPromptDeletionIncomplete` on `boundary_layer_prompt_deletion_orphan_records_total` |
| Validation | `POST /labs/governance/run` in both modes |

## Lab 06: PostgreSQL Write Storm

| Field | Value |
|-------|-------|
| Article gap | Runaway prompt logging overloads PostgreSQL primary writer |
| Risk | Write-path saturation from uncontrolled application inserts |
| Control | Tenant write budget and backpressure on synthetic batches |
| Detection | `BoundaryLayerPostgresWriteStormDetected`, `BoundaryLayerPostgresWriteStormMitigated` |
| Validation | `POST /labs/postgres-write-storm/run` in both modes; metrics and `write_storm_events` row count |

## Lab 07: Circuit Breaker Simulation

| Field | Value |
|-------|-------|
| Article gap | Inference tier accepts unbounded work without backpressure |
| Risk | Cascading failure from queue growth and elevated error rates |
| Control | Circuit breaker and load shedding at safe capacity |
| Detection | `BoundaryLayerInferenceCircuitBreakerOpen`, `BoundaryLayerInferenceQueueDepthHigh`, `BoundaryLayerInferenceWorkShed` |
| Validation | `POST /labs/circuit-breaker/run` in both modes; circuit breaker state gauge changes |

## Lab 08: SSE Exhaustion Simulation

| Field | Value |
|-------|-------|
| Article gap | Unbounded SSE streams exhaust workers and memory |
| Risk | Streaming resource exhaustion without caps or cleanup |
| Control | Tenant stream cap, idle timeout, and cleanup |
| Detection | `BoundaryLayerSSEStreamExhaustionDetected`, `BoundaryLayerSSEOrphanedStreamsDetected`, `BoundaryLayerSSEBackpressureTriggered`, `BoundaryLayerSSECleanupApplied` |
| Validation | `POST /labs/sse-exhaustion/run` in both modes; active, orphaned, and rejected stream metrics |

## Lab 09: Prompt Cache Isolation

| Field | Value |
|-------|-------|
| Article gap | Shared prompt-prefix cache keys omit tenant identity |
| Risk | Cross-tenant cache bleed and side-channel exposure |
| Control | Per-tenant cache namespace isolation |
| Detection | `BoundaryLayerPromptCacheCrossTenantBleed`, `BoundaryLayerPromptCacheIsolationApplied` |
| Validation | `POST /labs/prompt-cache-isolation/run` in both modes; bleed and isolation metrics |

## Cross-Cutting Detections

- `PostgresPrimarySaturation` - external PostgreSQL connection saturation (not lab metrics)
- `BoundaryLayerPostgresWriteStormDetected` - lab write storm activity threshold
- `BoundaryLayerPostgresWriteStormMitigated` - hardened write storm blocked excess writes
- `BoundaryLayerInferenceCircuitBreakerOpen` on lab-driven `boundary_layer_inference_circuit_breaker_state`
- `BoundaryLayerInferenceQueueDepthHigh` on `boundary_layer_inference_simulated_queue_depth`
- `BoundaryLayerInferenceWorkShed` on `boundary_layer_inference_shed_work_units_total`
- `BoundaryLayerSSEStreamExhaustionDetected` on `boundary_layer_sse_active_streams`
- `BoundaryLayerSSEOrphanedStreamsDetected` on `boundary_layer_sse_orphaned_streams`
- `BoundaryLayerSSEBackpressureTriggered` on `boundary_layer_sse_rejected_streams_total`
- `BoundaryLayerSSECleanupApplied` on `boundary_layer_sse_cleanup_applied_total`
- `BoundaryLayerPromptCacheCrossTenantBleed` on `boundary_layer_prompt_cache_cross_tenant_bleed_total`
- `BoundaryLayerPromptCacheIsolationApplied` on `boundary_layer_prompt_cache_isolation_applied_total`
- `BoundaryLayerFileUploadHiddenInstructionDetected` on `boundary_layer_file_upload_hidden_instruction_detected_total`
- `BoundaryLayerFileUploadEgressBlocked` on `boundary_layer_file_upload_egress_blocked_total`
- `BoundaryLayerFileUploadActiveContentBlocked` on `boundary_layer_file_upload_active_content_blocked_total`
- `BoundaryLayerFileUploadContentWrapped` on `boundary_layer_file_upload_untrusted_content_wrapped_total`

## Metrics Validation

`make validate` checks `GET /metrics` returns all required metric names and that hardened lab runs emit block counters.

## Alert Delivery Validation

`make validate` checks Prometheus (`9090`), Alertmanager (`9093`), and alert webhook (`8081`) health, then confirms `BoundaryLayerInferenceCircuitBreakerOpen` is delivered to the local webhook after a hardened circuit breaker lab run.
