# Staging Environment Contract

This document defines the contract for a valid BoundaryLayer **staging** environment used by structural and live validation gates.

BoundaryLayer separates three validation states:

1. **Local lab validation** — default Docker Compose stack; no cloud credentials.
2. **Structural staging readiness** — configuration and policy checks only; no network calls to managed services or staging API.
3. **Live staging validation** — explicit connectivity and HTTP smoke tests; requires real endpoints and secrets.

**Never commit real values.** Use an untracked local `.env.staging` file or GitHub Environment / CI secret store. Do not paste tokens into documentation or commits.

## Required variables

| Variable | Purpose | Example placeholder | Secret | Structural | Live |
|----------|---------|---------------------|--------|------------|------|
| `STAGING_BASE_URL` | Public staging API base URL | `https://staging.example.com` | No | Yes | Yes |
| `STAGING_HEALTH_URL` | Optional explicit health URL | `https://staging.example.com/health` | No | Optional | Optional |
| `STAGING_METRICS_URL` | Optional explicit metrics URL | `https://staging.example.com/metrics` | No | Optional | Optional |
| `STAGING_TEST_ACCESS_TOKEN_TENANT_A` | Bearer JWT for tenant A smoke tests | `staging-test-token-tenant-a-minimum-24` | **Yes** | Yes | Yes |
| `STAGING_TEST_ACCESS_TOKEN_TENANT_B` | Bearer JWT for cross-tenant denial test | `staging-test-token-tenant-b-minimum-24` | **Yes** | Optional | Optional |
| `STAGING_METRICS_AUTH_TOKEN` | Metrics bearer token | `staging-metrics-token-minimum-24` | **Yes** | Yes | Yes |
| `OIDC_ISSUER_URL` | OIDC issuer (HTTPS) | `https://staging-issuer.example.com` | No | Yes | Yes |
| `OIDC_AUDIENCE` | API audience | `boundary-layer-api-staging` | No | Yes | Yes |
| `OIDC_JWKS_URL` | JWKS document URL (HTTPS) | `https://staging-issuer.example.com/.well-known/jwks.json` | No | Yes | Yes |
| `OIDC_TENANT_CLAIM` | Tenant ID claim name | `https://boundarylayer.dev/tenant_id` | No | Yes | Yes |
| `OIDC_ROLES_CLAIM` | Roles claim name | `https://boundarylayer.dev/roles` | No | Yes | Yes |
| `DATABASE_URL` | Managed PostgreSQL URL with SSL | `postgresql://user:***@db.staging.example:5432/db?sslmode=require` | **Yes** | Yes | Yes |
| `REDIS_URL` | Managed Redis TLS URL | `rediss://:***@redis.staging.example:6379/0` | **Yes** | Yes | Yes |
| `REDIS_KEY_PREFIX` | Tenant Redis namespace prefix | `boundary_layer:tenant` | No | Yes | Yes |
| `OBJECT_STORAGE_BUCKET` | Object storage bucket | `boundary-layer-staging-artifacts` | No | Yes | Yes |
| `OBJECT_STORAGE_REGION` | Object storage region | `us-east-1` | No | Yes | Yes |
| `OBJECT_STORAGE_PREFIX` | Tenant object prefix | `tenants/` | No | Yes | Yes |
| `SECRET_MANAGER_PROVIDER` | Secret manager backend | `aws` | No | Yes | Yes |
| `SECRET_MANAGER_PROJECT_OR_PATH` | Secret manager path/project | `boundary-layer/staging` | No | Yes | Yes |
| `SECRET_ROTATION_REQUIRED` | Rotation policy flag | `true` | No | Yes | Yes |
| `SECRET_CACHE_TTL_SECONDS` | Secret cache TTL | `300` | No | Yes | Yes |
| `BOUNDARY_LAYER_HEALTHCHECK_SECRET_NAME` | Non-sensitive health-check secret name | `boundary-layer/healthcheck` | No | Optional | Yes |
| `BOUNDARY_LAYER_PUBLIC_BASE_URL` | Public app URL (HTTPS) | `https://staging.example.com` | No | Yes | Yes |
| `BOUNDARY_LAYER_ALLOWED_ORIGINS` | CORS allowlist | `https://staging.example.com` | No | Yes | Yes |
| `BOUNDARY_LAYER_METRICS_TOKEN` | Metrics auth token | `production-metrics-token-minimum-24` | **Yes** | Yes | Yes |
| `BOUNDARY_LAYER_AUDIT_LOG_ENABLED` | Audit logging enabled | `true` | No | Yes | Yes |
| `AUDIT_SINK_PROVIDER` | Audit sink target | `postgres` | No | Yes | Yes |
| `WAF_ENABLED` | Edge WAF expected | `true` | No | Optional | Optional |
| `RUN_LIVE_STAGING_CHECKS` | Enable live connectivity checks | `true` | No | No | **Required** |

## Validation rules (summary)

- All OIDC and public URLs must use `https://`.
- `DATABASE_URL` must require SSL (`sslmode=require` or `DB_SSL_MODE=require`).
- `REDIS_URL` must use `rediss://`.
- Wildcard CORS origins are rejected in production-saas/staging.
- Localhost/container managed-service hosts are rejected unless explicitly overridden for tests.
- Live checks run **only** when `RUN_LIVE_STAGING_CHECKS=true`.

## Local usage

```bash
# Structural only (no cloud/network required beyond examples)
make production-saas-staging-readiness-example
make production-saas-managed-services-example
make staging-smoke-structural

# Live (requires untracked .env.staging with real values)
set -a && source .env.staging && set +a
export RUN_LIVE_STAGING_CHECKS=true
make production-saas-managed-services-live-check
make staging-smoke-live
```

## CI usage

Use GitHub Environment `staging` with protected secrets. Run workflow:

`.github/workflows/staging-live-validation.yml` (manual `workflow_dispatch` only).

If staging secrets are not configured, workflows must report **LIVE STAGING CHECKS SKIPPED** and must not claim live validation passed.

## Score impact

If live staging checks are skipped, Production SaaS score must not exceed **6/10**. Live checks must pass against real infrastructure before score may move to **7/10** or **8/10**.
