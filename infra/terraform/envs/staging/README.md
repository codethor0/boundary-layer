# Staging Environment

This folder documents the intended **staging** environment for Production SaaS.

## Required runtime profile

- `BOUNDARY_LAYER_PROFILE=production-saas`
- `BOUNDARY_LAYER_ENV=staging`
- `BOUNDARY_LAYER_AUTH_PROVIDER=oidc` (not `oidc-test`)

## Readiness gate

Run locally without cloud credentials:

```bash
make production-saas-staging-readiness-example
```

Run against your shell environment (expects NOT READY until real values are set):

```bash
make production-saas-staging-readiness-check
```

## Not included

- Applied Terraform
- Live OIDC tenant registration
- Managed service endpoints
- Deploy pipeline execution
