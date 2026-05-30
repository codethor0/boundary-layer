# Terminal Output Examples

Representative API responses from a local BoundaryLayer stack. Values are sanitized and truncated for readability. These are not validation transcripts.

## GET /health

```bash
curl -sf http://localhost:8000/health
```

```json
{
  "status": "ok",
  "service": "boundary-layer-api",
  "version": "1.0.8"
}
```

## GET /labs

```bash
curl -sf http://localhost:8000/labs
```

```json
{
  "labs": [
    {
      "id": "tool-router",
      "name": "Tool Router Injection Lab",
      "path": "/labs/tool-router/run",
      "description": "Poisoned retrieved content influences simulated tool requests."
    },
    {
      "id": "redis",
      "name": "Redis State Tampering Lab",
      "path": "/labs/redis/run",
      "description": "Predictable or unsigned session values can be modified."
    }
  ]
}
```

The live response lists all nine labs. Output above shows the first two entries only.

## Redis vulnerable mode

```bash
curl -sf -X POST http://localhost:8000/labs/redis/run \
  -H "Content-Type: application/json" \
  -d '{"mode":"vulnerable"}'
```

```json
{
  "lab": "redis",
  "mode": "vulnerable",
  "blocked": false,
  "risk": "redis_state_tampering",
  "control": "none",
  "events": [
    "Stored unsigned session blob",
    "Tampered session role from viewer to admin",
    "Accepted tampered session; privilege escalation succeeded"
  ],
  "summary": "Vulnerable mode accepted a tampered session blob; role escalated from viewer to admin."
}
```

## Redis hardened mode

```bash
curl -sf -X POST http://localhost:8000/labs/redis/run \
  -H "Content-Type: application/json" \
  -d '{"mode":"hardened"}'
```

```json
{
  "lab": "redis",
  "mode": "hardened",
  "blocked": true,
  "risk": "redis_state_tampering",
  "control": "hmac_session_integrity",
  "events": [
    "Stored HMAC-signed session token: eyJ1c2VyIjogImRlbW8i...",
    "Rejected tampered session; HMAC verification failed"
  ],
  "summary": "Hardened mode rejected tampered session; privilege escalation blocked."
}
```

## Circuit breaker hardened mode

Default request load is 250 work units. Safe capacity is 100, so the breaker opens and work is shed.

```bash
curl -sf -X POST http://localhost:8000/labs/circuit-breaker/run \
  -H "Content-Type: application/json" \
  -d '{"mode":"hardened"}'
```

```json
{
  "lab": "circuit-breaker",
  "mode": "hardened",
  "blocked": true,
  "risk": "inference_backpressure",
  "control": "capacity_limit_and_circuit_breaker",
  "events": [
    "Requested work units: 250",
    "Safe capacity: 100",
    "Circuit breaker opened; shedding excess work"
  ],
  "summary": "Hardened mode accepted 100 work units, shed 150, circuit breaker state open."
}
```

## Prompt cache vulnerable mode

```bash
curl -sf -X POST http://localhost:8000/labs/prompt-cache-isolation/run \
  -H "Content-Type: application/json" \
  -d '{"mode":"vulnerable"}'
```

```json
{
  "lab": "prompt-cache-isolation",
  "mode": "vulnerable",
  "blocked": false,
  "risk": "prompt_cache_cross_tenant_bleed",
  "control": "none",
  "events": [
    "Tenant A wrote shared cache entry",
    "Tenant B lookup hit Tenant A cache entry"
  ],
  "summary": "Vulnerable mode allowed Tenant B to hit Tenant A's shared prompt cache entry."
}
```

## Prompt cache hardened mode

```bash
curl -sf -X POST http://localhost:8000/labs/prompt-cache-isolation/run \
  -H "Content-Type: application/json" \
  -d '{"mode":"hardened"}'
```

```json
{
  "lab": "prompt-cache-isolation",
  "mode": "hardened",
  "blocked": true,
  "risk": "prompt_cache_cross_tenant_bleed",
  "control": "tenant_scoped_cache_keys",
  "events": [
    "Tenant A wrote tenant-scoped cache entry",
    "Tenant B lookup used isolated namespace; no cross-tenant hit"
  ],
  "summary": "Hardened mode prevented cross-tenant prompt cache bleed using tenant namespaces."
}
```

## Alert webhook output

After clearing the store and triggering the circuit breaker alert path:

```bash
curl -sf -X DELETE http://localhost:8081/alerts
curl -sf http://localhost:8081/alerts
```

Empty store:

```json
{
  "count": 0,
  "alerts": []
}
```

After Prometheus and Alertmanager route a firing alert (may take up to 60 seconds):

```json
{
  "count": 1,
  "alerts": [
    {
      "status": "firing",
      "labels": {
        "alertname": "BoundaryLayerInferenceCircuitBreakerOpen",
        "severity": "warning"
      },
      "annotations": {
        "summary": "Inference circuit breaker is open"
      }
    }
  ]
}
```

Label and annotation text may vary slightly with Prometheus rule evaluation timing.

For live Docker verification commands, see [E2E_VALIDATION.md](E2E_VALIDATION.md).
