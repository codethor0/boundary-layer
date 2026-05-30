# Prompt Cache Isolation Lab

Lab ID: `prompt-cache-isolation`

Endpoint: `POST /labs/prompt-cache-isolation/run`

## What this lab demonstrates

This lab simulates how shared prompt-prefix cache keys can create cross-tenant exposure risk when tenant identity is omitted from cache keys. It maps to the preventive architecture section of the BoundaryLayer security model: cache isolation and side-channel prevention.

## Safety and scope

- This lab does not attempt to reproduce a confirmed production exploit.
- This is a preventive architecture simulation.
- It does not store real prompts; only synthetic prompt prefixes are used.
- This lab is local-only and defensive.

## Modes

### Vulnerable

Tenant A writes a synthetic prompt-prefix cache entry using a global Redis key. Tenant B requests the same prefix and receives a cross-tenant cache hit. Returns `blocked: false`.

### Hardened

Tenant A and Tenant B use tenant-scoped cache keys. Tenant B does not hit Tenant A's entry. Returns `blocked: true`.

Optional request fields:

```json
{
  "mode": "hardened",
  "tenant_a": "tenant-a",
  "tenant_b": "tenant-b",
  "prompt_prefix": "summarize confidential acquisition plan"
}
```

## Redis live mode

When `BOUNDARY_LAYER_REDIS_LIVE=true`, the lab writes and reads keys under `boundary_layer:lab:prompt_cache:` with TTLs in live Docker Redis.

When live mode is disabled, deterministic in-memory fallback is used for unit tests.

When live mode is enabled but Redis is unavailable, the API returns HTTP 503.

## Metrics

- `boundary_layer_prompt_cache_requests_total{mode,tenant,result}`
- `boundary_layer_prompt_cache_hits_total{mode,tenant,hit_type}`
- `boundary_layer_prompt_cache_cross_tenant_bleed_total{mode}`
- `boundary_layer_prompt_cache_isolation_applied_total{mode}`

## Alerts

- `BoundaryLayerPromptCacheCrossTenantBleed`
- `BoundaryLayerPromptCacheIsolationApplied`

## What this lab does not simulate

- Confirmed production cache side-channel exploits
- Real prompt content or PII storage
- Production KV cache implementations such as GPU prefix caches
- Cross-region cache replication behavior
