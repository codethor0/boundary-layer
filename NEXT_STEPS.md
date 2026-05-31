# Next Steps

BoundaryLayer v1.3.5 remains a **complete local defensive security lab**. Production SaaS Phase 3 adds staging-readiness scaffolding but **hosted SaaS is not shipped**.

## Immediate priorities (Production SaaS Phase 4)

1. **Apply IaC to a staging account** — managed Postgres, Redis, object storage, secret manager, private networking.
2. **Register live OIDC provider for staging** — Auth0/Clerk/Cognito with RS256/JWKS; retire `oidc-test` outside unit tests.
3. **Implement cloud storage adapter** — S3/GCS/R2 behind `StorageBackend` with presigned uploads.
4. **Implement secret manager adapter** — AWS/GCP/Azure/Doppler/Vault lookup with rotation hooks.
5. **Deploy staging environment** — container service + CI deploy gate + smoke against live endpoints.
6. **Immutable audit pipeline** — append-only retention and SIEM export.

## Validation commands (Phase 3)

```bash
make production-saas-staging-readiness-check    # expects NOT READY locally
make production-saas-staging-readiness-example  # mocked structural pass
```

## Do not do yet

- Do not expose `docker-compose.yml` to the public internet.
- Do not claim Production SaaS readiness in README or release notes.
- Do not remove vulnerable lab modes from local-lab profile.
- Do not run `terraform apply` from the skeleton without a reviewed staging plan.

## Recommended next surgical prompt

**BoundaryLayer Production SaaS Phase 4 — Live Staging Deploy and Managed Service Adapters**

## References

- [docs/PRODUCTION_SAAS_READINESS.md](docs/PRODUCTION_SAAS_READINESS.md)
- [infra/README.md](infra/README.md)
- [docs/CI_CD_PRODUCTION_PLAN.md](docs/CI_CD_PRODUCTION_PLAN.md)
