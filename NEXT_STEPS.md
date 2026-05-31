# Next Steps

BoundaryLayer v1.3.5 remains a **complete local defensive security lab**. Production SaaS Phase 5 adds live staging validation **gates** (structural default, live explicitly gated) but **hosted SaaS is not shipped** and live staging was **not validated** in this pass.

## Immediate priorities (Production SaaS Phase 6)

1. **Provision staging account** — apply IaC to real staging with remote state and locking.
2. **Deploy staging API** — container service with live OIDC and protected GitHub Environment secrets.
3. **Run live validation** — `RUN_LIVE_STAGING_CHECKS=true` managed-service checks + staging HTTP smoke.
4. **Immutable audit sink** — implement external `AUDIT_SINK_PROVIDER` adapter and SIEM export.
5. **Edge WAF enforcement** — enable managed WAF/rate limits at load balancer/CDN.
6. **CI/CD staging deploy** — automated deploy job with live smoke and rollback metadata.

## Validation commands (Phase 5)

```bash
make production-saas-managed-services-example  # STRUCTURALLY READY (mocked)
make staging-smoke-structural                  # no remote calls
make staging-release-gate                      # LOCAL + STRUCTURAL PASS; LIVE SKIPPED by default
make infra-validate
make container-image-check

# Live (requires untracked .env.staging or GitHub Environment secrets)
export RUN_LIVE_STAGING_CHECKS=true
make production-saas-managed-services-live-check
make staging-smoke-live
```

Manual CI: `.github/workflows/staging-live-validation.yml` (`workflow_dispatch`, `environment: staging`).

## Do not do yet

- Do not expose `docker-compose.yml` to the public internet.
- Do not claim Production SaaS readiness in README or release notes.
- Do not remove vulnerable lab modes from local-lab profile.
- Do not run `terraform apply` without reviewed plan and staging account isolation.
- Do not claim live staging pass when `RUN_LIVE_STAGING_CHECKS` is unset.

## Recommended next surgical prompt

**BoundaryLayer Production SaaS Phase 6 — Staging Account Provisioning and Live Deploy Pipeline**

## References

- [docs/PRODUCTION_SAAS_READINESS.md](docs/PRODUCTION_SAAS_READINESS.md)
- [docs/STAGING_ENVIRONMENT_CONTRACT.md](docs/STAGING_ENVIRONMENT_CONTRACT.md)
- [docs/AUDIT_SIEM_PLAN.md](docs/AUDIT_SIEM_PLAN.md)
- [docs/WAF_ABUSE_CONTROLS.md](docs/WAF_ABUSE_CONTROLS.md)
- [docs/CONTAINER_RELEASE.md](docs/CONTAINER_RELEASE.md)
- [infra/README.md](infra/README.md)
- [docs/CI_CD_PRODUCTION_PLAN.md](docs/CI_CD_PRODUCTION_PLAN.md)
