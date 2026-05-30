# Redis State Tampering Lab

Demonstrates session privilege escalation via unsigned Redis session blobs.

## Modes

- **vulnerable**: Base64-encoded JSON sessions in live Redis accept tampered role elevation.
- **hardened**: HMAC verification rejects modified session payloads read from Redis.

## Live Redis Mode

When `BOUNDARY_LAYER_REDIS_LIVE=true` (default in Docker Compose):

- Connects to `REDIS_HOST` / `REDIS_PORT` / `REDIS_DB`
- Uses keys under `boundary_layer:lab:redis:`
- Applies TTLs to lab keys

When `BOUNDARY_LAYER_REDIS_LIVE=false`:

- Uses deterministic in-memory fallback for local tests

## Validation

```bash
curl -X POST http://localhost:8000/labs/redis/run \
  -H "Content-Type: application/json" \
  -d '{"mode":"vulnerable"}'

curl -X POST http://localhost:8000/labs/redis/run \
  -H "Content-Type: application/json" \
  -d '{"mode":"hardened"}'

curl -sf http://localhost:8000/metrics | grep boundary_layer_redis_tamper_rejected_total
```

## Risk

Session privilege escalation via predictable or unsigned cache state.

## Control

HMAC session integrity verification with live Redis state reads.
