# Demo Assets Plan

BoundaryLayer does not ship terminal GIFs or README screenshots yet. This document defines how to capture them for GitHub discovery without faking assets.

## Recommended capture flow (asciinema)

Install [asciinema](https://asciinema.org/) locally. Record on a clean terminal with the dev stack running.

Suggested sequence:

```bash
# Terminal 1 — start stack
make up

# Terminal 2 — record
asciinema rec boundary-layer-demo.cast
make smoke
make demo
# Optional: show Prometheus query in browser (describe verbally or cut separate clip)
exit
```

Upload to asciinema.org or convert to GIF with `agg` / `svg-term`.

## Recommended terminal GIF shots

| # | Command / action | Caption |
|---|------------------|---------|
| 1 | `make up` + health curl | "Start the local defensive lab stack" |
| 2 | `make smoke` | "Fast sanity check in under a minute" |
| 3 | `make demo` | "Redis, cache isolation, and circuit breaker alert" |
| 4 | Browser Prometheus query `boundary_layer_inference_circuit_breaker_state` | "Metrics exposed for blue-team runbooks" |
| 5 | `curl http://localhost:8081/alerts` after demo | "Local Alertmanager delivery without external paging" |

## Recommended README screenshots

When captured, place files under:

```
docs/assets/
  demo-smoke.png
  demo-make-demo.png
  prometheus-circuit-breaker.png
  alert-webhook.png
```

Reference from README only **after files exist**. Until then, README states:

> Screenshots/GIFs are planned. See docs/DEMO_ASSETS.md for capture flow.

## Exact commands for alert webhook shot

```bash
curl -sf -X DELETE http://localhost:8081/alerts
curl -sf -X POST http://localhost:8000/labs/circuit-breaker/run \
  -H "Content-Type: application/json" -d '{"mode":"hardened"}'
sleep 30
curl -sf http://localhost:8081/alerts | python3 -m json.tool
```

Expected alert name in output: `BoundaryLayerInferenceCircuitBreakerOpen`.

## Prometheus query examples for screenshots

```promql
boundary_layer_inference_circuit_breaker_state
increase(boundary_layer_authz_denied_total[5m])
increase(boundary_layer_redis_tamper_rejected_total[5m])
boundary_layer_sse_active_streams
```

Open http://localhost:9090/graph and capture the graph panel.

## Do not

- Add placeholder image files that look like real screenshots
- Reference nonexistent images in README
- Commit private prompts or unsanitized transcripts in asset folders

## Related

- [WORKSHOP.md](WORKSHOP.md)
- [OBSERVABILITY_WALKTHROUGH.md](OBSERVABILITY_WALKTHROUGH.md)
- [DEMO.md](DEMO.md)
