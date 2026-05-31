#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export BOUNDARY_LAYER_PROFILE=production-saas
export BOUNDARY_LAYER_ENV=production
export BOUNDARY_LAYER_AUTH_PROVIDER=oidc-example
export DATABASE_URL=postgresql://boundary_layer:example@postgres.example:5432/boundary_layer
export REDIS_URL=rediss://:example@redis.example:6379/0
export BOUNDARY_LAYER_SECRET_KEY=example-production-saas-secret-key-32chars
export BOUNDARY_LAYER_ALLOWED_ORIGINS=https://app.example.com
export BOUNDARY_LAYER_PUBLIC_BASE_URL=https://app.example.com
export BOUNDARY_LAYER_SECURE_COOKIES=true
export BOUNDARY_LAYER_TRUST_PROXY_HEADERS=true
export BOUNDARY_LAYER_METRICS_TOKEN=example-metrics-token-min-24-chars
export BOUNDARY_LAYER_FILE_STORAGE_BACKEND=s3
export BOUNDARY_LAYER_AUDIT_LOG_ENABLED=true
export BOUNDARY_LAYER_API_KEY=example-production-api-key-min-24-chars
export POSTGRES_PASSWORD=example-postgres-password
export REDIS_PASSWORD=example-redis-password-16
export SESSION_HMAC_SECRET=example-session-hmac-secret

.venv/bin/python -m apps.api.config_check
