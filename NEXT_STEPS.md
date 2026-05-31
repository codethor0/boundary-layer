# Next Steps

BoundaryLayer v1.3.5 is a **complete local defensive security lab** with a published GitHub release. Production SaaS is **not shipped**.

## Immediate priorities (Production SaaS foundation)

1. **Implement OIDC authentication middleware** — JWT validation, user provisioning, no change to local-lab profile behavior.
2. **Add tenant and membership tables** — Alembic migration behind `production-saas` profile only; see [docs/TENANCY_DATA_MODEL.md](docs/TENANCY_DATA_MODEL.md).
3. **Tenant-scope Redis and future object storage keys** — namespace helper used by labs when profile is production-saas.
4. **Terraform staging environment** — managed Postgres, Redis, secret manager, private networking; see [docs/DEPLOYMENT_ARCHITECTURE.md](docs/DEPLOYMENT_ARCHITECTURE.md).
5. **Audit log writer** — append-only table + structured events for lab runs and admin actions.
6. **Extend CI with production-saas-check gate** — fail PR if mocked example check regresses.

## Do not do yet

- Do not expose `docker-compose.yml` to the public internet.
- Do not claim Production SaaS readiness in README or release notes.
- Do not remove vulnerable lab modes from local-lab profile.
- Do not add billing until auth and tenancy are proven.

## Recommended next surgical prompt

**BoundaryLayer Production SaaS Phase 1 — OIDC Auth and Tenant Schema Implementation**

Scope: implement JWT middleware, tenant/membership models, cross-tenant denial tests, and staging-only deploy — without breaking `make validate` on local-lab profile.

## References

- [docs/PRODUCTION_SAAS_READINESS.md](docs/PRODUCTION_SAAS_READINESS.md)
- [docs/AUTH_TENANCY_DESIGN.md](docs/AUTH_TENANCY_DESIGN.md)
- [docs/SAAS_SECURITY_CHECKLIST.md](docs/SAAS_SECURITY_CHECKLIST.md)
