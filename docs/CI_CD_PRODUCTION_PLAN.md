# CI/CD Production Plan

Required pipeline for hosted Production SaaS. **Deploy stages are not implemented in v1.3.5.**

## Current CI (implemented)

| Job | Workflow | Status |
|-----|----------|--------|
| Unit tests + lint | CI | Done |
| Secret scan on tracked source | CI | Done |
| pip-audit | Security Scan | Done |
| Hadolint | Security Scan | Done |
| Trivy container scan | Security Scan | Done |
| Production-like validate | Production Validate | Done |

## Required for Production SaaS (not implemented)

| Stage | Purpose | Gate |
|-------|---------|------|
| Unit tests | Fast feedback | Block on fail |
| Integration tests | Postgres/Redis/API flows | Block on fail |
| Docker build | Reproducible artifact | Block on fail |
| Secret scan | Leaked credentials | Block on fail |
| Dependency scan | CVEs in requirements | Block on fail |
| Container scan | Image CVEs | Block on policy |
| SBOM generation | Supply chain audit | Artifact upload |
| IaC scan | Terraform misconfig | Block on critical |
| Migration check | Alembic dry-run against staging schema | Block on fail |
| Production config check | `make production-saas-check` with staging secrets | Block if NOT READY |
| Staging deploy | Auto on main after gates | Smoke test follows |
| Staging smoke test | Health, ready, auth, one lab | Block on fail |
| Manual production approval | Human reviewer | Required |
| Production deploy | Tagged release only | Audit logged |
| Post-deploy smoke test | Same as staging smoke | Rollback on fail |
| Rollback plan | Previous image + migration strategy | Documented runbook |

## Suggested workflow layout

```text
PR -> test/lint/scan -> merge main -> build image -> deploy staging -> smoke
                                                      -> manual approve -> deploy prod -> smoke
```

## Local commands mapped to future gates

| Local today | Future CI equivalent |
|-------------|---------------------|
| `make test` | Unit tests job |
| `make validate-prod` | Staging smoke subset |
| `make production-saas-check` | Production config gate |
| `make validate` | Extended integration (lab only) |

## Secrets in CI

- Store staging/production secrets in GitHub Environments.
- Never echo secrets in logs.
- Rotate on compromise.

## Not in scope yet

- Blue/green or canary deploy automation
- Multi-region failover
- Customer-facing status page automation

See [PRODUCTION_SAAS_READINESS.md](PRODUCTION_SAAS_READINESS.md) for priority order.
