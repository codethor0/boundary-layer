# Next Steps

BoundaryLayer v1.3.5 local lab: **ready**. Production SaaS: **6/10** (capped until live staging evidence exists).

## Phase 7 result: LIVE STAGING BLOCKED

Live validation did not run. Missing:

1. Untracked local `.env.staging` **or** GitHub Environment `staging` (environment does not exist yet — HTTP 404)
2. All managed-service, OIDC, and staging smoke variables listed in `make check-live-staging-prereqs` output

## Exact next commands (when credentials exist)

```bash
# 1. Create GitHub Environment "staging" and add secrets per docs/STAGING_SECRETS_INVENTORY.md
#    OR create untracked .env.staging locally (never commit)

# 2. Verify prerequisites (names only, no secret values printed)
export RUN_LIVE_STAGING_CHECKS=true
# source .env.staging  # if using local file
make check-live-staging-prereqs

# 3. Run full evidence chain
make production-saas-evidence-runner

# 4. Fill docs/LIVE_STAGING_EVIDENCE_TEMPLATE.md from sanitized output
```

Manual CI: `.github/workflows/production-saas-live-validation.yml` (requires GitHub Environment `staging`).

## AWS staging provisioning (prerequisite)

Follow `docs/STAGING_DEPLOYMENT_RUNBOOK.md`:

1. Create staging AWS account resources (RDS, ElastiCache, S3, ECR, ECS, WAF)
2. Configure OIDC provider and issue tenant A/B test JWTs
3. Create GitHub Environment `staging` with all secrets
4. Deploy via `staging-deploy` workflow with reviewer approval

## Recommended next prompt

**BoundaryLayer Production SaaS Phase 8 — Provision Staging AWS Account and Run Live Evidence Runner**

## References

- [docs/PRODUCTION_10_10_EVIDENCE_MATRIX.md](docs/PRODUCTION_10_10_EVIDENCE_MATRIX.md)
- [docs/GITHUB_ENVIRONMENT_SETUP.md](docs/GITHUB_ENVIRONMENT_SETUP.md)
- [docs/STAGING_SECRETS_INVENTORY.md](docs/STAGING_SECRETS_INVENTORY.md)
- [artifacts/live-evidence/LIVE_STAGING_EVIDENCE.md](artifacts/live-evidence/LIVE_STAGING_EVIDENCE.md) (local, gitignored)
