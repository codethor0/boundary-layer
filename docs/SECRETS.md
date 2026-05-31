# Secrets Management

Production requires strong secrets in `.env.production` or a secrets manager. Minimum lengths enforced at API startup:

| Secret | Minimum length |
|---|---|
| `BOUNDARY_LAYER_API_KEY` | 24 |
| `BOUNDARY_LAYER_METRICS_TOKEN` | 24 |
| `BOUNDARY_LAYER_ALERT_WEBHOOK_TOKEN` | 24 |
| `POSTGRES_PASSWORD` | 16 |
| `REDIS_PASSWORD` | 16 |
| `SESSION_HMAC_SECRET` | 16 |

## Local production profile

```bash
cp .env.production.example .env.production
# Replace every CHANGE_ME value
```

Never commit `.env.production`.

## HashiCorp Vault

Example loader: `deploy/secrets/load-from-vault.sh.example`

```bash
export VAULT_ADDR=https://vault.example.com
export VAULT_TOKEN=...
bash deploy/secrets/load-from-vault.sh > .env.production
make prod-up
```

Store a JSON object at `secret/data/boundary-layer` with all keys from `.env.production.example`.

## AWS Secrets Manager

Example loader: `deploy/secrets/load-from-aws-sm.sh.example`

```bash
export AWS_REGION=us-east-1
export SECRET_ID=boundary-layer/production
bash deploy/secrets/load-from-aws-sm.sh > .env.production
make prod-up
```

Secret JSON should include all production keys. Defaults for `BOUNDARY_LAYER_ENV`, trusted hosts, and rate-limit backend are applied if omitted.

## Rotation

1. Generate new values in your secrets manager
2. Render observability configs: `make prod-render-config`
3. Rolling restart: `make prod-down && make prod-up`
4. Rotate TLS material separately — see [TLS.md](TLS.md)

## CI

GitHub Actions generates ephemeral secrets for `make validate-prod` in `.github/workflows/prod-validate.yml`. Do not reuse CI-generated values in real deployments.
