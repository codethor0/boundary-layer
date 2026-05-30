# BoundaryLayer Demo Walkthrough

This walkthrough runs entirely on your machine. It uses synthetic lab data, does not call external LLM APIs, and does not send alerts to external on-call systems.

## Prerequisites

- Python 3.12+
- Docker and Docker Compose
- `curl`

## 1. Quick setup

```bash
git clone https://github.com/codethor0/boundary-layer.git
cd boundary-layer
make setup
```

Copy `.env.example` to `.env` only if you need local overrides. Do not commit `.env`.

## 2. Run the stack

```bash
make up
```

Wait until the API health check succeeds:

```bash
curl -sf http://localhost:8000/health
```

Expected services:

| Service | URL |
|---------|-----|
| API | http://localhost:8000 |
| Alert webhook | http://localhost:8081 |
| Prometheus | http://localhost:9090 |
| Alertmanager | http://localhost:9093 |

## 3. Run one vulnerable lab

Redis State Tampering in vulnerable mode accepts an unsigned session tamper:

```bash
curl -sf -X POST http://localhost:8000/labs/redis/run \
  -H "Content-Type: application/json" \
  -d '{"mode":"vulnerable"}'
```

You should see `"blocked": false` and a summary describing privilege escalation.

## 4. Run one hardened lab

The same lab in hardened mode rejects the tamper:

```bash
curl -sf -X POST http://localhost:8000/labs/redis/run \
  -H "Content-Type: application/json" \
  -d '{"mode":"hardened"}'
```

You should see `"blocked": true` and HMAC verification in the event list.

## 5. View Prometheus metrics

Lab runs increment counters exposed at `/metrics`:

```bash
curl -sf http://localhost:8000/metrics | head -40
```

Look for names such as `boundary_layer_lab_runs_total` and lab-specific counters after your runs.

## 6. Trigger the circuit breaker alert

Clear any prior webhook deliveries:

```bash
curl -sf -X DELETE http://localhost:8081/alerts
```

Run the circuit breaker lab in hardened mode with default load (250 work units exceeds safe capacity):

```bash
curl -sf -X POST http://localhost:8000/labs/circuit-breaker/run \
  -H "Content-Type: application/json" \
  -d '{"mode":"hardened"}'
```

Confirm the circuit breaker metric is open:

```bash
curl -sf http://localhost:8000/metrics | grep boundary_layer_inference_circuit_breaker_state
```

Prometheus evaluates alert rules on a short interval. Wait up to 60 seconds for Alertmanager to route `BoundaryLayerInferenceCircuitBreakerOpen` to the local webhook.

## 7. View the delivered alert in the local webhook

```bash
curl -sf http://localhost:8081/alerts
```

You should see a non-zero `count` and an alert named `BoundaryLayerInferenceCircuitBreakerOpen`.

## 8. Clean up

```bash
make down
```

## Scope notes

- The demo is local-only.
- No external LLM API is called.
- No external alert integration is used.
- All lab inputs and outputs are synthetic.

For compact JSON examples, see [EXAMPLES.md](EXAMPLES.md). For architecture diagrams, see [DIAGRAMS.md](DIAGRAMS.md).
