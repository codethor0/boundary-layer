# GitHub Environment Setup

Configure GitHub Environment **`staging`** for manual staging deploy and live validation workflows.

## Create the environment

1. Repository **Settings** -> **Environments** -> **New environment**
2. Name: `staging`
3. Enable **Required reviewers** (recommended: 1–2 operators)
4. Optional: restrict deployment branches to `main` only
5. Optional: add wait timer before deploy jobs run

## Required secrets

Add each secret from [STAGING_SECRETS_INVENTORY.md](STAGING_SECRETS_INVENTORY.md). Minimum set for live validation:

- `DATABASE_URL`
- `REDIS_URL`
- `BOUNDARY_LAYER_SECRET_KEY`
- `BOUNDARY_LAYER_METRICS_TOKEN`
- `BOUNDARY_LAYER_ALLOWED_ORIGINS`
- `BOUNDARY_LAYER_PUBLIC_BASE_URL`
- `OIDC_ISSUER_URL`, `OIDC_AUDIENCE`, `OIDC_JWKS_URL`, `OIDC_TENANT_CLAIM`, `OIDC_ROLES_CLAIM`
- `SECRET_MANAGER_PROVIDER`, `SECRET_MANAGER_PROJECT_OR_PATH`
- `OBJECT_STORAGE_BUCKET`, `OBJECT_STORAGE_REGION`
- `STAGING_BASE_URL`
- `STAGING_TEST_ACCESS_TOKEN_TENANT_A`
- `STAGING_METRICS_AUTH_TOKEN`
- `BOUNDARY_LAYER_API_KEY`, `POSTGRES_PASSWORD`, `REDIS_PASSWORD`, `SESSION_HMAC_SECRET`

Optional: `STAGING_TEST_ACCESS_TOKEN_TENANT_B`, `STAGING_ALERT_WEBHOOK_URL`, `CONTAINER_REGISTRY`.

## Required variables (non-secret)

Use Environment **variables** where possible:

| Variable | Value |
|----------|-------|
| `DEPLOY_STAGING` | `false` (set `true` only for intentional deploy) |
| `BOUNDARY_LAYER_PROFILE` | `production-saas` |
| `BOUNDARY_LAYER_ENV` | `staging` |

## Branch protection recommendation

- Require PR review before merge to `main`
- Require status checks: CI, staging-readiness
- Block force-push to `main`

## Manual approval recommendation

Enable environment protection so **Staging Deploy** and **Staging Live Validation** require reviewer approval before secrets are exposed to the job.

## Run staging-live-validation workflow

1. Ensure all secrets above are configured
2. Actions -> **Staging Live Validation** -> **Run workflow**
3. Workflow runs on `environment: staging`
4. Structural checks always run; live checks run when `DATABASE_URL` and `STAGING_BASE_URL` secrets exist

## Run staging-deploy workflow

1. Default: dry run only (`DEPLOY_STAGING` not true)
2. For deploy attempt: set `DEPLOY_STAGING=true` in environment variables **and** obtain reviewer approval
3. Workflow runs test, lint, container build/smoke, structural checks, then deploy placeholder or dry run

## Read failure logs safely

- GitHub masks secret values in logs when stored as Secrets
- Do not `echo` secret env vars in custom scripts
- Use `PASS`/`FAIL` lines without printing token values
- Download logs only to secure operator storage

## Rotate secrets

1. Generate new value in IdP/cloud console
2. Update GitHub Environment secret
3. Redeploy or restart staging service if runtime caches secrets
4. Re-run `make live-staging-validation-package`
5. Document rotation in operator notes (not in repo)

## Checklists

### Before live run

- [ ] Staging account provisioned per [STAGING_DEPLOYMENT_RUNBOOK.md](STAGING_DEPLOYMENT_RUNBOOK.md)
- [ ] All required GitHub secrets populated
- [ ] OIDC test tokens issued for tenant A (and B for cross-tenant test)
- [ ] `DEPLOY_STAGING=false` unless intentional deploy
- [ ] Operator available for rollback

### During live run

- [ ] Monitor workflow job without copying secrets from logs
- [ ] Confirm structural steps pass before live steps
- [ ] Stop on first `FAIL` and capture job URL

### After live run

- [ ] Fill [LIVE_STAGING_EVIDENCE_TEMPLATE.md](LIVE_STAGING_EVIDENCE_TEMPLATE.md)
- [ ] Update score only if `LIVE STAGING VALIDATION PASS`
- [ ] Revoke temporary operator credentials if used

### If live run fails

- [ ] Identify failing step (managed services vs HTTP smoke)
- [ ] Verify secret names match inventory (not values in chat)
- [ ] Check staging service health and OIDC issuer status
- [ ] Re-run after fix; do not claim pass until full package passes
