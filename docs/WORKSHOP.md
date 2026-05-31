# BoundaryLayer Workshop Guide

A practical 30–45 minute walkthrough for teams learning LLM infrastructure security beyond prompt injection.

## Audience

- Platform and AI infrastructure engineers
- Security and DevSecOps teams
- Educators running a local security lab session

## Time required

30–45 minutes (plus 5–10 minutes for `make setup` on first run).

## Prerequisites

- Python 3.12+
- Docker and Docker Compose
- `curl`
- A machine you control (local lab only; not for public internet exposure)

## Learning objectives

By the end, participants should be able to:

1. Run the dev stack and validate it locally.
2. Compare vulnerable vs hardened lab outcomes on live Redis.
3. Explain tenant-scoped cache isolation using the prompt cache lab.
4. Trigger a Prometheus alert and inspect Alertmanager webhook delivery.
5. Describe why BoundaryLayer is a local lab, not hosted production SaaS.

## Step 1: Start the stack

```bash
git clone https://github.com/codethor0/boundary-layer.git
cd boundary-layer
make setup
make up
make smoke
```

Expected: smoke prints `PASS health` with `"version":"1.3.5"`.

Guided demo with alert poll:

```bash
make demo
```

Optional full gate for facilitators:

```bash
make validate
```

## Step 2: Redis tampering (vulnerable vs hardened)

Vulnerable mode accepts unsigned session tampering:

```bash
curl -sf -X POST http://localhost:8000/labs/redis/run \
  -H "Content-Type: application/json" -d '{"mode":"vulnerable"}'
```

Expected: `"blocked": false`, summary mentions privilege escalation.

Hardened mode rejects tampering with HMAC verification:

```bash
curl -sf -X POST http://localhost:8000/labs/redis/run \
  -H "Content-Type: application/json" -d '{"mode":"hardened"}'
```

Expected: `"blocked": true`, `"control"` mentions HMAC.

Discussion: Where would unsigned session blobs appear in a real LLM app stack?

## Step 3: Prompt cache isolation (vulnerable vs hardened)

Vulnerable mode uses a shared cache key:

```bash
curl -sf -X POST http://localhost:8000/labs/prompt-cache-isolation/run \
  -H "Content-Type: application/json" -d '{"mode":"vulnerable"}'
```

Hardened mode uses tenant-scoped namespaces in live Redis:

```bash
curl -sf -X POST http://localhost:8000/labs/prompt-cache-isolation/run \
  -H "Content-Type: application/json" -d '{"mode":"hardened"}'
```

Expected: vulnerable allows cross-tenant bleed; hardened blocks it.

Discussion: Why is cache key design an authorization boundary, not just a performance detail?

## Step 4: Trigger a circuit breaker alert

Clear prior webhook deliveries:

```bash
curl -sf -X DELETE http://localhost:8081/alerts
```

Run hardened circuit breaker (default load exceeds safe capacity):

```bash
curl -sf -X POST http://localhost:8000/labs/circuit-breaker/run \
  -H "Content-Type: application/json" -d '{"mode":"hardened"}'
```

Check the metric:

```bash
curl -sf http://localhost:8000/metrics | grep boundary_layer_inference_circuit_breaker_state
```

Expected: gauge value `1` (open).

## Step 5: Inspect Prometheus metrics

```bash
curl -sf http://localhost:8000/metrics | grep boundary_layer_ | head -20
```

Open Prometheus UI at http://localhost:9090 and confirm the API scrape target is up.

Discussion: Which metrics would you wire into a real on-call runbook?

## Step 6: Inspect Alertmanager webhook delivery

Wait up to 60 seconds for Alertmanager to route the alert, then:

```bash
curl -sf http://localhost:8081/alerts
```

Expected: `"count"` greater than zero and alert name `BoundaryLayerInferenceCircuitBreakerOpen`.

Optional: run hardened authz and confirm alert delivery (included in `make validate-alerts`):

```bash
curl -sf -X DELETE http://localhost:8081/alerts
curl -sf -X POST http://localhost:8000/labs/authz/run \
  -H "Content-Type: application/json" -d '{"mode":"hardened"}'
curl -sf http://localhost:8000/metrics | grep boundary_layer_authz_denied_total
# Wait up to 60 seconds
curl -sf http://localhost:8081/alerts
```

Expected alert name: `BoundaryLayerAuthzDenied`.

## Discussion questions

1. Which lab best represents a failure you have seen or worry about in production-like systems?
2. What is the difference between blocking in application code vs detecting in metrics/alerts?
3. Why is the default dev stack intentionally unauthenticated?
4. What would you need before calling the production-like profile "ready for your environment"?
5. What does BoundaryLayer **not** simulate (real LLM APIs, real file parsers, external paging)?

## Cleanup

```bash
make down
```

## Related docs

- Quick demo: `make demo` or [DEMO.md](DEMO.md)
- Sample JSON: [EXAMPLES.md](EXAMPLES.md)
- Observability: [OBSERVABILITY_WALKTHROUGH.md](OBSERVABILITY_WALKTHROUGH.md)
- Troubleshooting: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- Controls and alert mapping: [CONTROLS_MAP.md](CONTROLS_MAP.md)
- Production-like profile (controlled local machines only): [PRODUCTION.md](PRODUCTION.md)
