# Circuit Breaker Simulation Lab

Lab ID: `circuit-breaker`

Endpoint: `POST /labs/circuit-breaker/run`

## What this lab demonstrates

This lab simulates how an inference tier can cascade under load when all synthetic work units are accepted without backpressure, and how a hardened circuit breaker sheds excess work before the platform fails.

## Safety and scope

- This lab does not generate real inference load.
- This lab does not require GPUs.
- It uses deterministic synthetic work units only.
- This lab is local-only and defensive.

## Modes

### Vulnerable

Accepts all requested work units (default 250). No circuit breaker is applied. Queue depth and p99 latency increase deterministically. When work exceeds critical capacity (200), simulated failures are recorded. Returns `blocked: false`.

### Hardened

When requested work exceeds safe capacity (100), opens the circuit breaker, accepts only safe capacity work units, and sheds the excess. Returns `blocked: true` when work is shed. When requested work is within safe capacity, the circuit remains closed and all work is accepted.

Optional request field:

```json
{
  "mode": "hardened",
  "requested_work_units": 250
}
```

## Metrics

- `boundary_layer_inference_circuit_breaker_state` (0=closed, 1=open)
- `boundary_layer_inference_requests_total{mode,result}`
- `boundary_layer_inference_shed_work_units_total{mode}`
- `boundary_layer_inference_simulated_failures_total{mode}`
- `boundary_layer_inference_simulated_queue_depth{mode}`
- `boundary_layer_inference_simulated_p99_latency_ms{mode}`

## Alerts

- `BoundaryLayerInferenceCircuitBreakerOpen` - circuit breaker entered open state
- `BoundaryLayerInferenceQueueDepthHigh` - simulated queue depth exceeded threshold
- `BoundaryLayerInferenceWorkShed` - hardened mode shed excess work units

## What this lab does not simulate

- Real model inference or GPU utilization
- Network partitions or multi-region failover
- Actual queueing systems such as Kafka or Redis streams
- Production SLO burn rates
