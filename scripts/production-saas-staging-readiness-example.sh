#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "NOTE: mocked staging example values only — not a live deployment."
export BOUNDARY_LAYER_PROFILE=production-saas
export BOUNDARY_LAYER_ENV=staging
export BOUNDARY_LAYER_AUTH_ENABLED=true
export BOUNDARY_LAYER_AUTH_PROVIDER=oidc
export OIDC_ISSUER_URL=https://staging-issuer.example.com
export OIDC_AUDIENCE=boundary-layer-api-staging
export OIDC_JWKS_URL=https://staging-issuer.example.com/.well-known/jwks.json
export OIDC_ALGORITHMS=RS256
export OIDC_TENANT_CLAIM=https://boundarylayer.dev/tenant_id
export OIDC_ROLES_CLAIM=https://boundarylayer.dev/roles
export OIDC_SUBJECT_CLAIM=sub
export OIDC_EMAIL_CLAIM=email
export OIDC_REQUIRED_ROLES=lab_runner
export OIDC_CLOCK_SKEW_SECONDS=60
export DATABASE_URL='postgresql://boundary_layer:example@db.staging.example:5432/boundary_layer?sslmode=require'
export DB_SSL_MODE=require
export DB_POOL_MIN_SIZE=2
export DB_POOL_MAX_SIZE=20
export DB_CONNECT_TIMEOUT_SECONDS=5
export REDIS_URL=rediss://:example@redis.staging.example:6379/0
export REDIS_CONNECT_TIMEOUT_SECONDS=3
export REDIS_KEY_PREFIX=boundary_layer:tenant
export BOUNDARY_LAYER_SECRET_KEY=production-saas-staging-secret-key-minimum-32
export BOUNDARY_LAYER_ALLOWED_ORIGINS=https://staging.example.com
export BOUNDARY_LAYER_PUBLIC_BASE_URL=https://staging.example.com
export BOUNDARY_LAYER_SECURE_COOKIES=true
export BOUNDARY_LAYER_TRUST_PROXY_HEADERS=true
export BOUNDARY_LAYER_METRICS_TOKEN=production-metrics-token-minimum-24
export BOUNDARY_LAYER_FILE_STORAGE_BACKEND=s3
export OBJECT_STORAGE_BUCKET=boundary-layer-staging-artifacts
export OBJECT_STORAGE_REGION=us-east-1
export OBJECT_STORAGE_PREFIX=tenants/
export OBJECT_STORAGE_PRESIGNED_URL_TTL_SECONDS=900
export BOUNDARY_LAYER_AUDIT_LOG_ENABLED=true
export SECRET_MANAGER_PROVIDER=aws
export SECRET_MANAGER_PROJECT_OR_PATH=boundary-layer/staging
export SECRET_ROTATION_REQUIRED=true
export BOUNDARY_LAYER_API_KEY=production-api-key-minimum-24-chars
export POSTGRES_PASSWORD=production-postgres-password
export REDIS_PASSWORD=production-redis-password-16
export SESSION_HMAC_SECRET=production-session-hmac-secret

.venv/bin/python - <<'PY'
from apps.api.staging_check import evaluate_staging_readiness
import os

report = evaluate_staging_readiness(dict(os.environ), mocked=True)
print(report.format_text())
raise SystemExit(0 if report.ready else 1)
PY
