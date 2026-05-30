# Live Docker Release Gate

This document describes the final live Docker release gate for BoundaryLayer before public promotion. It is public-facing guidance, not a command transcript dump. Generated validation logs and command transcripts belong in local review bundles only (`make bundle`) and are not committed to Git.

## Purpose

Confirm that the full Docker Compose stack, all nine labs, live Redis and PostgreSQL integration, Prometheus metrics and rules, and Alertmanager delivery to the local webhook work together from a clean runtime state.

## Prerequisites

- Python 3.12+
- Docker and Docker Compose running
- `curl`
- macOS or Linux recommended

## Release gate commands

From the repository root:

```bash
make setup
make test
make lint
docker compose down -v --remove-orphans
make up
make validate
```

Expected baseline:

- 149 tests passing
- Lint clean
- `make validate` exits 0
- Alert delivery includes `BoundaryLayerInferenceCircuitBreakerOpen`

## Services verified

| Service | Port | Check |
|---------|------|-------|
| API | 8000 | `GET /health`, `/labs`, `/metrics` |
| Mock LLM | 8080 | Healthy via Compose |
| Redis | 6379 | `redis-cli ping`, namespaced keys |
| PostgreSQL | 5432 | Tables and lab row counts |
| Prometheus | 9090 | `/-/healthy`, targets up, rules loaded |
| Alertmanager | 9093 | `/-/healthy` |
| Alert webhook | 8081 | `GET /health`, `GET /alerts` |

## Labs verified

All nine labs run in vulnerable and hardened mode:

- Tool Router Injection
- Redis State Tampering
- Flat AuthN/AuthZ
- File Upload Injection and Sandbox Hardening
- Prompt Governance
- PostgreSQL Write Storm
- Circuit Breaker
- SSE Exhaustion
- Prompt Cache Isolation

Each response must include `lab`, `mode`, `blocked`, `risk`, `control`, `events`, and `summary`.

## Observability verified

- API exposes Prometheus metrics at `/metrics`
- Prometheus scrapes the API target
- Alert rules load from `detections/prometheus/alerts.yml`
- Required alert names include `BoundaryLayerInferenceCircuitBreakerOpen`

## Alert delivery verified

1. Clear webhook store: `curl -sf -X DELETE http://localhost:8081/alerts`
2. Trigger circuit breaker: hardened mode with default load
3. Poll `GET /alerts` for up to 60 seconds
4. Confirm `BoundaryLayerInferenceCircuitBreakerOpen` in the payload

## Database checks

**Redis**

```bash
docker compose exec -T redis redis-cli ping
docker compose exec -T redis redis-cli keys 'boundary_layer:lab:*' | head -50
```

**PostgreSQL**

```bash
docker compose exec -T postgres psql -U boundary_layer -d boundary_layer -c "\dt"
docker compose exec -T postgres psql -U boundary_layer -d boundary_layer -c "SELECT count(*) FROM deletion_audit;"
docker compose exec -T postgres psql -U boundary_layer -d boundary_layer -c "SELECT count(*) FROM write_storm_events;"
```

## Manual extended gate (optional)

For a deeper pre-release pass, also verify:

- 18 lab JSON outputs under `/tmp/boundary-layer-live-gate/`
- Special-case functional behavior (circuit breaker within capacity, SSE within cap, write storm blocking, prompt cache isolation, file upload safe path)
- Prometheus targets and selected alert rule names via `/api/v1/targets` and `/api/v1/rules`
- Service log tails for tracebacks or fatal errors

See [E2E_VALIDATION.md](E2E_VALIDATION.md) for command details.

## Troubleshooting

| Symptom | Action |
|---------|--------|
| API unhealthy | Wait for Compose health checks; inspect `docker compose logs api` |
| 503 from Postgres labs | Confirm postgres container healthy |
| No alert within 60s | Confirm circuit breaker metric open; wait for Prometheus evaluation |
| Empty Redis keys | Rerun Redis or prompt cache labs; keys may expire by TTL |
| `make validate` fails on metrics | Rerun from clean state: `docker compose down -v && make up` |

## Scope

- Validation is local-only and defensive.
- No external LLM APIs are called.
- No external alert integrations are used.
- Synthetic lab data only.

For demo walkthrough, see [DEMO.md](DEMO.md). For architecture context, see [DIAGRAMS.md](DIAGRAMS.md).
