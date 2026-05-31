# WAF and Abuse Controls Plan

BoundaryLayer does **not** ship edge WAF, bot management, or tenant abuse controls today. Production-like local validation includes Redis-backed rate limiting, but that is **not** a substitute for edge protection in hosted Production SaaS.

## Current state

| Control | Status |
|---------|--------|
| Application rate limiting | Partial (production-like profile) |
| Per-tenant concurrency/rate config | Config validated (`TENANT_CONCURRENCY_LIMIT`, `TENANT_RATE_LIMIT_PER_MINUTE`) |
| Edge WAF | Not implemented |
| Bot management | Not implemented |
| Abuse alerting | Config scaffolding only |
| Payload/file size limits | Partial (production-saas request body guard) |
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

These fields are documented and validated structurally where safe. In-app request body size enforcement applies in production-saas when `MAX_REQUEST_BODY_BYTES > 0`. True WAF enforcement must happen at the edge; in-app controls are secondary.

## AWS WAF setup (default staging provider)

Recommended for AWS ECS/Fargate + ALB staging path:

1. Create **AWS WAF web ACL** (regional) attached to staging ALB.
2. Enable **AWS Managed Rules** baseline (Core rule set, Known bad inputs).
3. Add **rate-based rule** per IP (e.g. 2000 requests / 5 min) as coarse edge limit.
4. Add **size constraint** rule matching `MAX_REQUEST_BODY_BYTES` at edge where supported.
5. Enable **AWS Bot Control** (optional cost) for signup/login paths when UI exists.
6. Configure **geo match** only if product policy requires blocking.
7. Export WAF logs to S3 or CloudWatch for abuse investigations.
8. Set `WAF_ENABLED=true` in staging env; run `make waf-readiness-check`.

### Tenant-level abuse policy (application)

- `TENANT_RATE_LIMIT_PER_MINUTE` — per-tenant app limiter (secondary to edge)
- `TENANT_CONCURRENCY_LIMIT` — cap concurrent lab runs per tenant
- `ABUSE_ALERTING_ENABLED` — route Prometheus abuse metrics to on-call (future)

### Validation

```bash
make waf-readiness-check
```

Structural pass verifies docs and config fields. Live WAF resource check runs only when `aws` CLI and `AWS_WAF_WEB_ACL_*` variables are configured.

## Runbook outline (future)

1. Detect abuse signal (rate limit spike, WAF block surge, audit anomaly).
2. Identify tenant/user from request context and audit events.
3. Apply temporary tenant throttle or suspension.
4. Rotate affected credentials via secret manager.
5. Notify on-call and document incident timeline.
6. Post-incident review and control tuning.

## Score note

WAF/abuse controls remain **P0 blockers** for Production SaaS 10/10. Config scaffolding alone does not improve operational readiness.
