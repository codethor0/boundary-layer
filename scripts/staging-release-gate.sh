#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

export_staging_dry_run_env() {
  export BOUNDARY_LAYER_PROFILE="${BOUNDARY_LAYER_PROFILE:-production-saas}"
  export BOUNDARY_LAYER_ENV="${BOUNDARY_LAYER_ENV:-staging}"
  export DATABASE_URL="${DATABASE_URL:-postgresql://placeholder:placeholder@db.staging.example:5432/boundary_layer?sslmode=require}"
  export REDIS_URL="${REDIS_URL:-rediss://:placeholder@redis.staging.example:6379/0}"
  export SECRET_MANAGER_PROVIDER="${SECRET_MANAGER_PROVIDER:-aws}"
  export SECRET_MANAGER_PROJECT_OR_PATH="${SECRET_MANAGER_PROJECT_OR_PATH:-boundary-layer/staging}"
  export OBJECT_STORAGE_BUCKET="${OBJECT_STORAGE_BUCKET:-boundary-layer-staging-artifacts-example}"
  export BOUNDARY_LAYER_PUBLIC_BASE_URL="${BOUNDARY_LAYER_PUBLIC_BASE_URL:-https://staging.example.com}"
  export STAGING_RELEASE_IMAGE="${STAGING_RELEASE_IMAGE:-ghcr.io/example/boundary-layer:staging-placeholder}"
}

echo "BoundaryLayer staging release gate"
echo ""

LOCAL_OK=true
STRUCTURAL_OK=true
LIVE_SKIPPED=true
LIVE_OK=false

run_step() {
  local label="$1"
  shift
  if "$@"; then
    echo "PASS $label"
  else
    echo "FAIL $label" >&2
    return 1
  fi
}

run_step "unit tests" make test >/dev/null || LOCAL_OK=false
run_step "lint" make lint >/dev/null || LOCAL_OK=false
run_step "production-saas-check-example" make production-saas-check-example >/dev/null || STRUCTURAL_OK=false
run_step "production-saas-staging-readiness-example" make production-saas-staging-readiness-example >/dev/null || STRUCTURAL_OK=false
run_step "production-saas-managed-services-example" make production-saas-managed-services-example >/dev/null || STRUCTURAL_OK=false

export_staging_dry_run_env
run_step "staging-deploy-dry-run" bash scripts/staging-deploy-dry-run.sh >/dev/null || STRUCTURAL_OK=false
run_step "staging-smoke-structural" make staging-smoke-structural >/dev/null || STRUCTURAL_OK=false

if [[ "${RUN_LIVE_STAGING_CHECKS:-}" == "true" ]]; then
  LIVE_SKIPPED=false
  if run_step "production-saas-managed-services-live-check" make production-saas-managed-services-live-check >/dev/null \
    && run_step "staging-smoke-live" make staging-smoke-live >/dev/null; then
    LIVE_OK=true
  else
    LIVE_OK=false
  fi
fi

echo ""
if [[ "$LOCAL_OK" == "true" ]]; then
  echo "LOCAL CHECKS PASS"
else
  echo "LOCAL CHECKS FAIL"
fi

if [[ "$STRUCTURAL_OK" == "true" ]]; then
  echo "STRUCTURAL STAGING CHECKS PASS"
else
  echo "STRUCTURAL STAGING CHECKS FAIL"
fi

if [[ "$LIVE_SKIPPED" == "true" ]]; then
  echo "LIVE STAGING CHECKS SKIPPED"
else
  if [[ "$LIVE_OK" == "true" ]]; then
    echo "LIVE STAGING CHECKS PASS"
  else
    echo "LIVE STAGING CHECKS FAIL"
  fi
fi

if [[ "$LOCAL_OK" != "true" || "$STRUCTURAL_OK" != "true" ]]; then
  exit 1
fi

if [[ "$LIVE_SKIPPED" == "false" && "$LIVE_OK" != "true" ]]; then
  exit 1
fi

echo ""
echo "Staging release gate complete."
