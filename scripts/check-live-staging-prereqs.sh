#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "BoundaryLayer live staging prerequisites check"

if [[ "${RUN_LIVE_STAGING_CHECKS:-}" != "true" ]]; then
  echo "LIVE STAGING PREREQS MISSING"
  echo "  - RUN_LIVE_STAGING_CHECKS"
  exit 1
fi

# Map alternate env names without printing values.
if [[ -z "${BOUNDARY_LAYER_ALLOWED_ORIGINS:-}" && -n "${ALLOWED_ORIGINS:-}" ]]; then
  export BOUNDARY_LAYER_ALLOWED_ORIGINS="$ALLOWED_ORIGINS"
fi
if [[ -z "${BOUNDARY_LAYER_PUBLIC_BASE_URL:-}" && -n "${PUBLIC_BASE_URL:-}" ]]; then
  export BOUNDARY_LAYER_PUBLIC_BASE_URL="$PUBLIC_BASE_URL"
fi
if [[ -z "${BOUNDARY_LAYER_METRICS_TOKEN:-}" && -n "${METRICS_AUTH_TOKEN:-}" ]]; then
  export BOUNDARY_LAYER_METRICS_TOKEN="$METRICS_AUTH_TOKEN"
fi
if [[ -z "${STAGING_METRICS_AUTH_TOKEN:-}" && -n "${BOUNDARY_LAYER_METRICS_TOKEN:-}" ]]; then
  export STAGING_METRICS_AUTH_TOKEN="$BOUNDARY_LAYER_METRICS_TOKEN"
fi

required_env=(
  STAGING_BASE_URL
  STAGING_TEST_ACCESS_TOKEN_TENANT_A
  STAGING_TEST_ACCESS_TOKEN_TENANT_B
  STAGING_METRICS_AUTH_TOKEN
  DATABASE_URL
  REDIS_URL
  OBJECT_STORAGE_BUCKET
  OBJECT_STORAGE_REGION
  OBJECT_STORAGE_PREFIX
  SECRET_MANAGER_PROVIDER
  SECRET_MANAGER_PROJECT_OR_PATH
  BOUNDARY_LAYER_HEALTHCHECK_SECRET_NAME
  OIDC_ISSUER_URL
  OIDC_AUDIENCE
  OIDC_JWKS_URL
  BOUNDARY_LAYER_ALLOWED_ORIGINS
  BOUNDARY_LAYER_PUBLIC_BASE_URL
  BOUNDARY_LAYER_METRICS_TOKEN
  AUDIT_SINK_PROVIDER
)

missing=()
for name in "${required_env[@]}"; do
  if [[ -z "${!name:-}" ]]; then
    missing+=("$name")
  fi
done

if ((${#missing[@]} > 0)); then
  echo "LIVE STAGING PREREQS MISSING"
  for name in "${missing[@]}"; do
    echo "  - $name"
  done
  exit 1
fi

echo "LIVE STAGING PREREQS READY"
