# Deployment Architecture

Target architecture for hosted Production SaaS. **Not deployed today.**

> **Note:** `docker-compose.yml` is for local lab use only, not public hosting.

## Recommended path (Phase 1)

Managed PaaS or container service with minimal moving parts:

```text
Internet -> WAF/CDN -> HTTPS LB -> API containers -> Private VPC
                                              |-> Managed PostgreSQL
                                              |-> Managed Redis
                                              |-> Object storage (S3/GCS/R2)
                                              |-> Secret manager
```

## Components

| Layer | Recommendation |
|-------|----------------|
| API | FastAPI container, non-root, read-only root FS where possible |
| Database | Managed PostgreSQL, TLS, PITR, automated backups |
| Cache | Managed Redis, TLS, AUTH enabled |
| Files | S3/GCS/R2; no local disk for uploads |
| Secrets | AWS Secrets Manager, GCP Secret Manager, or Vault |
| TLS | Terminate at load balancer; optional mTLS internal |
| Networking | Private subnets for data stores; no public DB ports |

## Container build

- Multi-stage Dockerfile (already non-root in BoundaryLayer).
- Pin base image digests in production pipeline.
- Scan images in CI (Trivy) before deploy.

## CI/CD gates (see CI_CD_PRODUCTION_PLAN.md)

1. Unit + integration tests
2. Secret scan, dependency scan, container scan, SBOM
3. Production config check (`make production-saas-check` with real env in CI secrets)
4. Staging deploy + smoke test
5. Manual approval for production
6. Post-deploy smoke + rollback artifact retained

## Database migrations

- Alembic migrations run as init job or deploy hook.
- Backward-compatible migrations only for zero-downtime deploys.
- Never run `docker compose down -v` in production.

## Health and readiness

- `/health` — liveness (no auth)
- `/ready` — Postgres + Redis checks (auth in hardened profiles)
- Load balancer uses both endpoints.

## Backup and restore

- Managed DB automated backups + PITR.
- Object storage versioning/lifecycle rules.
- Quarterly restore drill documented in runbook.

## Monitoring and alert routing

- OpenTelemetry traces and structured logs.
- Prometheus-compatible metrics (existing lab metrics as foundation).
- Alert routing to on-call (PagerDuty/Opsgenie), not local webhook only.

## Rollbacks

- Keep previous container image tag.
- Database migrations must support rollback or forward-fix plan.
- One-click rollback in PaaS or GitOps revert.

## Cost controls

- Budget alerts per environment.
- Autoscaling min/max caps.
- Review idle staging resources weekly.

## Environment separation

| Environment | Purpose |
|-------------|---------|
| local-lab | Developer machine, compose stack |
| staging | Pre-prod integration, synthetic data only |
| production | Customer data, strict change control |

Never share secrets or databases across environments.
