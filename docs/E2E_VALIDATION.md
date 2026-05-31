# End-to-End Validation Guide

This guide documents how to verify BoundaryLayer locally with Docker Compose. It is public-facing documentation, not a command transcript dump. Generated validation logs and command transcripts belong in local review bundles only (`make bundle`) and are not committed to Git.

## Purpose

Confirm that all nine labs, live Redis and PostgreSQL integration, Prometheus rules, Alertmanager routing, and the local alert webhook work together from a clean Docker state.

## Prerequisites

- Python 3.12+
- Docker and Docker Compose
- `curl`
- macOS or Linux recommended

## Baseline validation pipeline

From the repository root:

```bash
make setup
make test
make lint
docker compose down -v
make up
make smoke
make demo
make validate
make validate-alerts
make validate-restore-fresh-volume
```

Expected results:

- 184 tests passing
- Lint clean
- `make smoke` and `make demo` exit 0
- `make validate` exits 0
- Alert delivery validation confirms six deterministic alerts (`make validate-alerts`)
- Fresh-volume restore proof passes (`make validate-restore-fresh-volume`)

## Service health checks

After `make up`:

```bash
curl -sf http://localhost:8000/health
curl -sf http://localhost:8000/labs
curl -sf http://localhost:9090/-/healthy
curl -sf http://localhost:9093/-/healthy
curl -sf http://localhost:8081/health
```

Expected API health:

```json
{"status":"ok","service":"boundary-layer-api","version":"1.3.5"}
```

Version string must match the current release tag.

## Lab endpoint checks

Each lab accepts `{"mode":"vulnerable"}` or `{"mode":"hardened"}`. Every successful response includes `lab`, `mode`, `blocked`, `risk`, `control`, `events`, and `summary`.

Run all nine labs in both modes:

```bash
for lab in tool-router redis authz file-upload governance postgres-write-storm circuit-breaker sse-exhaustion prompt-cache-isolation; do
  curl -sf -X POST "http://localhost:8000/labs/${lab}/run" \
    -H "Content-Type: application/json" \
    -d '{"mode":"vulnerable"}' | python3 -m json.tool >/dev/null
  curl -sf -X POST "http://localhost:8000/labs/${lab}/run" \
    -H "Content-Type: application/json" \
    -d '{"mode":"hardened"}' | python3 -m json.tool >/dev/null
done
```

Special cases:

```bash
curl -sf -X POST http://localhost:8000/labs/circuit-breaker/run \
  -H "Content-Type: application/json" \
  -d '{"mode":"hardened","requested_work_units":50}'

curl -sf -X POST http://localhost:8000/labs/sse-exhaustion/run \
  -H "Content-Type: application/json" \
  -d '{"mode":"hardened","requested_streams":25,"stream_duration_seconds":10}'

curl -sf -X POST http://localhost:8000/labs/postgres-write-storm/run \
  -H "Content-Type: application/json" \
  -d '{"mode":"hardened","requested_writes":250}'

curl -sf -X POST http://localhost:8000/labs/prompt-cache-isolation/run \
  -H "Content-Type: application/json" \
  -d '{"mode":"hardened","tenant_a":"tenant-a","tenant_b":"tenant-b","prompt_prefix":"summarize synthetic acquisition plan"}'

curl -sf -X POST http://localhost:8000/labs/file-upload/run \
  -H "Content-Type: application/json" \
  -d '{"mode":"hardened","contains_hidden_instruction":false,"contains_active_content":false,"egress_attempted":false}'
```

Expected behavior:

- Vulnerable modes demonstrate the documented failure path.
- Hardened modes apply the documented control and set `blocked` appropriately.
- Invalid input returns HTTP 422 where request validation applies.

## Redis live check

```bash
docker compose exec -T redis redis-cli ping
docker compose exec -T redis redis-cli keys 'boundary_layer:lab:*' | head -50
```

Expected: `PONG` and namespaced lab keys after running Redis or prompt cache labs.

## PostgreSQL live check

```bash
docker compose exec -T postgres psql -U boundary_layer -d boundary_layer -c "\dt"
docker compose exec -T postgres psql -U boundary_layer -d boundary_layer -c "SELECT count(*) FROM deletion_audit;"
docker compose exec -T postgres psql -U boundary_layer -d boundary_layer -c "SELECT count(*) FROM write_storm_events;"
```

Expected: governance and write storm tables exist; counts increase after relevant lab runs.

## Prometheus check

```bash
curl -sf http://localhost:9090/-/healthy
curl -sf "http://localhost:9090/api/v1/targets" | head -100
curl -sf "http://localhost:9090/api/v1/rules" | head -200
```

Expected: Prometheus healthy, API scrape target up, alert rules loaded from `detections/prometheus/alerts.yml`.

## Alertmanager and webhook check

```bash
curl -sf -X DELETE http://localhost:8081/alerts
curl -sf -X POST http://localhost:8000/labs/circuit-breaker/run \
  -H "Content-Type: application/json" \
  -d '{"mode":"hardened"}'
```

Poll for alert delivery (up to 60 seconds):

```bash
for i in $(seq 1 60); do
  ALERTS="$(curl -sf http://localhost:8081/alerts || true)"
  echo "$ALERTS" | grep -q "BoundaryLayerInferenceCircuitBreakerOpen" && break
  sleep 1
done
curl -sf http://localhost:8081/alerts
```

Expected: webhook payload includes alert name `BoundaryLayerInferenceCircuitBreakerOpen`.

## Metrics spot check

```bash
curl -sf http://localhost:8000/metrics | head -80
```

Expected: Prometheus text format with `boundary_layer_` metric names after lab runs.

## Troubleshooting

| Symptom | Likely cause | Action |
|---------|--------------|--------|
| API not ready | Containers still starting | Wait for `make up` health checks; retry `/health` |
| 503 from governance or write storm labs | PostgreSQL not ready | `docker compose ps`; restart postgres |
| 503 from Redis labs | Redis not ready | `docker compose exec redis redis-cli ping` |
| No alert within 60s | Prometheus evaluation delay | Confirm circuit breaker metric is open; wait and poll again |
| Port conflict | Local service on 8000/9090/etc. | Stop conflicting services or change compose ports locally |

## Scope

- Validation is local-only.
- No external LLM APIs are called.
- No external alert integrations are used.
- Synthetic lab data only.

For a deeper pre-release pass before public promotion, see [LIVE_RELEASE_GATE.md](LIVE_RELEASE_GATE.md) and [DEEP_QA.md](DEEP_QA.md).
