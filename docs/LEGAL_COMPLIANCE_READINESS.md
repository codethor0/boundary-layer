# Legal and Compliance Readiness (Starter)

**This document is not legal advice.** All items require review by qualified legal counsel before any public Production SaaS launch.

## Required before production launch

| Artifact | Status | Owner |
|----------|--------|-------|
| Terms of Service | Not started | Legal |
| Privacy Policy | Not started | Legal |
| Data Processing Agreement (DPA) | Not started | Legal |
| Subprocessor list | Not started | Legal / Platform |
| Data retention policy | Not started | Product / Legal |
| Security policy (customer-facing) | Not started | Security |
| Acceptable Use Policy | Not started | Legal |
| Incident disclosure process | Partial (SECURITY.md disclosure path) | Security / Legal |
| User data export process | Not started | Engineering / Legal |
| User data deletion process | Not started | Engineering / Legal |
| Cookie/consent strategy (if UI added) | Not started | Product / Legal |

## Compliance mapping (placeholder)

| Framework | Applicability | Status |
|-----------|---------------|--------|
| GDPR | If EU users | Not assessed |
| SOC 2 | If enterprise customers | Not started |
| ISO 27001 | Optional | Not started |

## Engineering prerequisites (non-legal)

- Immutable audit trail (not live)
- Tenant data isolation (partial)
- Encryption in transit (staging design)
- Backup/restore documentation (partial)
- Secret rotation policy (config gate only)

## Before claiming Production SaaS readiness

1. Legal review of all customer-facing policies
2. Data inventory and classification
3. Subprocessor agreements for managed cloud and IdP
4. DSR (access/delete) workflow tested
5. Incident notification timelines defined with counsel

BoundaryLayer **must not** claim 10/10 Production SaaS readiness until legal/compliance artifacts are reviewed and operational controls are validated.
