# Red Team Playbook

Safe local-only test scenarios for BoundaryLayer v1.3.5. Run only against your local Docker stack.

## Prerequisites

```bash
make up
curl -sf http://localhost:8000/health
```

## Scenario 1: Retrieval Poisoning

Objective: Route tool execution to a destructive action via poisoned context.

```bash
curl -X POST http://localhost:8000/labs/tool-router/run \
  -H "Content-Type: application/json" \
  -d '{"mode":"vulnerable"}'
```

Expected: `blocked: false`, summary references destructive tool.

Hardened retest:

```bash
curl -X POST http://localhost:8000/labs/tool-router/run \
  -H "Content-Type: application/json" \
  -d '{"mode":"hardened"}'
```

Expected: `blocked: true`, injection pattern detected.

## Scenario 2: Redis Session Tampering

Objective: Escalate role by replacing session blob.

Run vulnerable then hardened modes via `POST /labs/redis/run`. Compare `blocked` and `events` fields.

## Scenario 3: Token Scope Bypass

Objective: Access restricted PII export with basic read scope.

Run `POST /labs/authz/run` with both modes. Hardened mode should deny with tenant/scope reason.

## Scenario 4: Document Instruction Injection

Objective: Inject SYSTEM directive via uploaded file extraction.

Run `POST /labs/file-upload/run` in both modes. v0.9 adds sandbox, egress, active content, and wrapping simulation:

```bash
curl -X POST http://localhost:8000/labs/file-upload/run \
  -H "Content-Type: application/json" \
  -d '{"mode":"vulnerable"}'

curl -X POST http://localhost:8000/labs/file-upload/run \
  -H "Content-Type: application/json" \
  -d '{"mode":"hardened"}'

curl -sf http://localhost:8000/metrics | grep boundary_layer_file_upload
```

Expected: vulnerable allows direct context insertion; hardened blocks risky defaults and emits sandbox metrics.

## Scenario 5: Incomplete Prompt Deletion

Objective: Delete prompt while leaving training/eval artifacts.

Run `POST /labs/governance/run` in both modes. Hardened mode should produce audit evidence.

## Scenario 6: PostgreSQL Write Storm

Objective: Demonstrate write-path pressure from uncontrolled prompt logging inserts.

```bash
curl -X POST http://localhost:8000/labs/postgres-write-storm/run \
  -H "Content-Type: application/json" \
  -d '{"mode":"vulnerable"}'

curl -X POST http://localhost:8000/labs/postgres-write-storm/run \
  -H "Content-Type: application/json" \
  -d '{"mode":"hardened"}'

curl -sf http://localhost:8000/metrics | grep boundary_layer_postgres_write_storm
```

Expected: vulnerable inserts full batch; hardened blocks excess writes and emits mitigation metrics.

## Scenario 7: Inference Circuit Breaker

Objective: Demonstrate cascading risk from unbounded synthetic inference work.

```bash
curl -X POST http://localhost:8000/labs/circuit-breaker/run \
  -H "Content-Type: application/json" \
  -d '{"mode":"vulnerable"}'

curl -X POST http://localhost:8000/labs/circuit-breaker/run \
  -H "Content-Type: application/json" \
  -d '{"mode":"hardened"}'

curl -sf http://localhost:8000/metrics | grep boundary_layer_inference
```

Expected: vulnerable accepts all work; hardened sheds excess and opens circuit breaker.

## Scenario 8: SSE Stream Exhaustion

Objective: Demonstrate worker and memory pressure from unbounded synthetic SSE streams.

```bash
curl -X POST http://localhost:8000/labs/sse-exhaustion/run \
  -H "Content-Type: application/json" \
  -d '{"mode":"vulnerable"}'

curl -X POST http://localhost:8000/labs/sse-exhaustion/run \
  -H "Content-Type: application/json" \
  -d '{"mode":"hardened"}'

curl -sf http://localhost:8000/metrics | grep boundary_layer_sse
```

Expected: vulnerable accepts all streams with orphaned stream metrics; hardened rejects excess and applies cleanup.

## Scenario 9: Prompt Cache Cross-Tenant Bleed

Objective: Demonstrate cross-tenant prompt-prefix cache bleed and tenant namespace isolation.

```bash
curl -X POST http://localhost:8000/labs/prompt-cache-isolation/run \
  -H "Content-Type: application/json" \
  -d '{"mode":"vulnerable"}'

curl -X POST http://localhost:8000/labs/prompt-cache-isolation/run \
  -H "Content-Type: application/json" \
  -d '{"mode":"hardened"}'

curl -sf http://localhost:8000/metrics | grep boundary_layer_prompt_cache
```

Expected: vulnerable records cross-tenant cache hit and bleed metric; hardened applies tenant-scoped keys and isolation metric.

## Scenario 10: Alert Delivery Validation

Objective: Confirm Prometheus alert routing through Alertmanager to the local webhook.

```bash
curl -sf -X DELETE http://localhost:8081/alerts

curl -X POST http://localhost:8000/labs/circuit-breaker/run \
  -H "Content-Type: application/json" \
  -d '{"mode":"hardened"}'

curl -sf http://localhost:8081/alerts
```

Expected: webhook receives `BoundaryLayerInferenceCircuitBreakerOpen` after Prometheus evaluation.

## Safety Rules

- Local Docker targets only
- No external systems
- No real credentials
- Document findings in your own notes; do not commit unsanitized transcripts
