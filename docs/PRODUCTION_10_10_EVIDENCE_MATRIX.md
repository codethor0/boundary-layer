# Production SaaS 10/10 Evidence Matrix

Source of truth for Production SaaS readiness scoring. **Dry-runs, scaffolds, and structural checks are not live production evidence.**

Score cap rule: **Production SaaS score is capped at 6/10 until live staging validation passes.**

| # | Category | Current score | Required evidence for 10/10 | Current evidence | Missing evidence | Local | Cloud | Legal | Next command / document | Owner | Priority |
|---|----------|---------------|----------------------------|------------------|------------------|-------|-------|-------|-------------------------|-------|----------|
| 1 | Staging deployment | 2/10 | Live ECS/container deploy + health | Dry-run scripts, runbook | Live deploy, DNS, TLS | Partial | Yes | No | `make deploy-staging-dry-run`; `docs/STAGING_DEPLOYMENT_RUNBOOK.md` | Platform | P0 |
| 2 | Production deployment architecture | 2/10 | Approved architecture + prod account | Design docs only | Prod topology applied | Yes | Yes | No | `docs/DEPLOYMENT_ARCHITECTURE.md` | Platform | P0 |
| 3 | Managed PostgreSQL | 3/10 | Live `SELECT 1`, SSL, DB name, timeout | Policy checks, local compose | Live RDS proof | Partial | Yes | No | `RUN_LIVE_STAGING_CHECKS=true make production-saas-managed-services-live-check` | Platform | P0 |
| 4 | Managed Redis | 3/10 | Live PING, tenant key TTL, rediss | Policy checks, local redis | Live ElastiCache proof | Partial | Yes | No | managed-services live check | Platform | P0 |
| 5 | Object storage | 3/10 | Live write/read/delete tenant path | Adapter code, policy | Live S3 proof | Partial | Yes | No | managed-services live check | Platform | P0 |
| 6 | Secret manager | 3/10 | Live secret read, redaction | Adapter shells, policy | Live Secrets Manager | Partial | Yes | No | managed-services live check | Platform | P0 |
| 7 | OIDC authentication | 4/10 | Live JWKS, issuer HTTPS, smoke JWT | Middleware, unit tests | Live IdP + tokens | Partial | Yes | No | `make staging-smoke-live` | Engineering | P0 |
| 8 | Tenant isolation | 4/10 | Live cross-tenant 403 smoke | Unit tests, audit writes | Live staging proof | Yes | Yes | No | staging smoke tenant B token | Engineering | P0 |
| 9 | RBAC authorization | 3/10 | Role enforcement in prod paths | Claim checks | Policy engine, admin UI | Partial | Yes | No | `docs/AUTH_TENANCY_DESIGN.md` | Engineering | P0 |
| 10 | Immutable audit logging | 2/10 | Append-only sink, tamper detection | Postgres audit table | Immutable sink live | Partial | Yes | No | `make audit-sink-live-check` | Security | P0 |
| 11 | SIEM/export | 1/10 | Live export with correlation IDs | Design doc, fail-closed shells | SIEM integration | No | Yes | No | `docs/AUDIT_SIEM_PLAN.md` | Security | P0 |
| 12 | WAF/edge protection | 2/10 | Live WAF rules, size/rate limits | In-app body guard, docs | Edge WAF enforced | Partial | Yes | No | `make waf-live-check` | Security | P0 |
| 13 | Abuse/rate-limit controls | 3/10 | Edge + tenant limits validated | Redis limiter local | Live abuse alerts | Partial | Yes | No | `docs/WAF_ABUSE_CONTROLS.md` | Security | P0 |
| 14 | CI/CD deploy pipeline | 4/10 | Manual deploy + live smoke artifact | Workflows (manual) | Auto deploy + evidence upload | Partial | Yes | No | `.github/workflows/production-saas-live-validation.yml` | Platform | P0 |
| 15 | Rollback | 2/10 | Tested rollback to prior digest | Runbook text | Executed rollback proof | No | Yes | No | `docs/STAGING_DEPLOYMENT_RUNBOOK.md` | Platform | P0 |
| 16 | Container image security | 4/10 | Scan gate on release image | Hadolint, Trivy CI | Live scan artifact | Yes | Yes | No | `make container-security-scan` | Security | P1 |
| 17 | SBOM | 2/10 | SPDX SBOM per release | Script scaffold | CI SBOM artifact | Yes | Yes | No | `make generate-sbom` | Security | P1 |
| 18 | Dependency scanning | 4/10 | pip-audit clean or documented | pip-audit CI | Patched deps verified | Yes | No | No | `pip-audit -r apps/api/requirements.txt` | Security | P1 |
| 19 | SAST/DAST | 3/10 | SAST + scheduled DAST on staging | ruff, secret scan | DAST reports | Partial | Yes | No | CI security scan | Security | P1 |
| 20 | Backup and restore | 4/10 | Off-host backup + restore drill | Local fresh-volume proof | Staging RDS restore drill | Partial | Yes | No | `make validate-restore-fresh-volume` | Platform | P0 |
| 21 | Disaster recovery | 1/10 | DR drill with RTO/RPO met | Starter runbook | Tested failover | No | Yes | No | `CONFIRM_STAGING_DR_TEST=true make dr-restore-live-check` | Platform | P0 |
| 22 | On-call runbooks | 1/10 | Tested paging + runbooks | `docs/DR_ONCALL_RUNBOOK.md` | On-call rotation | No | Yes | No | DR/on-call doc | Operations | P0 |
| 23 | Alert routing | 3/10 | PagerDuty/Opsgenie live | Local Prometheus | Production routing | Partial | Yes | No | Alertmanager config | Operations | P1 |
| 24 | SLOs/error budgets | 1/10 | Defined SLOs + dashboards | Metrics docs | SLO enforcement | No | Yes | No | `docs/METRICS.md` | Operations | P2 |
| 25 | Data retention | 1/10 | Published retention policy | Config scaffold | Enforcement job | No | Yes | Yes | Legal + engineering | Legal | P1 |
| 26 | User deletion/export | 1/10 | DSR workflow tested | Not implemented | Export/delete API | No | Yes | Yes | `docs/LEGAL_COMPLIANCE_READINESS.md` | Legal | P1 |
| 27 | Legal terms | 0/10 | Counsel-approved ToS | MIT license only | ToS published | No | No | Yes | Legal review | Legal | P0 |
| 28 | Privacy policy | 0/10 | Counsel-approved privacy policy | Not published | Privacy policy | No | No | Yes | Legal review | Legal | P0 |
| 29 | DPA/subprocessors | 0/10 | Signed DPA + subprocessor list | Not started | DPA package | No | No | Yes | Legal review | Legal | P0 |
| 30 | Support process | 1/10 | Ticketing + SLA tiers | None | Support tooling | No | Yes | No | Product ops | Product | P2 |
| 31 | Cost controls | 1/10 | Budget alerts per env | Not configured | Cloud budgets | No | Yes | No | Cloud billing alerts | Platform | P2 |
| 32 | Operational evidence | 2/10 | Completed evidence runner artifact | Structural gates only; Phase 7 blocked | `artifacts/live-evidence/LIVE_STAGING_EVIDENCE.md` when live passes | Partial | Yes | No | `make production-saas-evidence-runner` | Operations | P0 |

## Scoring rules

| Score | Meaning |
|-------|---------|
| **6/10** | Structural readiness, local lab, scaffolds, dry runs only |
| **7/10** | Live staging deploy; managed DB/Redis/object storage/secret manager/OIDC pass |
| **8/10** | CI/CD deploy pipeline, live smoke, rollback plan, WAF enabled, audit export, alerts validated |
| **9/10** | DR restore drill, on-call tested, SLOs, DAST/SBOM/signing, operational evidence |
| **10/10** | Legal/compliance approved, incident response tested, production readiness review signed, external review |

Do not claim Production SaaS ready until every P0 row has **Passed** evidence.
