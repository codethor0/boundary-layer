# Next Steps

BoundaryLayer v1.3.5 remains a **complete local defensive security lab**. Production SaaS Phase 6 adds the **staging provisioning package** (runbooks, secrets inventory, GitHub Environment guide, container build/deploy scripts, live validation package) but **hosted SaaS is not shipped** and live staging was **not validated** unless an operator provisions real infrastructure.

## Immediate priorities (Production SaaS Phase 7)

1. **Provision AWS staging account** — apply IaC; create RDS, ElastiCache, S3, ECR, ECS, WAF per runbook.
2. **Configure GitHub Environment `staging`** — all secrets from inventory.
3. **Deploy staging API** — `staging-deploy` workflow with `DEPLOY_STAGING=true` after review.
4. **Run live validation** — `RUN_LIVE_STAGING_CHECKS=true make live-staging-validation-package`.
5. **Fill live evidence** — `docs/LIVE_STAGING_EVIDENCE_TEMPLATE.md`.
6. **Immutable audit + SIEM** — implement external audit sink adapter.

## Validation commands (Phase 6)

```bash
make production-saas-managed-services-example
make staging-smoke-structural
make staging-release-gate
make container-build
make container-smoke-local
make deploy-staging-dry-run
make waf-readiness-check

# Expected fail without live env:
make live-staging-validation-package

# Live (requires untracked .env.staging or GitHub Environment secrets):
export RUN_LIVE_STAGING_CHECKS=true
make live-staging-validation-package
```

Manual CI: `.github/workflows/staging-deploy.yml`, `.github/workflows/staging-live-validation.yml`.

## Do not do yet

- Do not claim Production SaaS readiness without live staging evidence.
- Do not run `terraform apply` or destructive cloud commands without operator review.
- Do not commit `.env.staging` or cloud credentials.

## Recommended next surgical prompt

**BoundaryLayer Production SaaS Phase 7 — Staging Account Apply and Live Evidence Capture**

## References

- [docs/STAGING_DEPLOYMENT_RUNBOOK.md](docs/STAGING_DEPLOYMENT_RUNBOOK.md)
- [docs/STAGING_SECRETS_INVENTORY.md](docs/STAGING_SECRETS_INVENTORY.md)
- [docs/GITHUB_ENVIRONMENT_SETUP.md](docs/GITHUB_ENVIRONMENT_SETUP.md)
- [docs/PRODUCTION_SAAS_READINESS.md](docs/PRODUCTION_SAAS_READINESS.md)
