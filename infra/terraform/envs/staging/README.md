# Staging Environment

This folder documents the intended **staging** environment for Production SaaS.

See [docs/STAGING_ENVIRONMENT_CONTRACT.md](../../../docs/STAGING_ENVIRONMENT_CONTRACT.md) for the full variable contract.

## Required runtime profile

- `BOUNDARY_LAYER_PROFILE=production-saas`
- `BOUNDARY_LAYER_ENV=staging`
- `BOUNDARY_LAYER_AUTH_PROVIDER=oidc` (not `oidc-test`)

## Readiness gates

Structural (no cloud credentials):

```bash
make production-saas-staging-readiness-example
make production-saas-managed-services-example
make staging-smoke-structural
make staging-release-gate
```

Live (requires untracked `.env.staging` or GitHub Environment secrets):

```bash
export RUN_LIVE_STAGING_CHECKS=true
make production-saas-managed-services-live-check
make staging-smoke-live
```

Manual CI workflow: `.github/workflows/staging-live-validation.yml` (`workflow_dispatch`, `environment: staging`).

## IaC (plan only)

```bash
make infra-validate
CONFIRM_STAGING_PLAN=true make infra-plan-staging
```

Never run `terraform apply` without reviewed plan and staging account isolation.

## Not included

- Applied Terraform
- Live OIDC tenant registration (unless configured externally)
- Verified managed service endpoints (unless live checks enabled)
- Automated production deploy pipeline
