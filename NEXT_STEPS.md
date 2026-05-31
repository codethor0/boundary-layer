# Next Steps

BoundaryLayer v1.3.5 is a **complete local defensive security lab** with a published GitHub release. Production SaaS Phase 1 adds auth/tenancy scaffolding but **hosted SaaS is not shipped**.

## Immediate priorities (Production SaaS Phase 2)

1. **Tenant-scope all lab tables and queries** — add `tenant_id` to lab persistence paths; Alembic migration behind `production-saas` profile.
2. **Wire live OIDC provider in staging** — Auth0/Clerk/Cognito with RS256/JWKS; keep `oidc-test` for unit tests only.
3. **Extend audit logging** — lab run events, admin actions, immutable retention policy.
4. **Terraform staging environment** — managed Postgres, Redis, secret manager, private networking.
5. **Extend CI** — `make production-saas-auth-smoke` gate + membership integration tests against Compose Postgres.
6. **Object storage backend** — S3/GCS/R2 adapter for file-upload lab in production-saas.

## Do not do yet

- Do not expose `docker-compose.yml` to the public internet.
- Do not claim Production SaaS readiness in README or release notes.
- Do not remove vulnerable lab modes from local-lab profile.
- Do not add billing until tenant isolation is proven on all tables.

## Recommended next surgical prompt

**BoundaryLayer Production SaaS Phase 2 — Tenant-Scoped Lab Data and Staging OIDC**

Scope: migrate lab tables to tenant-scoped schema, extend cross-tenant denial tests to all labs, add staging OIDC integration — without breaking `make validate` on `local-lab` profile.

## References

- [docs/PRODUCTION_SAAS_READINESS.md](docs/PRODUCTION_SAAS_READINESS.md)
- [docs/AUTH_TENANCY_DESIGN.md](docs/AUTH_TENANCY_DESIGN.md)
- [docs/SAAS_SECURITY_CHECKLIST.md](docs/SAAS_SECURITY_CHECKLIST.md)
