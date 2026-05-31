#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "NOTE: mocked example values only — not a live deployment."
export BOUNDARY_LAYER_PROFILE=production-saas
export BOUNDARY_LAYER_ENV=production
export BOUNDARY_LAYER_AUTH_ENABLED=true
export BOUNDARY_LAYER_AUTH_PROVIDER=oidc
export OIDC_ISSUER_URL=https://issuer.example.com
export OIDC_AUDIENCE=boundary-layer-api
export OIDC_JWKS_URL=https://issuer.example.com/.well-known/jwks.json
export OIDC_ALGORITHMS=RS256
export OIDC_TENANT_CLAIM=https://boundarylayer.dev/tenant_id
export OIDC_ROLES_CLAIM=https://boundarylayer.dev/roles
export OIDC_SUBJECT_CLAIM=sub
export OIDC_EMAIL_CLAIM=email
export OIDC_CLOCK_SKEW_SECONDS=60
export DATABASE_URL='postgresql://boundary_layer:example@postgres.example:5432/boundary_layer?sslmode=require'
export REDIS_URL=rediss://:example@redis.example:6379/0
export REDIS_KEY_PREFIX=boundary_layer:tenant
export DB_SSL_MODE=require
export BOUNDARY_LAYER_SECRET_KEY=production-saas-phase1-secret-key-minimum-32
export BOUNDARY_LAYER_ALLOWED_ORIGINS=https://app.example.com
export BOUNDARY_LAYER_PUBLIC_BASE_URL=https://app.example.com
export BOUNDARY_LAYER_SECURE_COOKIES=true
export BOUNDARY_LAYER_TRUST_PROXY_HEADERS=true
export BOUNDARY_LAYER_METRICS_TOKEN=production-metrics-token-minimum-24
export BOUNDARY_LAYER_FILE_STORAGE_BACKEND=s3
export OBJECT_STORAGE_BUCKET=boundary-layer-staging-example
export OBJECT_STORAGE_REGION=us-east-1
export OBJECT_STORAGE_PREFIX=tenants/
export BOUNDARY_LAYER_AUDIT_LOG_ENABLED=true
export SECRET_MANAGER_PROVIDER=aws
export SECRET_MANAGER_PROJECT_OR_PATH=boundary-layer/staging
export SECRET_ROTATION_REQUIRED=true
export SECRET_CACHE_TTL_SECONDS=300
export BOUNDARY_LAYER_API_KEY=production-api-key-minimum-24-chars
export POSTGRES_PASSWORD=production-postgres-password
export REDIS_PASSWORD=production-redis-password-16
export SESSION_HMAC_SECRET=production-session-hmac-secret

.venv/bin/python - <<'PY'
from apps.api.config_check import evaluate_production_saas_readiness
import os

report = evaluate_production_saas_readiness(dict(os.environ), mocked=True)
print(report.format_text())
raise SystemExit(0 if report.ready else 1)
PY
