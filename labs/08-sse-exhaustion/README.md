# SSE Exhaustion Simulation Lab

Lab ID: `sse-exhaustion`

Endpoint: `POST /labs/sse-exhaustion/run`

## What this lab demonstrates

This lab simulates how unbounded server-sent event streams can exhaust workers, connections, or memory when there are no stream caps, idle timeouts, or cleanup controls. It maps to Gap 7 from the BoundaryLayer article: SSE stream exhaustion.

## Safety and scope

- This lab does not open real long-running streams.
- This lab does not create real socket exhaustion.
- This lab does not attempt to crash the API.
- It uses deterministic synthetic stream units only.
- This lab is local-only and defensive.

## Modes

### Vulnerable

Accepts all requested streams (default 250) with no cap, idle timeout, or cleanup. Simulates orphaned streams, worker pressure, and memory pressure. Returns `blocked: false`.

### Hardened

Applies tenant stream cap (50), idle timeout (30s), and cleanup. Rejects excess streams when requested count exceeds the cap. Returns `blocked: true` when excess streams are rejected.

Optional request fields:

```json
{
  "mode": "hardened",
  "requested_streams": 250,
  "stream_duration_seconds": 120
}
```

## Metrics

- `boundary_layer_sse_streams_total{mode,result}`
- `boundary_layer_sse_rejected_streams_total{mode}`
- `boundary_layer_sse_active_streams{mode}`
- `boundary_layer_sse_orphaned_streams{mode}`
- `boundary_layer_sse_worker_pressure{mode}`
- `boundary_layer_sse_memory_pressure_mb{mode}`
- `boundary_layer_sse_cleanup_applied_total{mode}`

## Alerts

- `BoundaryLayerSSEStreamExhaustionDetected`
- `BoundaryLayerSSEOrphanedStreamsDetected`
- `BoundaryLayerSSEBackpressureTriggered`
- `BoundaryLayerSSECleanupApplied`

## What this lab does not simulate

- Real SSE socket connections or HTTP keep-alive exhaustion
- Actual worker thread pool saturation
- Production memory allocator behavior
- CDN or edge proxy stream limits
