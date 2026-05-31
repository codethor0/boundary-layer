# Tenancy Data Model

Proposed schema for hosted Production SaaS. **Phase 1 implemented:** `tenants`, `users`, `tenant_memberships`, and `audit_events` tables with helpers in `apps/api/tenancy.py` and migration `002_tenancy`. **Lab tables remain single-tenant and unchanged.**

## Core entities

### tenants

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | Tenant identifier |
| slug | text unique | URL-safe name |
| name | text | Display name |
| status | enum | active, suspended, deleted |
| created_at | timestamptz | |
| plan_id | text nullable | Billing placeholder |

### users

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | Internal user ID |
| oidc_sub | text unique | Identity provider subject |
| email | text | From OIDC, not primary auth secret |
| created_at | timestamptz | |

### memberships

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| tenant_id | UUID FK | |
| user_id | UUID FK | |
| role | text | tenant_admin, lab_runner, observer |
| created_at | timestamptz | |

Unique constraint: `(tenant_id, user_id)`.

### audit_events

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| tenant_id | UUID FK | Required |
| actor_id | UUID nullable | User or service account |
| action | text | e.g. lab.run, auth.login_failed |
| resource_type | text | |
| resource_id | text nullable | |
| metadata | jsonb | Redacted details |
| created_at | timestamptz | Append-only |

### lab_runs (future production table)

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| tenant_id | UUID FK | Required |
| lab_id | text | |
| mode | text | hardened only in SaaS |
| blocked | boolean | |
| created_at | timestamptz | |

### uploaded_artifacts (future)

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| tenant_id | UUID FK | Required |
| storage_key | text | Object store path |
| content_type | text | |
| sha256 | text | |
| created_at | timestamptz | |

### billing_customers (placeholder)

| Column | Type | Notes |
|--------|------|-------|
| tenant_id | UUID FK | |
| external_customer_id | text | Stripe/etc |
| status | text | |

## Scoping rules

1. **Every production table needs `tenant_id`.** No exceptions for tenant-owned data.
2. **Every query must filter by tenant** from authenticated context, not request body.
3. **Every Redis key** must include tenant namespace: `bl:{tenant_id}:...`.
4. **Every object key** must include tenant prefix: `{tenant_id}/...`.
5. **Every audit event** must include `tenant_id` and `actor_id` when known.

## Migration note

Current lab tables (`write_storm_events`, `deletion_audit`, etc.) are used for local simulation. A SaaS migration would either:

- Add `tenant_id` with default for local-lab profile only, or
- Introduce parallel tenant-scoped tables for hosted mode.

Do not migrate current lab tables in this pass without an explicit migration plan and tests.

## Data retention (placeholder)

- Lab run history: 90 days default (configurable per plan).
- Audit logs: 1 year minimum for security tenants.
- Uploaded artifacts: delete with tenant offboarding workflow.
