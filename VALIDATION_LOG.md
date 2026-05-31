# Validation Log

## v1.0 Public Release Stabilization

Generated: 2026-05-31T21:05:13Z

Scope: Public GitHub release hygiene, no new labs, generated reports excluded from Git.

### Ruff format check
- Command: `/Users/thor/Projects/boundary-layer/.venv/bin/ruff format --check apps/ labs/ tests/`
- Result: PASS

### Ruff lint
- Command: `/Users/thor/Projects/boundary-layer/.venv/bin/ruff check apps/ labs/ tests/`
- Result: PASS

### Pytest
- Command: `/Users/thor/Projects/boundary-layer/.venv/bin/pytest tests/ -v --tb=short`
- Result: PASS

### API health check
- Command: `curl -sf http://localhost:8000/health`
- Result: PASS

### Lab tool-router (vulnerable)
- Command: `curl -sf -X POST http://localhost:8000/labs/tool-router/run -H 'Content-Type: application/json' -d '{"mode":"vulnerable"}'`
- Result: PASS

### Lab tool-router (hardened)
- Command: `curl -sf -X POST http://localhost:8000/labs/tool-router/run -H 'Content-Type: application/json' -d '{"mode":"hardened"}'`
- Result: PASS

### Lab redis (vulnerable)
- Command: `curl -sf -X POST http://localhost:8000/labs/redis/run -H 'Content-Type: application/json' -d '{"mode":"vulnerable"}'`
- Result: PASS

### Lab redis (hardened)
- Command: `curl -sf -X POST http://localhost:8000/labs/redis/run -H 'Content-Type: application/json' -d '{"mode":"hardened"}'`
- Result: PASS

### Lab authz (vulnerable)
- Command: `curl -sf -X POST http://localhost:8000/labs/authz/run -H 'Content-Type: application/json' -d '{"mode":"vulnerable"}'`
- Result: PASS

### Lab authz (hardened)
- Command: `curl -sf -X POST http://localhost:8000/labs/authz/run -H 'Content-Type: application/json' -d '{"mode":"hardened"}'`
- Result: PASS

### Lab file-upload (vulnerable)
- Command: `curl -sf -X POST http://localhost:8000/labs/file-upload/run -H 'Content-Type: application/json' -d '{"mode":"vulnerable"}'`
- Result: PASS

### Lab file-upload (hardened)
- Command: `curl -sf -X POST http://localhost:8000/labs/file-upload/run -H 'Content-Type: application/json' -d '{"mode":"hardened"}'`
- Result: PASS

### Lab governance (vulnerable)
- Command: `curl -sf -X POST http://localhost:8000/labs/governance/run -H 'Content-Type: application/json' -d '{"mode":"vulnerable"}'`
- Result: PASS

### Lab governance (hardened)
- Command: `curl -sf -X POST http://localhost:8000/labs/governance/run -H 'Content-Type: application/json' -d '{"mode":"hardened"}'`
- Result: PASS

### Lab postgres-write-storm (vulnerable)
- Command: `curl -sf -X POST http://localhost:8000/labs/postgres-write-storm/run -H 'Content-Type: application/json' -d '{"mode":"vulnerable"}'`
- Result: PASS

### Lab postgres-write-storm (hardened)
- Command: `curl -sf -X POST http://localhost:8000/labs/postgres-write-storm/run -H 'Content-Type: application/json' -d '{"mode":"hardened"}'`
- Result: PASS

### Lab circuit-breaker (vulnerable)
- Command: `curl -sf -X POST http://localhost:8000/labs/circuit-breaker/run -H 'Content-Type: application/json' -d '{"mode":"vulnerable"}'`
- Result: PASS

### Lab circuit-breaker (hardened)
- Command: `curl -sf -X POST http://localhost:8000/labs/circuit-breaker/run -H 'Content-Type: application/json' -d '{"mode":"hardened"}'`
- Result: PASS

### Lab sse-exhaustion (vulnerable)
- Command: `curl -sf -X POST http://localhost:8000/labs/sse-exhaustion/run -H 'Content-Type: application/json' -d '{"mode":"vulnerable"}'`
- Result: PASS

### Lab sse-exhaustion (hardened)
- Command: `curl -sf -X POST http://localhost:8000/labs/sse-exhaustion/run -H 'Content-Type: application/json' -d '{"mode":"hardened"}'`
- Result: PASS

### Lab prompt-cache-isolation (vulnerable)
- Command: `curl -sf -X POST http://localhost:8000/labs/prompt-cache-isolation/run -H 'Content-Type: application/json' -d '{"mode":"vulnerable"}'`
- Result: PASS

### Lab prompt-cache-isolation (hardened)
- Command: `curl -sf -X POST http://localhost:8000/labs/prompt-cache-isolation/run -H 'Content-Type: application/json' -d '{"mode":"hardened"}'`
- Result: PASS

### Metrics endpoint HTTP 200
- Command: `curl -sf http://localhost:8000/metrics`
- Result: PASS

### Metric present: boundary_layer_lab_runs_total
- Command: `grep boundary_layer_lab_runs_total /metrics`
- Result: PASS

### Metric present: boundary_layer_tool_injection_blocked_total
- Command: `grep boundary_layer_tool_injection_blocked_total /metrics`
- Result: PASS

### Metric present: boundary_layer_redis_tamper_rejected_total
- Command: `grep boundary_layer_redis_tamper_rejected_total /metrics`
- Result: PASS

### Metric present: boundary_layer_authz_denied_total
- Command: `grep boundary_layer_authz_denied_total /metrics`
- Result: PASS

### Metric present: boundary_layer_file_injection_blocked_total
- Command: `grep boundary_layer_file_injection_blocked_total /metrics`
- Result: PASS

### Metric present: boundary_layer_prompt_deletion_orphan_records_total
- Command: `grep boundary_layer_prompt_deletion_orphan_records_total /metrics`
- Result: PASS

### Metric present: boundary_layer_governance_deletion_audits_total
- Command: `grep boundary_layer_governance_deletion_audits_total /metrics`
- Result: PASS

### Metric present: boundary_layer_postgres_write_storm_events_total
- Command: `grep boundary_layer_postgres_write_storm_events_total /metrics`
- Result: PASS

### Metric present: boundary_layer_postgres_write_storm_blocked_writes_total
- Command: `grep boundary_layer_postgres_write_storm_blocked_writes_total /metrics`
- Result: PASS

### Metric present: boundary_layer_postgres_write_storm_insert_duration_seconds
- Command: `grep boundary_layer_postgres_write_storm_insert_duration_seconds /metrics`
- Result: PASS

### Metric present: boundary_layer_inference_circuit_breaker_state
- Command: `grep boundary_layer_inference_circuit_breaker_state /metrics`
- Result: PASS

### Metric present: boundary_layer_inference_requests_total
- Command: `grep boundary_layer_inference_requests_total /metrics`
- Result: PASS

### Metric present: boundary_layer_inference_shed_work_units_total
- Command: `grep boundary_layer_inference_shed_work_units_total /metrics`
- Result: PASS

### Metric present: boundary_layer_inference_simulated_failures_total
- Command: `grep boundary_layer_inference_simulated_failures_total /metrics`
- Result: PASS

### Metric present: boundary_layer_inference_simulated_queue_depth
- Command: `grep boundary_layer_inference_simulated_queue_depth /metrics`
- Result: PASS

### Metric present: boundary_layer_inference_simulated_p99_latency_ms
- Command: `grep boundary_layer_inference_simulated_p99_latency_ms /metrics`
- Result: PASS

### Metric present: boundary_layer_sse_streams_total
- Command: `grep boundary_layer_sse_streams_total /metrics`
- Result: PASS

### Metric present: boundary_layer_sse_rejected_streams_total
- Command: `grep boundary_layer_sse_rejected_streams_total /metrics`
- Result: PASS

### Metric present: boundary_layer_sse_active_streams
- Command: `grep boundary_layer_sse_active_streams /metrics`
- Result: PASS

### Metric present: boundary_layer_sse_orphaned_streams
- Command: `grep boundary_layer_sse_orphaned_streams /metrics`
- Result: PASS

### Metric present: boundary_layer_sse_worker_pressure
- Command: `grep boundary_layer_sse_worker_pressure /metrics`
- Result: PASS

### Metric present: boundary_layer_sse_memory_pressure_mb
- Command: `grep boundary_layer_sse_memory_pressure_mb /metrics`
- Result: PASS

### Metric present: boundary_layer_sse_cleanup_applied_total
- Command: `grep boundary_layer_sse_cleanup_applied_total /metrics`
- Result: PASS

### Metric present: boundary_layer_prompt_cache_requests_total
- Command: `grep boundary_layer_prompt_cache_requests_total /metrics`
- Result: PASS

### Metric present: boundary_layer_prompt_cache_hits_total
- Command: `grep boundary_layer_prompt_cache_hits_total /metrics`
- Result: PASS

### Metric present: boundary_layer_prompt_cache_cross_tenant_bleed_total
- Command: `grep boundary_layer_prompt_cache_cross_tenant_bleed_total /metrics`
- Result: PASS

### Metric present: boundary_layer_prompt_cache_isolation_applied_total
- Command: `grep boundary_layer_prompt_cache_isolation_applied_total /metrics`
- Result: PASS

### Metric present: boundary_layer_file_upload_extractions_total
- Command: `grep boundary_layer_file_upload_extractions_total /metrics`
- Result: PASS

### Metric present: boundary_layer_file_upload_sandbox_applied_total
- Command: `grep boundary_layer_file_upload_sandbox_applied_total /metrics`
- Result: PASS

### Metric present: boundary_layer_file_upload_egress_blocked_total
- Command: `grep boundary_layer_file_upload_egress_blocked_total /metrics`
- Result: PASS

### Metric present: boundary_layer_file_upload_active_content_blocked_total
- Command: `grep boundary_layer_file_upload_active_content_blocked_total /metrics`
- Result: PASS

### Metric present: boundary_layer_file_upload_hidden_instruction_detected_total
- Command: `grep boundary_layer_file_upload_hidden_instruction_detected_total /metrics`
- Result: PASS

### Metric present: boundary_layer_file_upload_untrusted_content_wrapped_total
- Command: `grep boundary_layer_file_upload_untrusted_content_wrapped_total /metrics`
- Result: PASS

### Metric emitted after lab runs: boundary_layer_tool_injection_blocked_total
- Command: `grep boundary_layer_tool_injection_blocked_total`
- Result: PASS

### Metric emitted after lab runs: boundary_layer_redis_tamper_rejected_total
- Command: `grep boundary_layer_redis_tamper_rejected_total`
- Result: PASS

### Metric emitted after lab runs: boundary_layer_authz_denied_total
- Command: `grep boundary_layer_authz_denied_total`
- Result: PASS

### Metric emitted after lab runs: boundary_layer_file_injection_blocked_total
- Command: `grep boundary_layer_file_injection_blocked_total`
- Result: PASS

### Metric emitted after lab runs: boundary_layer_prompt_deletion_orphan_records_total
- Command: `grep boundary_layer_prompt_deletion_orphan_records_total`
- Result: PASS

### PostgreSQL reachable in Docker
- Command: `docker compose exec -T postgres psql -U boundary_layer -d boundary_layer -c 'SELECT 1'`
- Result: PASS

### Governance orphan metric increased
- Command: `compare orphan counter before/after vulnerable run`
- Result: PASS

### Governance audit metric present
- Command: `grep boundary_layer_governance_deletion_audits_total`
- Result: PASS

### Write storm events metric present after vulnerable run
- Command: `grep boundary_layer_postgres_write_storm_events_total`
- Result: PASS

### Write storm blocked writes metric present after hardened run
- Command: `grep boundary_layer_postgres_write_storm_blocked_writes_total`
- Result: PASS

### PostgreSQL write_storm_events row count
- Command: `docker compose exec -T postgres psql -U boundary_layer -d boundary_layer -c 'SELECT count(*) FROM write_storm_events;'`
- Result: PASS

 count 
-------
    50
(1 row)
### Circuit breaker open after hardened default run
- Command: `grep boundary_layer_inference_circuit_breaker_state`
- Result: PASS

### Circuit breaker closed within safe capacity
- Command: `POST circuit-breaker hardened requested_work_units=50`
- Result: PASS

### Circuit breaker metric present: boundary_layer_inference_requests_total
- Command: `grep boundary_layer_inference_requests_total`
- Result: PASS

### Circuit breaker metric present: boundary_layer_inference_shed_work_units_total
- Command: `grep boundary_layer_inference_shed_work_units_total`
- Result: PASS

### Circuit breaker metric present: boundary_layer_inference_simulated_queue_depth
- Command: `grep boundary_layer_inference_simulated_queue_depth`
- Result: PASS

### Circuit breaker metric present: boundary_layer_inference_simulated_p99_latency_ms
- Command: `grep boundary_layer_inference_simulated_p99_latency_ms`
- Result: PASS

### SSE active streams metric after vulnerable run
- Command: `grep boundary_layer_sse_active_streams`
- Result: PASS

### SSE orphaned streams metric after vulnerable run
- Command: `grep boundary_layer_sse_orphaned_streams`
- Result: PASS

### SSE hardened default rejects excess streams
- Command: `POST sse-exhaustion hardened default`
- Result: PASS

### SSE rejected streams metric after hardened default run
- Command: `grep boundary_layer_sse_rejected_streams_total`
- Result: PASS

### SSE hardened within stream cap
- Command: `POST sse-exhaustion hardened requested_streams=25`
- Result: PASS

### SSE metric present: boundary_layer_sse_streams_total
- Command: `grep boundary_layer_sse_streams_total`
- Result: PASS

### SSE metric present: boundary_layer_sse_worker_pressure
- Command: `grep boundary_layer_sse_worker_pressure`
- Result: PASS

### SSE metric present: boundary_layer_sse_memory_pressure_mb
- Command: `grep boundary_layer_sse_memory_pressure_mb`
- Result: PASS

### SSE metric present: boundary_layer_sse_cleanup_applied_total
- Command: `grep boundary_layer_sse_cleanup_applied_total`
- Result: PASS

### Prompt cache cross-tenant bleed metric increased
- Command: `compare bleed counter before/after vulnerable run`
- Result: PASS

### Prompt cache isolation applied metric increased
- Command: `compare isolation counter before/after hardened run`
- Result: PASS

### Prompt cache vulnerable mode allows bleed
- Command: `POST prompt-cache-isolation vulnerable`
- Result: PASS

### Prompt cache hardened mode blocks bleed
- Command: `POST prompt-cache-isolation hardened`
- Result: PASS

### Prompt cache vulnerable run mentions live Redis
- Command: `grep live Redis in response events`
- Result: PASS

### Prompt cache metric present: boundary_layer_prompt_cache_requests_total
- Command: `grep boundary_layer_prompt_cache_requests_total`
- Result: PASS

### Prompt cache metric present: boundary_layer_prompt_cache_hits_total
- Command: `grep boundary_layer_prompt_cache_hits_total`
- Result: PASS

### Prompt cache metric present: boundary_layer_prompt_cache_cross_tenant_bleed_total
- Command: `grep boundary_layer_prompt_cache_cross_tenant_bleed_total`
- Result: PASS

### Prompt cache metric present: boundary_layer_prompt_cache_isolation_applied_total
- Command: `grep boundary_layer_prompt_cache_isolation_applied_total`
- Result: PASS

### Prompt cache invalid tenant rejected
- Command: `POST http://localhost:8000/labs/prompt-cache-isolation/run empty tenant_a`
- Result: PASS

### File upload vulnerable mode works
- Command: `POST file-upload vulnerable`
- Result: PASS

### File upload sandbox metric increased after hardened run
- Command: `compare sandbox counter before/after hardened run`
- Result: PASS

### File upload egress metric increased after hardened run
- Command: `compare egress counter before/after hardened run`
- Result: PASS

### File upload active metric increased after hardened run
- Command: `compare active counter before/after hardened run`
- Result: PASS

### File upload hidden metric increased after hardened run
- Command: `compare hidden counter before/after hardened run`
- Result: PASS

### File upload wrapped metric increased after hardened run
- Command: `compare wrapped counter before/after hardened run`
- Result: PASS

### File upload hardened mode blocks risky defaults
- Command: `POST file-upload hardened`
- Result: PASS

### File upload hardened safe fields not blocked
- Command: `POST file-upload hardened with no risky fields`
- Result: PASS

### File upload metric present: boundary_layer_file_upload_extractions_total
- Command: `grep boundary_layer_file_upload_extractions_total`
- Result: PASS

### File upload metric present: boundary_layer_file_upload_sandbox_applied_total
- Command: `grep boundary_layer_file_upload_sandbox_applied_total`
- Result: PASS

### File upload metric present: boundary_layer_file_upload_egress_blocked_total
- Command: `grep boundary_layer_file_upload_egress_blocked_total`
- Result: PASS

### File upload metric present: boundary_layer_file_upload_active_content_blocked_total
- Command: `grep boundary_layer_file_upload_active_content_blocked_total`
- Result: PASS

### File upload metric present: boundary_layer_file_upload_hidden_instruction_detected_total
- Command: `grep boundary_layer_file_upload_hidden_instruction_detected_total`
- Result: PASS

### File upload metric present: boundary_layer_file_upload_untrusted_content_wrapped_total
- Command: `grep boundary_layer_file_upload_untrusted_content_wrapped_total`
- Result: PASS

### File upload metric present: boundary_layer_file_injection_blocked_total
- Command: `grep boundary_layer_file_injection_blocked_total`
- Result: PASS

### File upload invalid file_type rejected
- Command: `POST http://localhost:8000/labs/file-upload/run invalid file_type`
- Result: PASS

### Postgres restore roundtrip
- Command: `drop write_storm_events then restore /Users/thor/Projects/boundary-layer/backups/postgres/boundary-layer-20260531T210517Z.sql.gz`
- Result: PASS

### Prometheus health check
- Command: `curl -sf http://localhost:9090/-/healthy`
- Result: PASS

### Alertmanager health check
- Command: `curl -sf http://localhost:9093/-/healthy`
- Result: PASS

### Alert webhook health check
- Command: `curl -sf http://localhost:8081/health`
- Result: PASS

### Circuit breaker metric open
- Command: `grep boundary_layer_inference_circuit_breaker_state`
- Result: PASS

### Clear alert webhook store
- Command: `DELETE http://localhost:8081/alerts`
- Result: PASS

### Metric present: boundary_layer_authz_denied_total
- Command: `grep boundary_layer_authz_denied_total`
- Result: PASS

### Alert delivered: BoundaryLayerAuthzDenied
- Command: `GET http://localhost:8081/alerts`
- Result: PASS

### Clear alert webhook store
- Command: `DELETE http://localhost:8081/alerts`
- Result: PASS

### Metric present: boundary_layer_redis_tamper_rejected_total
- Command: `grep boundary_layer_redis_tamper_rejected_total`
- Result: PASS

### Alert delivered: BoundaryLayerRedisTamperRejected
- Command: `GET http://localhost:8081/alerts`
- Result: PASS

### Clear alert webhook store
- Command: `DELETE http://localhost:8081/alerts`
- Result: PASS

### Metric present: boundary_layer_postgres_write_storm_blocked_writes_total
- Command: `grep boundary_layer_postgres_write_storm_blocked_writes_total`
- Result: PASS

### Alert delivered: BoundaryLayerPostgresWriteStormMitigated
- Command: `GET http://localhost:8081/alerts`
- Result: PASS

### Clear alert webhook store
- Command: `DELETE http://localhost:8081/alerts`
- Result: PASS

### Metric present: boundary_layer_sse_rejected_streams_total
- Command: `grep boundary_layer_sse_rejected_streams_total`
- Result: PASS

### Alert delivered: BoundaryLayerSSEBackpressureTriggered
- Command: `GET http://localhost:8081/alerts`
- Result: PASS

### Clear alert webhook store
- Command: `DELETE http://localhost:8081/alerts`
- Result: PASS

### Metric present: boundary_layer_prompt_deletion_orphan_records_total
- Command: `grep boundary_layer_prompt_deletion_orphan_records_total`
- Result: PASS

### Alert delivered: BoundaryLayerPromptDeletionIncomplete
- Command: `GET http://localhost:8081/alerts`
- Result: PASS

### Hardened lab after API restart
- Command: `curl -sf -X POST http://localhost:8000/labs/redis/run -H 'Content-Type: application/json' -d '{"mode":"hardened"}'`
- Result: PASS

### Metrics after API restart
- Command: `curl -sf http://localhost:8000/metrics`
- Result: PASS

### Logo SVG validation
- Command: `python logo svg checks`
- Result: PASS

### Secret scan
- Command: `rg secret patterns`
- Result: PASS

## Production SaaS Phase 7 — Live Evidence Capture

Generated: 2026-05-31T21:10:00Z

Scope: Attempt live staging validation; stop if prerequisites missing.

### Baseline
- Git HEAD: 99b9437
- Working tree: clean

### LIVE STAGING BLOCKED

Prerequisites: **MISSING**

Missing variable names (no values printed):

- RUN_LIVE_STAGING_CHECKS (when unset)
- STAGING_BASE_URL
- STAGING_TEST_ACCESS_TOKEN_TENANT_A
- STAGING_TEST_ACCESS_TOKEN_TENANT_B
- STAGING_METRICS_AUTH_TOKEN
- DATABASE_URL
- REDIS_URL
- OBJECT_STORAGE_BUCKET
- OBJECT_STORAGE_REGION
- OBJECT_STORAGE_PREFIX
- SECRET_MANAGER_PROVIDER
- SECRET_MANAGER_PROJECT_OR_PATH
- BOUNDARY_LAYER_HEALTHCHECK_SECRET_NAME
- OIDC_ISSUER_URL
- OIDC_AUDIENCE
- OIDC_JWKS_URL
- BOUNDARY_LAYER_ALLOWED_ORIGINS
- BOUNDARY_LAYER_PUBLIC_BASE_URL
- BOUNDARY_LAYER_METRICS_TOKEN
- AUDIT_SINK_PROVIDER

Local `.env.staging`: **not present**

GitHub Environment `staging`: **not found** (`gh secret list --env staging` HTTP 404)

| Secret/variable | Required | Present | Purpose |
|-----------------|----------|---------|---------|
| STAGING_BASE_URL | Yes | No | Live HTTP smoke |
| DATABASE_URL | Yes | No | Managed PostgreSQL live check |
| REDIS_URL | Yes | No | Managed Redis live check |
| OIDC_JWKS_URL | Yes | No | JWKS live check |
| STAGING_TEST_ACCESS_TOKEN_TENANT_A | Yes | No | Auth smoke |
| All others in STAGING_SECRETS_INVENTORY.md | Yes | No | Staging deploy and evidence runner |

Live evidence runner: **NOT RUN** (prereqs failed)

Production SaaS score: **6/10** (unchanged)

### Local regression
- make test (377): PASS
- make lint: PASS
- make smoke: PASS
- make validate: PASS
- make validate-alerts: PASS
- make validate-restore-fresh-volume: PASS

### Structural staging
- make staging-release-gate: PASS (LIVE STAGING CHECKS SKIPPED)
- make deploy-staging-dry-run: PASS (DRY RUN ONLY)

### Container build (local, not deployed)
- Image tag: boundary-layer-api:99b9437
- make container-smoke-local: PASS /health
- make container-image-check: PASS

### Security evidence
- pip-audit: PASS (no known vulnerabilities)
- make generate-sbom: PASS
- make container-security-scan: PASS (grype)
- Secret scan (validate.sh / tracked source): PASS
- make dependency-audit: SKIPPED (no Makefile target)
- make secret-scan: SKIPPED (no Makefile target; validate.sh used)

### Live checks (not run)
- WAF live: SKIPPED
- Audit/SIEM live: SKIPPED
- DR live: SKIPPED

Sanitized evidence file: `artifacts/live-evidence/LIVE_STAGING_EVIDENCE.md` (local, gitignored)

