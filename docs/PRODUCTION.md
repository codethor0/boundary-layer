# Production Deployment

BoundaryLayer v1.3.0 adds a production deployment profile while preserving the local lab stack in `docker-compose.yml`.

## What Production Adds

| Capability | Local lab (`docker-compose.yml`) | Production (`docker-compose.prod.yml`) |
|---|---|---|
| API authentication | Disabled by default | Required API key (Bearer or `X-API-Key`) |
| Metrics access | Open | Bearer token required |
| Vulnerable lab mode | Enabled | Disabled |
| Rate limiting | Disabled | Redis-backed (120 req/min default) + nginx burst limit |
| Structured logging | Plain text | JSON logs |
| Database migrations | On-demand `init_db()` | Alembic on startup |
| TLS ingress | None | Nginx on `:8443` |
| Data stores on host | Exposed | Internal network only |
| Alert webhook | Open | Bearer token required |
| External alerts | Local webhook only | Authenticated local webhook (Slack/PagerDuty templates commented in config) |
| OpenAPI / docs | Enabled | Disabled |
| Observability UI | Localhost ports | Internal-only (not exposed via nginx) |
| Container hardening | Dev defaults | Non-root, read-only rootfs, resource limits |
| Data-plane TLS | Disabled | Postgres `sslmode=require`, Redis TLS-only port |
| Secrets / backup | Manual | Vault/AWS SM examples, `make backup` / `make restore` |
| Security scanning | Local only | Hadolint, pip-audit, Trivy in CI |

## Quick Start (Production Profile)

1. Copy secrets:

```bash
cp .env.production.example .env.production
# Edit every CHANGE_ME value
```

2. Generate TLS material:

```bash
bash deploy/nginx/generate-certs.sh
bash deploy/tls/generate-internal-ca.sh
```

See [TLS.md](TLS.md) for CA-backed ingress certs and rotation.

3. Render observability configs:

```bash
set -a && source .env.production && set +a
bash deploy/scripts/render-prometheus-config.sh
bash deploy/scripts/render-alertmanager-config.sh
```

4. Start production stack:

```bash
make prod-up
# or: docker compose --env-file .env.production -f docker-compose.prod.yml -p boundary-layer-prod up -d --build
```

Production uses compose project `boundary-layer-prod` so Postgres/Redis volumes stay isolated from the local lab stack.

5. Verify through TLS ingress:

```bash
curl -k https://localhost:8443/health
curl -k -H "Authorization: Bearer $BOUNDARY_LAYER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"mode":"hardened"}' \
  https://localhost:8443/labs/redis/run
```

## Environment Variables

See `.env.production.example` for required secrets. Minimum token length is 24 characters.

Production mode (`BOUNDARY_LAYER_ENV=production`) automatically enables:

- `BOUNDARY_LAYER_AUTH_ENABLED=true`
- `BOUNDARY_LAYER_METRICS_AUTH_REQUIRED=true`
- `BOUNDARY_LAYER_ALLOW_VULNERABLE=false`
- `BOUNDARY_LAYER_RATE_LIMIT_ENABLED=true`
- `BOUNDARY_LAYER_RATE_LIMIT_BACKEND=redis`
- `BOUNDARY_LAYER_LOG_JSON=true`
- `BOUNDARY_LAYER_RUN_MIGRATIONS=true`

Local development remains unchanged when using `make up` without production env vars.

## Migrations

Alembic migrations live in `migrations/versions/`. Production startup runs `alembic upgrade head` when `BOUNDARY_LAYER_RUN_MIGRATIONS=true`.

Manual run:

```bash
export POSTGRES_HOST=localhost POSTGRES_PASSWORD=...
alembic upgrade head
```

## Observability

- Prometheus scrapes `/metrics` with bearer token authentication
- Alertmanager routes to the authenticated local webhook by default; uncomment Slack/PagerDuty receivers in `deploy/alertmanager/alertmanager.prod.yml.template` when real credentials are available
- Render configs before each deploy when tokens rotate

## Security Notes

- Replace self-signed certs with CA-backed certificates for real deployments
- Rotate API, metrics, webhook, Redis, Postgres, and HMAC secrets regularly
- Keep Redis and PostgreSQL off public networks (production compose does this by default)
- Use a secrets manager (Vault, AWS Secrets Manager, etc.) instead of plain `.env.production` in real environments — see [SECRETS.md](SECRETS.md)
- Schedule Postgres backups — see [BACKUP_RESTORE.md](BACKUP_RESTORE.md)

## Makefile Targets

```bash
make prod-render-config   # Render prometheus + alertmanager configs
make prod-up              # Start production stack
make prod-down            # Stop production stack
make validate-prod        # Full production profile validation (stops prod stack when done)
make validate-e2e         # Full test + lint + prod + local validation gate
make backup               # pg_dump backup to backups/postgres/
make restore BACKUP=...   # Restore from backup file
```
