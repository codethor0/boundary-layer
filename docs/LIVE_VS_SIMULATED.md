# Live vs Simulated Labs

BoundaryLayer is a **local defensive AI infrastructure security lab**. Labs mix live infrastructure where it teaches real boundary failures and deterministic simulation where live behavior would be unsafe, slow, or non-repeatable.

See also the compact table in [README.md](../README.md#live-vs-simulated-labs).

## Mock LLM

The stack includes a deterministic **mock LLM** service (`mock-llm:8080`) for demos and extension points. **Most lab runners do not call it directly.** Live labs use Redis and PostgreSQL. In-process labs stay deterministic and safe. This is intentional.

## Lab matrix

| Lab | Live infrastructure | Simulation type | Key metrics | Alert coverage | Why safe | What it does not simulate |
|-----|---------------------|-----------------|-------------|----------------|----------|----------------------------|
| Tool Router Injection | None | Deterministic in-process | `boundary_layer_tool_injection_blocked_total` | `BoundaryLayerToolInjectionBlockedSpike` | No external tools or network calls | Real vector DB retrieval poisoning at scale |
| Redis State Tampering | Live Redis (+ fallback) | Tampered blob replay | `boundary_layer_redis_tamper_rejected_total` | `BoundaryLayerRedisTamperRejected` | Namespaced keys; local Redis only | Full session store compromise of a production cluster |
| Flat AuthN/AuthZ | None | Deterministic in-process | `boundary_layer_authz_denied_total` | `BoundaryLayerAuthzDenied` | Synthetic tokens and tools only | OAuth/OIDC provider bugs, JWT algorithm confusion |
| File Upload Injection | None | Metadata/content simulation | `boundary_layer_file_upload_*` | File upload alert family | No real file parsers or malware execution | Antivirus, sandbox VMs, polyglot files |
| Prompt Governance | Live PostgreSQL (+ fallback) | Synthetic deletion audit | `boundary_layer_prompt_deletion_orphan_records_total` | `BoundaryLayerPromptDeletionIncomplete` | Bounded tables; local DB | Enterprise DLP, legal hold workflows |
| PostgreSQL Write Storm | Live PostgreSQL | Bounded synthetic inserts | `boundary_layer_postgres_write_storm_*` | Write storm alert pair | Caps on event count and rate | Unbounded production logging pipelines |
| Circuit Breaker | None | Synthetic work units | `boundary_layer_inference_circuit_breaker_state` | Circuit breaker alert family | No real GPU/LLM inference | Provider rate limits, autoscaling lag |
| SSE Exhaustion | None | Synthetic stream units | `boundary_layer_sse_*` | SSE alert family | No real long-lived sockets | CDN edge disconnect storms |
| Prompt Cache Isolation | Live Redis (+ fallback) | Synthetic tenant prefixes | `boundary_layer_prompt_cache_*` | Prompt cache alert pair | Namespaced keys; local Redis | Global CDN cache poisoning |

## How to read “partially live”

When a lab lists **live Redis or PostgreSQL plus fallback**, the API attempts live infrastructure first. If the service is unreachable, the lab falls back to an in-process path so workshops still complete. Metrics and JSON shape stay consistent; event text may note fallback usage.

## Validation expectations

- `make smoke` — fast sanity check including one live Redis pair.
- `make demo` — Redis, prompt cache, and circuit breaker alert path.
- `make validate` — full gate including extended alert delivery (`make validate-alerts`).

For blue-team observability steps, see [OBSERVABILITY_WALKTHROUGH.md](OBSERVABILITY_WALKTHROUGH.md).
