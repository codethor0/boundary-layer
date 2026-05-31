# Live Staging Evidence Template

Fill this document **after** a successful live staging validation run. Store completed copies in secure operator storage (not in the public repo).

**Do not include real secrets, passwords, or JWT values.**

Copy `.env.staging.example` to untracked `.env.staging` before local live runs. See `docs/PHASE_8_OPERATOR_RUNBOOK.md`.

## Deployment metadata

| Field | Value |
|-------|-------|
| Deployment timestamp (UTC) | |
| Git commit | |
| Container image digest | |
| Container image tag | |
| Cloud provider | |
| Operator who validated | |
| Evidence links (CI run URL, internal ticket) | |

## Endpoints (redacted where sensitive)

| Field | Value |
|-------|-------|
| STAGING_BASE_URL | |
| OIDC issuer URL | |
| Managed Postgres endpoint class | e.g. `*.rds.amazonaws.com` (hostname redacted) |
| Managed Redis endpoint class | e.g. `*.cache.amazonaws.com` (redacted) |
| Object storage bucket | redacted or prefix only |
| Secret manager provider | |
| WAF / edge | e.g. AWS WAF on ALB — Yes/No |

## Check results

| Check | Result (PASS/FAIL/SKIP) | Notes |
|-------|-------------------------|-------|
| Health `GET /health` | | |
| Auth smoke `GET /labs` with Bearer | | |
| Redis lab POST | | |
| Tenant-sensitive lab POST | | |
| Metrics with token | | |
| Unauthenticated `/labs` expects 401 | | |
| Invalid token expects 401 | | |
| Cross-tenant expects 403 (if tenant B token configured) | | |
| Managed PostgreSQL live check | | |
| Managed Redis live check | | |
| Object storage live check | | |
| Secret manager live check | | |
| JWKS live check | | |
| Alert endpoint (if configured) | | |
| WAF readiness | | |

## Rollback

| Field | Value |
|-------|-------|
| Rollback tested | Yes / No |
| Previous image digest | |
| Rollback procedure reference | |

## Known failures

List any skipped or failed checks and remediation plan.

## Sign-off

| Role | Name | Date |
|------|------|------|
| Operator | | |
| Reviewer | | |

Score impact: live evidence with all critical checks **PASS** may support Production SaaS **7/10** or **8/10**. Without this evidence, score remains capped at **6/10**.
