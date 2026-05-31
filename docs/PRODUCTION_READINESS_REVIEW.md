# Production Readiness Review

**Status:** Template only. All approvals default to **unchecked**. Do not mark approved without evidence.

## System overview

BoundaryLayer is a defensive AI infrastructure security lab with an optional `production-saas` profile for future hosted multi-tenant deployment. Local lab remains the supported product mode.

## Architecture

See [DEPLOYMENT_ARCHITECTURE.md](DEPLOYMENT_ARCHITECTURE.md), [STAGING_DEPLOYMENT_RUNBOOK.md](STAGING_DEPLOYMENT_RUNBOOK.md).

## Data flows

Tenant JWT -> API auth middleware -> tenant context -> lab handlers -> Postgres/Redis/object storage (tenant-scoped).

## Auth/tenant model

OIDC JWT with tenant and roles claims. Cross-tenant denial with audit. See [AUTH_TENANCY_DESIGN.md](AUTH_TENANCY_DESIGN.md).

## Threat model

See [THREAT_MODEL.md](THREAT_MODEL.md).

## Secrets

GitHub Environment `staging` + cloud secret manager. Never commit `.env.staging`.

## Managed services

RDS PostgreSQL, ElastiCache Redis, S3, Secrets Manager (staging target). Live proof via `make production-saas-evidence-runner`.

## WAF/edge

AWS WAF on ALB (target). Live proof via `make waf-live-check`.

## Audit/SIEM

Postgres audit foundation; external immutable sink required for 10/10. See [AUDIT_SIEM_PLAN.md](AUDIT_SIEM_PLAN.md).

## DR/backup

See [DR_ONCALL_RUNBOOK.md](DR_ONCALL_RUNBOOK.md). DR live check: `CONFIRM_STAGING_DR_TEST=true make dr-restore-live-check`.

## On-call

Not configured in repository. Required for 9/10+.

## SLOs

Not defined. Required for 9/10+.

## Compliance

See [LEGAL_COMPLIANCE_READINESS.md](LEGAL_COMPLIANCE_READINESS.md). Legal review required for 10/10.

## Open risks

- **Phase 7 (2026-05-31):** Live staging blocked — no `.env.staging`, GitHub Environment `staging` missing, all managed-service/OIDC secrets absent
- Live staging not validated until evidence runner passes
- Immutable audit/SIEM not live
- WAF edge not enforced without cloud config
- Legal artifacts missing

## Go/no-go decision

| Decision | Status |
|----------|--------|
| Go to staging live validation | Pending credentials |
| Go to production | **No** |

## Approval checklist

| Approval | Status | Evidence location |
|----------|--------|-------------------|
| Engineering | [ ] | `artifacts/live-evidence/LIVE_STAGING_EVIDENCE.md` |
| Security | [ ] | pip-audit, container scan, WAF/audit live checks |
| Operations | [ ] | DR/on-call drills |
| Legal | [ ] | Legal compliance checklist |
| Founder/product | [ ] | Production readiness review meeting notes |

See [PRODUCTION_10_10_EVIDENCE_MATRIX.md](PRODUCTION_10_10_EVIDENCE_MATRIX.md) for full gap list.
