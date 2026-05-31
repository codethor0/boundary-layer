# Authentication and Tenancy Design

Design document for a future hosted Production SaaS. **Phase 1 implemented:** JWT middleware, tenant/membership/audit schema, and production-saas route protection. **Not a full hosted SaaS launch.**

## Recommendation: OIDC-first

Use an OIDC identity provider (Auth0, Clerk, AWS Cognito, or self-hosted Keycloak only if operational cost is accepted).

Flow:

1. User signs in via OIDC authorization code flow (PKCE for SPA).
2. API validates JWT access tokens (issuer, audience, signature, expiry).
3. API resolves `tenant_id` and `roles` from token claims plus membership table.
4. Every request carries server-resolved tenant context; never trust client-supplied tenant IDs alone.

## JWT validation model

- Validate `iss`, `aud`, `exp`, `nbf`, signature (JWKS rotation).
- Reject tokens with weak algorithms.
- Map `sub` to internal user ID.
- Optional: refresh tokens handled only by auth provider or BFF layer.

## Tenant resolution

1. Primary: JWT claim `https://boundarylayer.dev/tenant_id` or org slug mapped in membership table.
2. Fallback for service accounts: API key scoped to single tenant.
3. Admin cross-tenant access: explicit admin role with audit logging only.

## Role model

| Role | Permissions |
|------|-------------|
| `tenant_admin` | Manage tenant settings, users, API keys |
| `lab_runner` | Run labs in hardened mode within tenant |
| `observer` | Read metrics, audit logs, lab history (no vulnerable mode) |
| `service_account` | Automation with scoped API key |
| `platform_admin` | Internal operator; cross-tenant; heavily audited |

Deny by default. Vulnerable lab modes disabled in production-saas.

## API key strategy

- Tenant-scoped API keys stored hashed (bcrypt/argon2).
- Prefix + secret pattern for identification.
- Rotation and revocation with audit events.
- Separate keys for CI automation vs human operators.

## Session and cookie strategy (future web UI)

If a browser UI is added:

- HttpOnly, Secure, SameSite=Lax/Strict cookies for session BFF.
- CSRF tokens for state-changing browser requests.
- No lab tokens in localStorage.

## Enforcement points

### PostgreSQL

- Every production table includes `tenant_id UUID NOT NULL`.
- All queries filter by `tenant_id` from request context.
- Consider Postgres Row Level Security as defense in depth.

### Redis

- Key pattern: `bl:{tenant_id}:{namespace}:{key}`.
- Never use global keys for tenant data in SaaS mode.

### Object storage

- Path pattern: `{tenant_id}/uploads/{artifact_id}`.
- Presigned URLs scoped to tenant prefix.

### Logs

- Include `tenant_id`, `actor_id`, `request_id`.
- Redact secrets, tokens, PII from log fields.

## Test isolation checklist (future)

- [ ] User A cannot read tenant B lab runs.
- [ ] Redis keys from tenant A never visible to tenant B.
- [ ] Object listing restricted to tenant prefix.
- [ ] Admin actions emit audit events.
- [ ] Vulnerable mode returns 403 in production-saas.

## Implementation checklist

1. Choose OIDC provider and register API audience. **[Phase 2]**
2. Add User, Tenant, Membership models (see `TENANCY_DATA_MODEL.md`). **[Done: schema + helpers]**
3. Implement JWT middleware and tenant context dependency. **[Done: production-saas profile]**
4. Migrate lab tables to tenant-scoped schema (Alembic). **[Not started]**
5. Add integration tests for cross-tenant denial. **[Partial: prompt-cache + auth tests]**
6. Add admin audit log pipeline. **[Foundation only]**
