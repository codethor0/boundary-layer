# Next Steps

BoundaryLayer v1.3.5 remains a **complete local defensive security lab**. Production SaaS Phase 4 adds managed-service adapter interfaces and staging deployment proof scripts but **hosted SaaS is not shipped**.

## Immediate priorities (Production SaaS Phase 5)

1. **Apply IaC to a staging account** — provision managed Postgres, Redis, object storage, secret manager, VPC.
2. **Deploy staging environment** — container service with live OIDC provider and smoke tests.
3. **Validate live managed-service connectivity** — run `RUN_LIVE_STAGING_CHECKS=true` against real endpoints.
4. **Implement immutable audit sink** — see [docs/AUDIT_SIEM_PLAN.md](docs/AUDIT_SIEM_PLAN.md).
5. **Enable edge WAF/abuse controls** — see [docs/WAF_ABUSE_CONTROLS.md](docs/WAF_ABUSE_CONTROLS.md).
6. **CI/CD staging deploy pipeline** — automated deploy + smoke with GitHub Environment secrets.

## Validation commands (Phase 4)

```bash
make production-saas-managed-services-check    # expects NOT READY locally
make production-saas-managed-services-example  # STRUCTURALLY READY (mocked)
make staging-deploy-dry-run                    # dry run only (requires env)
make staging-release-gate                      # strict gate; smoke optional
```

## Do not do yet

- Do not expose `docker-compose.yml` to the public internet.
- Do not claim Production SaaS readiness in README or release notes.
- Do not remove vulnerable lab modes from local-lab profile.
- Do not run `terraform apply` from the skeleton without a reviewed staging plan.

## Recommended next surgical prompt

**BoundaryLayer Production SaaS Phase 5 — Live Staging Deploy and Managed Service Validation**

## References

- [docs/PRODUCTION_SAAS_READINESS.md](docs/PRODUCTION_SAAS_READINESS.md)
- [docs/AUDIT_SIEM_PLAN.md](docs/AUDIT_SIEM_PLAN.md)
- [docs/WAF_ABUSE_CONTROLS.md](docs/WAF_ABUSE_CONTROLS.md)
- [infra/README.md](infra/README.md)
- [docs/CI_CD_PRODUCTION_PLAN.md](docs/CI_CD_PRODUCTION_PLAN.md)
