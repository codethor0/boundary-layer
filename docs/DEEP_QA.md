# Deep End-to-End QA

This document describes the deeper quality-assurance pass for BoundaryLayer beyond the standard live release gate. It verifies API contracts, invalid-input handling, metrics consistency, live Redis and PostgreSQL state, Prometheus rules, Alertmanager delivery, and Docker restart recovery.

Generated command transcripts and validation logs belong in local review bundles only (`make bundle`) and are not committed to Git.

## Purpose

Confirm the application behaves as documented under normal and adversarial inputs, not only that the happy path passes. This pass is a quality gate, not a feature pass.

## Prerequisites

- Python 3.12+
- Docker and Docker Compose running
- `curl`
- Clean runtime recommended: `docker compose down -v --remove-orphans && make up`

## Baseline

```bash
make setup
make test
make lint
make up
```

Expected: 177 tests passing, lint clean, all seven Compose services running (health checks healthy where defined).

## API contract testing

```bash
curl -sf http://localhost:8000/health
curl -sf http://localhost:8000/labs
curl -sf http://localhost:8000/metrics | head -120
```

Verify:

- `/health` returns JSON with `status`, `service`, and `version`
- `/labs` lists all nine lab identifiers
- `/metrics` returns Prometheus exposition text (not HTML)

Lab inventory check:

```bash
python3 - <<'PY'
import json, urllib.request
expected = {
    "tool-router", "redis", "authz", "file-upload", "governance",
    "postgres-write-storm", "circuit-breaker", "sse-exhaustion", "prompt-cache-isolation",
}
with urllib.request.urlopen("http://localhost:8000/labs") as r:
    blob = json.dumps(json.loads(r.read().decode()))
missing = [x for x in expected if x not in blob]
assert not missing, missing
print("labs inventory verified")
PY
```

## Lab contract and behavior testing

Run all nine labs in vulnerable and hardened mode. Each response must include `lab`, `mode`, `blocked`, `risk`, `control`, `events`, and `summary`.

Behavior expectations:

| Lab | Vulnerable | Hardened |
|-----|------------|----------|
| Tool Router | Not blocked | Blocked |
| Redis | Accepts tampered state | Rejects tampered state |
| AuthZ | Allows broad access | Denies unauthorized access |
| File Upload | Unsafe path allowed | Risky defaults blocked; safe path not blocked |
| Governance | Orphan records remain | Deletion propagation and audit |
| Write Storm | Full batch inserted | Excess writes blocked |
| Circuit Breaker | All work accepted | Default opens; within-capacity stays closed |
| SSE Exhaustion | All streams accepted | Excess rejected; within-capacity not blocked |
| Prompt Cache | Cross-tenant bleed | Tenant-scoped keys |

See [E2E_VALIDATION.md](E2E_VALIDATION.md) and [LIVE_RELEASE_GATE.md](LIVE_RELEASE_GATE.md) for command examples.

## Invalid input testing

Invalid mode should return 4xx (422):

```bash
curl -s -o /dev/null -w "%{http_code}\n" \
  -X POST http://localhost:8000/labs/redis/run \
  -H "Content-Type: application/json" \
  -d '{"mode":"invalid"}'
```

Malformed JSON and missing body should also return 4xx without crashing the API.

Field validators (all should return 4xx):

```bash
# Excessive write count
curl -s -o /dev/null -w "%{http_code}\n" \
  -X POST http://localhost:8000/labs/postgres-write-storm/run \
  -H "Content-Type: application/json" \
  -d '{"mode":"hardened","requested_writes":100000}'

# Excessive work units
curl -s -o /dev/null -w "%{http_code}\n" \
  -X POST http://localhost:8000/labs/circuit-breaker/run \
  -H "Content-Type: application/json" \
  -d '{"mode":"hardened","requested_work_units":100000}'

# Excessive streams
curl -s -o /dev/null -w "%{http_code}\n" \
  -X POST http://localhost:8000/labs/sse-exhaustion/run \
  -H "Content-Type: application/json" \
  -d '{"mode":"hardened","requested_streams":100000}'

# Invalid file type
curl -s -o /dev/null -w "%{http_code}\n" \
  -X POST http://localhost:8000/labs/file-upload/run \
  -H "Content-Type: application/json" \
  -d '{"mode":"hardened","file_type":"exe"}'
```

## Metrics consistency testing

After running all labs:

```bash
curl -sf http://localhost:8000/metrics > /tmp/boundary-layer-metrics.txt
```

Required metric families include:

- `boundary_layer_lab_runs_total`
- `boundary_layer_tool_injection_blocked_total`
- `boundary_layer_redis_tamper_rejected_total`
- `boundary_layer_authz_denied_total`
- `boundary_layer_file_injection_blocked_total`
- `boundary_layer_prompt_deletion_orphan_records_total`
- `boundary_layer_governance_deletion_audits_total`
- `boundary_layer_postgres_write_storm_events_total`
- `boundary_layer_postgres_write_storm_blocked_writes_total`
- `boundary_layer_inference_circuit_breaker_state`
- `boundary_layer_inference_shed_work_units_total`
- `boundary_layer_sse_rejected_streams_total`
- `boundary_layer_prompt_cache_cross_tenant_bleed_total`
- `boundary_layer_prompt_cache_isolation_applied_total`
- `boundary_layer_file_upload_sandbox_applied_total`
- `boundary_layer_file_upload_egress_blocked_total`

## Live Redis testing

```bash
docker compose exec -T redis redis-cli ping
docker compose exec -T redis redis-cli keys 'boundary_layer:lab:*' | head -50
```

Expected: `PONG` and namespaced keys only. Cache lab keys should have positive TTL where TTL is applied.

## Live PostgreSQL testing

```bash
docker compose exec -T postgres psql -U boundary_layer -d boundary_layer -c "\dt"
docker compose exec -T postgres psql -U boundary_layer -d boundary_layer -c \
  "SELECT mode, orphan_count, complete FROM deletion_audit ORDER BY created_at DESC LIMIT 10;"
docker compose exec -T postgres psql -U boundary_layer -d boundary_layer -c \
  "SELECT count(*) FROM write_storm_events;"
```

Expected after lab runs:

- Governance tables exist
- Vulnerable governance rows show `orphan_count > 0`
- Hardened governance rows show `complete = true`
- Write storm events exist after write storm runs

## Prometheus testing

```bash
curl -sf http://localhost:9090/-/healthy
curl -sf "http://localhost:9090/api/v1/targets"
curl -sf "http://localhost:9090/api/v1/rules"
```

All active targets should be `up`. Required alert rules include:

- `BoundaryLayerInferenceCircuitBreakerOpen`
- `BoundaryLayerSSEStreamExhaustionDetected`
- `BoundaryLayerPromptCacheCrossTenantBleed`
- `BoundaryLayerFileUploadHiddenInstructionDetected`
- `BoundaryLayerPostgresWriteStormDetected`
- `BoundaryLayerRedisTamperRejected`

## Alertmanager delivery testing

```bash
curl -sf -X DELETE http://localhost:8081/alerts
curl -sf -X POST http://localhost:8000/labs/circuit-breaker/run \
  -H "Content-Type: application/json" \
  -d '{"mode":"hardened"}'
# Poll up to 75 seconds
curl -sf http://localhost:8081/alerts
```

Expected: at least one alert containing `BoundaryLayerInferenceCircuitBreakerOpen`.

## Restart and recovery testing

```bash
docker compose restart api
sleep 5
curl -sf http://localhost:8000/health
curl -sf -X POST http://localhost:8000/labs/redis/run \
  -H "Content-Type: application/json" \
  -d '{"mode":"hardened"}'

docker compose restart prometheus alertmanager alert-webhook
sleep 10
curl -sf http://localhost:9090/-/healthy
curl -sf http://localhost:9093/-/healthy
curl -sf http://localhost:8081/health
```

Re-trigger circuit breaker and confirm webhook delivery after observability restart.

## Log inspection

```bash
docker compose logs --no-color --tail=300 api > /tmp/boundary-layer-api-tail.log
grep -RInEi "traceback|panic|fatal|segmentation fault" /tmp/boundary-layer-*-tail.log || true
```

Investigate real tracebacks, panics, or fatals. Harmless uses of the word "error" in status text may appear and are not necessarily failures.

## Full gate sequence

For release promotion, run deep QA after the standard gate:

```bash
make validate
# Then run the checks in this document
```

## Troubleshooting

| Symptom | Action |
|---------|--------|
| Empty Redis keys | Rerun Redis or prompt cache labs; keys may expire by TTL |
| No alert within 75s | Wait for Prometheus evaluation; confirm circuit breaker metric open |
| PostgreSQL counts zero | Rerun governance and write storm labs from clean stack |
| Target unhealthy | `docker compose ps`; inspect service logs |
| API 503 on live labs | Confirm postgres/redis containers healthy |

## Scope

- Local-only defensive validation
- No external LLM APIs
- No external alert integrations
- Synthetic lab data only

For the standard pre-release gate, see [LIVE_RELEASE_GATE.md](LIVE_RELEASE_GATE.md).
