# WAF and Abuse Controls Plan

BoundaryLayer does **not** ship edge WAF, bot management, or tenant abuse controls today. Production-like local validation includes Redis-backed rate limiting, but that is **not** a substitute for edge protection in hosted Production SaaS.

## Current state

| Control | Status |
|---------|--------|
| Application rate limiting | Partial (production-like profile) |
| Tenant-scoped rate limits | Config scaffolding only |
| Edge WAF | Not implemented |
| Bot management | Not implemented |
| Abuse alerting | Config scaffolding only |
| Payload/file size limits | Config scaffolding only |
| Upload malware scanning | Not implemented |

## Target controls

### Edge

- Managed WAF (AWS WAF, Cloudflare, GCP Cloud Armor, Azure Front Door WAF)
- IP reputation and geo blocking where appropriate
- Bot detection and challenge for signup/login surfaces (future UI)
- TLS termination and HTTP strict transport security

### Application

- Per-tenant quotas and concurrency caps
- Per-user rate limits on authenticated routes
- Request body size limits (`MAX_REQUEST_BODY_BYTES`)
- File upload size limits (`MAX_FILE_UPLOAD_BYTES`)
- Virus/malware scanning pipeline for object storage uploads

### Alerting

- Abuse detection metrics and alerts (`ABUSE_ALERTING_ENABLED`)
- On-call routing for sustained abuse or credential stuffing patterns
- Runbook for tenant suspension and key rotation

## Configuration scaffolding

```bash
WAF_ENABLED=true
TENANT_RATE_LIMIT_REQUIRED=true
ABUSE_ALERTING_ENABLED=true
MAX_REQUEST_BODY_BYTES=1048576
MAX_FILE_UPLOAD_BYTES=5242880
```

These fields are documented and validated structurally where safe. Runtime enforcement is **not** fully implemented in this pass.

## Runbook outline (future)

1. Detect abuse signal (rate limit spike, WAF block surge, audit anomaly).
2. Identify tenant/user from request context and audit events.
3. Apply temporary tenant throttle or suspension.
4. Rotate affected credentials via secret manager.
5. Notify on-call and document incident timeline.
6. Post-incident review and control tuning.

## Score note

WAF/abuse controls remain **P0 blockers** for Production SaaS 10/10. Config scaffolding alone does not improve operational readiness.
