# SaaS Security Checklist

P0 security gates before any public Production SaaS launch. Status as of v1.3.5 guardrails pass.

| Item | Status | Owner | Evidence required | Blocker |
|------|--------|-------|-------------------|---------|
| Auth required for all tenant APIs | Partial | Engineering | JWT middleware + membership check in production-saas; local-lab unchanged | Yes |
| Tenant isolation in DB queries | Partial | Engineering | Tenancy schema + tenant-scoped governance/write-storm helpers + cross-tenant tests | Yes |
| No public unauthenticated labs | Partial | Engineering | production-saas requires Bearer JWT on /labs; local-lab intentionally open | Yes |
| Rate limits at edge and app | Partial | Engineering | Edge WAF not live; Redis limiter + in-app body size guard in production-saas | Yes |
| Input validation on all endpoints | Partial | Engineering | Pydantic schemas, fuzz tests | Yes |
| Output redaction in logs | Not started | Security | Log sampling review | Yes |
| Audit logs for admin and lab actions | Partial | Engineering | `audit_events` + `apps/api/audit_export.py` local sink; external immutable/SIEM not live | Yes |
| Secret manager (no .env in prod) | Partial | Platform | `SECRET_MANAGER_PROVIDER` gate + lazy SDK adapters; live secret check gated | Yes |
| TLS everywhere | Partial | Platform | TLS in prod-like profile; `rediss://` + DB SSL validation in production-saas | Yes |
| CORS allowlist | Partial | Engineering | ALLOWED_ORIGINS in production-saas gate; wildcard rejected in staging | Yes |
| CSRF strategy if browser sessions | Not started | Engineering | Design doc + tests | Yes |
| Secure cookies | Partial | Engineering | SECURE_COOKIES required in production-saas/staging checks | Yes |
| Dependency scan in CI | Done | Engineering | Security Scan workflow green | No |
| Container scan in CI | Done | Engineering | Trivy job green | No |
| SBOM generation | Not started | Platform | Syft artifact in CI | Yes |
| SAST | Partial | Security | ruff + secret scan; no dedicated SAST | Yes |
| DAST plan | Not started | Security | Scheduled DAST against staging | Yes |
| Backup restore tested | Partial | Platform | Local fresh-volume proof only | Yes |
| Incident response runbook | Not started | Security | Published IR doc | Yes |
| Logging and alerting to on-call | Partial | Platform | Local Prometheus only | Yes |
| Access reviews | Not started | Security | Quarterly review process | Yes |
| Data retention policy | Not started | Product/Legal | Written policy | Yes |
| Abuse reporting channel | Not started | Product | security@ contact + abuse form | Yes |
| Terms of service | Not started | Legal | Published ToS | Yes |
| Privacy policy | Not started | Legal | Published privacy policy | Yes |

**None of the P0 blockers marked "Yes" are fully closed.** Do not launch public SaaS until evidence exists for each row.
