#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "BoundaryLayer live staging validation package"

if [[ "${RUN_LIVE_STAGING_CHECKS:-}" != "true" ]]; then
  echo "RUN_LIVE_STAGING_CHECKS must be true for live staging validation." >&2
  exit 1
fi

required_env=(
  STAGING_BASE_URL
  STAGING_TEST_ACCESS_TOKEN_TENANT_A
  STAGING_METRICS_AUTH_TOKEN
  DATABASE_URL
  REDIS_URL
  OIDC_JWKS_URL
)

missing=()
for name in "${required_env[@]}"; do
  if [[ -z "${!name:-}" ]]; then
    missing+=("$name")
  fi
done

if ((${#missing[@]} > 0)); then
  echo "Missing required environment variables for live staging validation:"
  for name in "${missing[@]}"; do
    echo "  - $name"
  done
  exit 1
fi

failures=0

run_step() {
  local label="$1"
  shift
  if "$@"; then
    echo "PASS $label"
  else
    echo "FAIL $label" >&2
    failures=$((failures + 1))
  fi
}

run_step "managed-services-live-check" bash scripts/production-saas-managed-services-live-check.sh
run_step "staging-smoke-live" bash scripts/staging-smoke-live.sh

if [[ -n "${STAGING_ALERT_WEBHOOK_URL:-}" ]]; then
  if curl -sf "${STAGING_ALERT_WEBHOOK_URL}/health" >/dev/null 2>&1; then
    echo "PASS staging alert endpoint reachable"
  else
    echo "FAIL staging alert endpoint check" >&2
    failures=$((failures + 1))
  fi
else
  echo "SKIP staging alert endpoint (STAGING_ALERT_WEBHOOK_URL not set)"
fi

echo ""
if [[ "$failures" -gt 0 ]]; then
  echo "LIVE STAGING VALIDATION FAIL ($failures step(s) failed)"
  exit 1
fi

echo "LIVE STAGING VALIDATION PASS"
