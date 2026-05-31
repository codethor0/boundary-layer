#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export BOUNDARY_LAYER_PROFILE=production-saas
export BOUNDARY_LAYER_ENV=production
export BOUNDARY_LAYER_AUTH_ENABLED=true
export BOUNDARY_LAYER_AUTH_PROVIDER=oidc
export OIDC_ISSUER_URL=https://issuer.example.com
export OIDC_AUDIENCE=boundary-layer-api
export OIDC_JWKS_URL=https://issuer.example.com/.well-known/jwks.json
export OIDC_ALGORITHMS=RS256
export DATABASE_URL=postgresql://boundary_layer:example@postgres.example:5432/boundary_layer
export REDIS_URL=rediss://:example@redis.example:6379/0
export BOUNDARY_LAYER_SECRET_KEY=production-saas-phase1-secret-key-minimum-32
export BOUNDARY_LAYER_ALLOWED_ORIGINS=https://app.example.com
export BOUNDARY_LAYER_PUBLIC_BASE_URL=https://app.example.com
export BOUNDARY_LAYER_SECURE_COOKIES=true
export BOUNDARY_LAYER_TRUST_PROXY_HEADERS=true
export BOUNDARY_LAYER_METRICS_TOKEN=production-metrics-token-minimum-24
export BOUNDARY_LAYER_FILE_STORAGE_BACKEND=s3
export BOUNDARY_LAYER_AUDIT_LOG_ENABLED=true
export BOUNDARY_LAYER_API_KEY=production-api-key-minimum-24-chars
export POSTGRES_PASSWORD=production-postgres-password
export REDIS_PASSWORD=production-redis-password-16
export SESSION_HMAC_SECRET=production-session-hmac-secret

.venv/bin/python -m apps.api.config_check
