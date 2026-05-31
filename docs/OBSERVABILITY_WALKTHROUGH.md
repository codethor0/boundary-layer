# Observability Walkthrough

Blue-team guide for Prometheus, Alertmanager, and the local alert webhook in BoundaryLayer.

**Prerequisites:** `make up` (dev stack). Allow **15–60 seconds** for scrape and alert evaluation after triggering a lab.

## 1. Health checks

```bash
curl -sf http://localhost:9090/-/healthy
curl -sf http://localhost:9093/-/healthy
curl -sf http://localhost:8081/health
curl -sf http://localhost:8000/health
```

Expected: Prometheus and Alertmanager return plain `Prometheus Server is Healthy.` / `OK`; webhook returns JSON with `"status":"ok"`.

## 2. Open Prometheus

Browser: http://localhost:9090

Confirm target `api:8000` (or `localhost:8000`) is **UP** under Status → Targets.

## 3. Query a metric

In the Graph tab, try:

```promql
boundary_layer_lab_runs_total
increase(boundary_layer_authz_denied_total[5m])
increase(boundary_layer_redis_tamper_rejected_total[5m])
boundary_layer_sse_active_streams
boundary_layer_inference_circuit_breaker_state
```

Or from the terminal:

```bash
curl -sf http://localhost:8000/metrics | grep boundary_layer_lab_runs_total
```

## 4. Trigger circuit breaker alert

Clear prior webhook deliveries:

```bash
curl -sf -X DELETE http://localhost:8081/alerts
```

Run hardened circuit breaker (default load opens the breaker):

```bash
curl -sf -X POST http://localhost:8000/labs/circuit-breaker/run \
  -H "Content-Type: application/json" \
  -d '{"mode":"hardened"}'
```

Confirm gauge:

```bash
curl -sf http://localhost:8000/metrics | grep boundary_layer_inference_circuit_breaker_state
```

Expected: value `1`.

## 5. Inspect Alertmanager

Browser: http://localhost:9093

After 15–60 seconds, the alert `BoundaryLayerInferenceCircuitBreakerOpen` should appear under Alerts (firing) if routing is healthy.

## 6. Inspect local webhook

```bash
curl -sf http://localhost:8081/alerts
```

Expected excerpt:

```json
{"count":1,"alerts":[{"labels":{"alertname":"BoundaryLayerInferenceCircuitBreakerOpen"}}]}
```

## 7. Clear webhook alerts

```bash
curl -sf -X DELETE http://localhost:8081/alerts
curl -sf http://localhost:8081/alerts
```

Expected: `"count":0` or empty alerts array.

## 8. Authz alert (extended)

```bash
curl -sf -X DELETE http://localhost:8081/alerts
curl -sf -X POST http://localhost:8000/labs/authz/run \
  -H "Content-Type: application/json" -d '{"mode":"hardened"}'
curl -sf http://localhost:8000/metrics | grep boundary_layer_authz_denied_total
# Wait up to 60 seconds
curl -sf http://localhost:8081/alerts
```

Expected alert name: `BoundaryLayerAuthzDenied`.

Run `make validate-alerts` to automate circuit breaker and authz delivery checks.

## Troubleshooting: alert does not appear

1. **Wait longer** — first scrape plus rule evaluation can take up to 60 seconds.
2. **Check Prometheus rules** — http://localhost:9090/rules — confirm `BoundaryLayerInferenceCircuitBreakerOpen` is loaded.
3. **Check metric first** — if `boundary_layer_inference_circuit_breaker_state` is not `1`, the lab did not open the breaker; re-run hardened mode.
4. **Check Alertmanager config** — http://localhost:9093/#/status — receiver should point to `alert-webhook:8080`.
5. **Webhook logs:**

```bash
docker compose logs alert-webhook --tail=100
docker compose logs prometheus --tail=100
docker compose logs alertmanager --tail=100
```

6. **Stack not running** — `make up` then `make smoke`.

## One-command paths

| Command | Purpose |
|---------|---------|
| `make smoke` | Fast sanity check |
| `make demo` | Guided demo with alert poll |
| `make validate-alerts` | Circuit breaker + authz alert delivery |
| `make validate` | Full local validation gate |

## Related

- [METRICS.md](METRICS.md)
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- [WORKSHOP.md](WORKSHOP.md)
