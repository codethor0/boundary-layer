# Legal and Compliance Readiness

**This document is not legal advice.** All items require review by qualified legal counsel before public Production SaaS launch.

## Completion checklist

| Artifact | Status | Owner | Evidence location | Blocks production |
|----------|--------|-------|-------------------|-------------------|
| Terms of Service | missing | Legal | Not published | yes |
| Privacy Policy | missing | Legal | Not published | yes |
| Data Processing Agreement (DPA) | missing | Legal | Not published | yes |
| Subprocessor list | missing | Legal / Platform | Not published | yes |
| Acceptable Use Policy | missing | Legal | Not published | yes |
| Data retention policy | missing | Product / Legal | Not documented | yes |
| User deletion procedure | missing | Engineering / Legal | Not implemented | yes |
| User data export procedure | missing | Engineering / Legal | Not implemented | yes |
| Security policy (customer-facing) | missing | Security | Partial internal notes only | yes |
| Incident disclosure process | draft | Security | SECURITY.md disclosure path | yes |
| Cookie policy | missing | Legal / Product | N/A (no browser UI yet) | yes if UI ships |
| Accessibility statement | missing | Product | Not published | yes if public UI |

Status values: **missing** | **draft** | **reviewed** | **approved**

No artifact is **approved** in this repository pass.

## Engineering prerequisites (non-legal)

| Control | Status |
|---------|--------|
| Tenant isolation | Partial — unit + staging smoke required |
| Encryption in transit | Partial — TLS design; live proof required |
| Audit trail | Partial — Postgres only; immutable sink required |
| Backup/restore | Partial — local proof; staging DR drill required |
| Secret rotation policy | Config gate only |

## Before 10/10 Production SaaS

1. Counsel review of all customer-facing policies
2. Data inventory and classification
3. Subprocessor agreements for cloud, IdP, observability vendors
4. DSR (access/delete) workflow tested in staging
5. Incident notification timelines defined with counsel

**If legal/compliance artifacts are not reviewed, score cannot be 10/10.**

See [PRODUCTION_10_10_EVIDENCE_MATRIX.md](PRODUCTION_10_10_EVIDENCE_MATRIX.md).
