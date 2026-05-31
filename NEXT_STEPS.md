# Next Steps

BoundaryLayer v1.3.5 is a **complete local defensive security lab** with a published GitHub release. Production SaaS Phase 2 adds tenant-scoped lab data paths and cross-tenant denial tests but **hosted SaaS is not shipped**.

## Immediate priorities (Production SaaS Phase 3)

1. **Wire live OIDC provider in staging** — Auth0/Clerk/Cognito with RS256/JWKS; keep `oidc-test` for unit tests only.
2. **Terraform staging environment** — managed Postgres, Redis, secret manager, private networking.
3. **Immutable audit pipeline** — append-only retention, SIEM export, admin action coverage.
4. **Object storage backend** — S3/GCS/R2 adapter for file-upload lab in production-saas.
5. **Extend CI** — staging deploy gate + membership integration tests against managed Postgres.
6. **WAF and abuse controls** — edge rate limits, account lockout, CAPTCHA at signup.

## Do not do yet

- Do not expose `docker-compose.yml` to the public internet.
- Do not claim Production SaaS readiness in README or release notes.
- Do not remove vulnerable lab modes from local-lab profile.
- Do not add billing until staging OIDC and managed services are validated.

## Recommended next surgical prompt

**BoundaryLayer Production SaaS Phase 3 — Staging OIDC and Managed Service Integration**

Scope: live OIDC in staging, managed Postgres/Redis wiring, secret manager references, and deploy pipeline smoke — without breaking `make validate` on `local-lab` profile.

## References

- [docs/PRODUCTION_SAAS_READINESS.md](docs/PRODUCTION_SAAS_READINESS.md)
- [docs/AUTH_TENANCY_DESIGN.md](docs/AUTH_TENANCY_DESIGN.md)
- [docs/SAAS_SECURITY_CHECKLIST.md](docs/SAAS_SECURITY_CHECKLIST.md)
