#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ -z "${STAGING_BASE_URL:-}" ]]; then
  echo "STAGING_BASE_URL is required for staging smoke checks." >&2
  exit 1
fi

base_url="${STAGING_BASE_URL%/}"
metrics_token="${BOUNDARY_LAYER_METRICS_TOKEN:-}"
auth_header="${STAGING_AUTH_HEADER:-}"

echo "BoundaryLayer staging smoke check"
echo "Target: $base_url"

curl -sf "$base_url/health" >/dev/null
echo "PASS GET /health"

if [[ -n "$metrics_token" ]]; then
  curl -sf -H "Authorization: Bearer $metrics_token" "$base_url/metrics" >/dev/null
  echo "PASS GET /metrics (authenticated)"
else
  echo "SKIP GET /metrics — BOUNDARY_LAYER_METRICS_TOKEN not set"
fi

if [[ -n "$auth_header" ]]; then
  curl -sf -H "Authorization: $auth_header" "$base_url/labs" >/dev/null
  echo "PASS GET /labs (authenticated)"
else
  echo "SKIP GET /labs — STAGING_AUTH_HEADER not set"
fi

if [[ -n "$auth_header" && -n "${STAGING_LAB_MODE:-}" ]]; then
  curl -sf -X POST "$base_url/labs/redis/run" \
    -H "Authorization: $auth_header" \
    -H "Content-Type: application/json" \
    -d "{\"mode\":\"${STAGING_LAB_MODE}\"}" >/dev/null
  echo "PASS POST /labs/redis/run"
fi

echo "Staging smoke check complete."
