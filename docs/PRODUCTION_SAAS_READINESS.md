# Production SaaS Readiness

> **Warning:** BoundaryLayer is currently a local defensive security lab. Do not deploy the development Docker Compose stack directly to the public internet.

## Three operating modes

| Mode | Profile | Purpose |
|------|---------|---------|
| Local defensive lab | `local-lab` (default) | Education, controlled local testing, unauthenticated dev stack |
| Production-like local validation | `production-like` | Auth, TLS, rate limits, fail-closed Redis limiter on a machine you control |
| Real hosted Production SaaS | `production-saas` | Multi-tenant hosted product with OIDC, tenant isolation, managed services, audit, DR |

BoundaryLayer **ships and validates** the first two modes today. **Production SaaS is not shipped.**

## Overall score

| Metric | Before this pass | After this pass |
|--------|------------------|-----------------|
| Production SaaS readiness | **4/10** | **5/10** |

The score improves through Phase 3 staging OIDC configuration validation, JWKS client abstraction, managed-service-ready settings (database, Redis, object storage, secret manager), storage/secrets scaffolds, IaC skeleton, and CI staging-readiness workflow. There is still no live staging deployment, applied IaC, immutable audit/SIEM, WAF, or operational validation.

## Gap audit matrix

| Category | Score | Current state | Gap | Risk | Required work for 10/10 | Priority | Approach |
|----------|-------|---------------|-----|------|-------------------------|----------|----------|
| Authentication | 5/10 | JWT/OIDC middleware, staging OIDC config validation, JWKS client abstraction | No live IdP integration in staging, no user signup | Anonymous access in local-lab only | Full OIDC provider integration + user lifecycle | P0 | Auth0/Clerk/Cognito + FastAPI middleware |
| Authorization | 4/10 | Role claims + membership check + cross-tenant denial with audit in production-saas | No policy engine, no tenant_admin UI | Privilege escalation if misconfigured | Role model + policy enforcement layer | P0 | RBAC middleware + membership table |
| Tenant isolation | 4/10 | Tenant-scoped governance/write-storm Postgres paths, tenant Redis namespaces, request context, cross-tenant tests | Not all synthetic labs persist data; no RLS | Residual bleed if new tables omit tenant_id | Tenant-scoped queries everywhere, RLS optional | P0 | See `TENANCY_DATA_MODEL.md` |
| Session security | 1/10 | Stateless API key only | No browser sessions | Session fixation, theft | Secure cookies, rotation, CSRF if UI added | P1 | HttpOnly Secure SameSite cookies |
| API security | 3/10 | Rate limit + auth in prod-like | No WAF, no mTLS service mesh | Abuse, credential stuffing | WAF, mTLS, schema validation at edge | P0 | Cloud WAF + API gateway |
| Secrets management | 3/10 | Config validation + `apps/api/secrets.py` scaffold | No cloud secret manager adapter | Leaked secrets in images/env | Cloud secret manager SDK + rotation | P0 | AWS SM / GCP SM / Vault |
| Database architecture | 3/10 | Managed-service URL/SSL validation in config | No managed HA, no PITR | Data loss, downtime | Managed Postgres, PITR, private networking | P0 | RDS/Cloud SQL + TLS |
| Cache architecture | 4/10 | Single Compose Redis; tenant-scoped lab keys; `rediss://` validation | No managed Redis, no cluster | Cache loss at scale | Managed Redis with TLS/auth, tenant namespaces | P1 | ElastiCache/Memorystore |
| File/object storage | 2/10 | `apps/api/storage.py` interface + config validation | No real object store adapter | Local disk exposure | S3/GCS/R2 with tenant prefixes | P0 | Presigned URLs + virus scan pipeline |
| Network security | 3/10 | TLS in prod-like nginx profile | No private networking | Public DB/Redis exposure | VPC, private subnets, egress controls | P0 | Private subnets + security groups |
| Deployment architecture | 2/10 | docker-compose prod profile + deployment docs | No hosted orchestration | Manual drift, no rollbacks | Container service or K8s with health gates | P0 | See `DEPLOYMENT_ARCHITECTURE.md` |
| Infrastructure-as-code | 2/10 | `infra/terraform/` skeleton + README | Not applied, no modules | Snowflake infra | IaC for all environments | P0 | Terraform modules per env |
| CI/CD | 5/10 | GitHub Actions test/lint/scan/prod validate + staging-readiness workflow | No staging/prod deploy pipeline | Untested deploys | Staging deploy, smoke, manual prod approval | P0 | See `CI_CD_PRODUCTION_PLAN.md` |
| Observability | 4/10 | Prometheus metrics + local webhook | No centralized logs/traces | Blind spots in prod | OpenTelemetry, log aggregation | P1 | OTel + Grafana/Datadog |
| Alerting | 3/10 | Prometheus rules + Alertmanager placeholder | No on-call routing | Missed incidents | PagerDuty/Opsgenie integration | P1 | Alertmanager receivers |
| Audit logging | 3/10 | `audit_events` table + auth/cross-tenant decision writes + metrics in production-saas | Not immutable, not SIEM-integrated | No forensic trail at scale | Immutable audit log pipeline | P0 | Append-only audit table + SIEM |
| Rate limiting and abuse prevention | 3/10 | Redis/memory limiter in prod-like | No global abuse detection | DoS, brute force | Edge rate limits + account lockout | P0 | WAF + app limiter + CAPTCHA at signup |
| Backup and restore | 4/10 | pg_dump scripts, fresh-volume lab proof | No off-host DR | Volume loss | Automated backups, tested restore | P0 | Managed DB backups + quarterly DR test |
| Disaster recovery | 1/10 | Not implemented | No failover region | Extended outage | Multi-region or warm standby runbook | P2 | DR runbook + RTO/RPO targets |
| Data retention | 1/10 | Not defined | No retention policy | Compliance violation | Retention + deletion workflows | P1 | Policy engine + scheduled purge |
| Privacy and compliance | 1/10 | Not addressed | No DPA/GDPR process | Legal exposure | Privacy policy, data map, DSR process | P1 | Legal review + data inventory |
| Admin operations | 1/10 | None | No admin console | Manual SQL for support | Admin UI + audited actions | P1 | Internal admin app |
| Customer onboarding | 1/10 | None | No signup flow | Cannot acquire tenants | Self-serve or sales-assisted onboarding | P1 | Signup + tenant provisioning |
| Billing and subscriptions | 1/10 | None | No billing | No revenue model | Stripe/similar integration | P2 | Billing webhooks + entitlements |
| Legal terms and policies | 1/10 | MIT license only | No ToS/Privacy Policy for SaaS | Liability | Terms, privacy, acceptable use | P1 | Legal counsel |
| Incident response | 2/10 | SECURITY.md disclosure path | No IR runbook | Slow response | IR plan, severity matrix, comms | P0 | IR doc + tabletop exercises |
| Security testing | 4/10 | Unit tests + cross-tenant isolation tests + CI scans | No DAST, no pen test | Unknown vulns | SAST/DAST, annual pen test | P1 | CI SAST + scheduled DAST |
| Dependency and container scanning | 4/10 | pip-audit, Trivy, Hadolint in CI | No SBOM publish | Supply chain risk | SBOM + policy gates | P1 | Syft/Grype in CI |
| Performance and scaling | 2/10 | Single API container | No autoscaling | Latency under load | HPA, load tests, SLOs | P2 | k6 tests + autoscaling |
| Cost controls | 1/10 | None | No budgets/alerts | Runaway cloud spend | Budget alerts, right-sizing | P2 | Cloud billing alerts |
| Documentation | 5/10 | Strong local lab docs | No SaaS operator/customer docs | Misconfiguration | Runbooks, API docs, SLA docs | P1 | Operator + customer docs |
| Support readiness | 1/10 | None | No support process | User churn | Ticketing, SLA tiers | P2 | Support tooling |

## Recommended Production SaaS Architecture

### Option A: Minimal hosted SaaS on managed PaaS (recommended)

- **Frontend:** optional future UI on static hosting (Cloudflare Pages/Vercel)
- **API:** containerized FastAPI behind HTTPS load balancer (Fly.io, Render, Cloud Run, or ECS Fargate)
- **Auth:** OIDC (Auth0, Clerk, or Cognito)
- **Database:** managed PostgreSQL with PITR and private networking
- **Cache:** managed Redis with TLS and auth
- **Object storage:** S3/GCS/R2 (never local disk)
- **Secrets:** cloud secret manager
- **Observability:** OpenTelemetry + metrics/logs/traces
- **IaC:** Terraform
- **CI/CD:** GitHub Actions with staging gate

Start boring. Add Kubernetes only when PaaS limits are proven.

### Option B: Kubernetes-based SaaS

EKS/GKE/AKS with ingress controller, external secrets, and GitOps. Higher operational cost; choose when multi-service scaling is required.

### Option C: Cloud-native managed services

Maximize managed primitives (Lambda + RDS + ElastiCache + S3). Good for API-light workloads; harder for long-running lab simulations.

## Runtime profiles (implemented)

Set `BOUNDARY_LAYER_PROFILE`:

| Value | Behavior |
|-------|----------|
| `local-lab` | Default. Current dev lab: auth off, vulnerable modes allowed |
| `production-like` | Same as `BOUNDARY_LAYER_ENV=production` hardening for local validation |
| `production-saas` | Fail startup unless required SaaS settings present (see below) |

Check readiness without starting the API:

```bash
make production-saas-check          # expects NOT READY locally
make production-saas-check-example  # mocked pass for CI/docs
make production-saas-staging-readiness-check   # staging deploy config (NOT READY locally)
make production-saas-staging-readiness-example  # mocked staging pass for CI/docs
python -m apps.api.config_check
python -m apps.api.staging_check
```

### production-saas required settings

When `BOUNDARY_LAYER_PROFILE=production-saas`, startup fails unless configured:

- `BOUNDARY_LAYER_AUTH_PROVIDER` (`oidc` for staging; `oidc-test` allowed only for deterministic unit tests in non-staging env)
- `BOUNDARY_LAYER_AUTH_ENABLED=true`
- `OIDC_ISSUER_URL`, `OIDC_AUDIENCE`, `OIDC_JWKS_URL`, `OIDC_ALGORITHMS` (https only in staging; `none` rejected)
- `OIDC_TENANT_CLAIM`, `OIDC_ROLES_CLAIM` (required claim mapping)
- `DATABASE_URL` with SSL (`sslmode=require` or `DB_SSL_MODE=require`; no localhost/container hosts)
- `REDIS_URL` with `rediss://` and `REDIS_KEY_PREFIX`
- `BOUNDARY_LAYER_SECRET_KEY` (32+ chars, no insecure defaults)
- `BOUNDARY_LAYER_ALLOWED_ORIGINS` (no wildcards)
- `BOUNDARY_LAYER_PUBLIC_BASE_URL` (https required in staging)
- `BOUNDARY_LAYER_SECURE_COOKIES=true`
- `BOUNDARY_LAYER_TRUST_PROXY_HEADERS=true`
- `BOUNDARY_LAYER_METRICS_TOKEN`
- `BOUNDARY_LAYER_FILE_STORAGE_BACKEND` (`s3`, `gcs`, or `r2` — not local disk)
- `OBJECT_STORAGE_BUCKET`, `OBJECT_STORAGE_REGION` when using cloud storage backend
- `SECRET_MANAGER_PROVIDER`, `SECRET_MANAGER_PROJECT_OR_PATH`
- `BOUNDARY_LAYER_AUDIT_LOG_ENABLED=true`
- Plus production env secrets when `BOUNDARY_LAYER_ENV=production` (`BOUNDARY_LAYER_API_KEY`, datastore passwords)

### Phase 3 scaffolds (not full services)

- `apps/api/jwks.py` — JWKS client with cache (HTTP for staging; in-memory for tests)
- `apps/api/storage.py` — object storage interface (no cloud SDK adapters yet)
- `apps/api/secrets.py` — secret manager interface (environment provider for tests only)
- `infra/terraform/` — IaC skeleton documented but **not applied**

## Non-breaking rules for the local lab

These commands must keep working without cloud services:

```bash
make setup
make up
make smoke
make demo
make validate
make validate-alerts
make validate-restore-fresh-volume
make bundle
```

Production SaaS work is **additive** and **profile-gated**.

## Related documents

- [AUTH_TENANCY_DESIGN.md](AUTH_TENANCY_DESIGN.md)
- [TENANCY_DATA_MODEL.md](TENANCY_DATA_MODEL.md)
- [DEPLOYMENT_ARCHITECTURE.md](DEPLOYMENT_ARCHITECTURE.md)
- [SAAS_SECURITY_CHECKLIST.md](SAAS_SECURITY_CHECKLIST.md)
- [CI_CD_PRODUCTION_PLAN.md](CI_CD_PRODUCTION_PLAN.md)
- [PRODUCTION.md](PRODUCTION.md)
