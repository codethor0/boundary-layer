# Threat Model

## Assets

- User session state (Redis)
- Authorization tokens and scopes
- Retrieved and uploaded content
- Tool routing decisions
- Prompt lifecycle records (requests, logs, tools, eval/training queues)
- Audit and governance evidence
- Lab metrics and detection telemetry
- Local alert webhook delivery evidence

## Trust Boundaries

- External content (retrieval, uploads) vs trusted system instructions
- Authenticated identity vs authorized action (scope/tenant)
- Client-visible session tokens vs server-side integrity verification
- Primary prompt records vs downstream derived artifacts
- Metrics exposition vs operational monitoring consumers
- Alertmanager routing vs external on-call systems

## Threat Actors

- External attacker injecting instructions via documents or retrieval poisoning
- Authenticated user attempting horizontal privilege escalation
- Insider tampering with cache session state
- Operator performing incomplete data deletion
- Red team simulating post-compromise blast radius expansion

## Attack Paths

1. Poison retrieval -> influence tool router -> invoke destructive tool
2. Tamper unsigned Redis session -> escalate role
3. Reuse broad token -> access tenant-restricted PII export
4. Upload malicious PDF text -> inject SYSTEM directives into context
5. Delete prompt primary record only -> leave eval/training artifacts
6. Runaway prompt logging -> saturate PostgreSQL write path
7. Unbounded inference requests -> cascade through queue and error rate
8. Unbounded SSE streams -> exhaust workers and memory
9. Shared prompt cache keys -> cross-tenant cache bleed

## Controls

| Path | Control |
|------|---------|
| Tool injection | Instruction-pattern detection, execution block |
| Redis tampering | HMAC session integrity |
| Flat authz | Scope and tenant enforcement |
| File injection | Sandbox policy, egress blocking, active content detection, untrusted wrapping |
| Governance gap | Downstream audit and cascade deletion |
| Write storm | Tenant write budget and backpressure |
| Inference cascade | Circuit breaker and load shedding |
| SSE exhaustion | Tenant stream cap, idle timeout, and cleanup |
| Prompt cache bleed | Per-tenant cache namespace isolation |

See [CONTROLS_MAP.md](CONTROLS_MAP.md) for lab-level mapping.
