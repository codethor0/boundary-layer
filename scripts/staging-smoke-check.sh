#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

MODE="${STAGING_SMOKE_MODE:-}"
if [[ -z "$MODE" ]]; then
  if [[ "${RUN_LIVE_STAGING_CHECKS:-}" == "true" ]]; then
    MODE="live"
  else
    MODE="structural"
  fi
fi

required_structural=(
  STAGING_BASE_URL
  STAGING_TEST_ACCESS_TOKEN_TENANT_A
  STAGING_METRICS_AUTH_TOKEN
)

if [[ "$MODE" == "structural" ]]; then
  echo "BoundaryLayer staging smoke check (structural)"
  missing=()
  for name in "${required_structural[@]}"; do
    if [[ -z "${!name:-}" ]]; then
      missing+=("$name")
    fi
  done
  if ((${#missing[@]} > 0)); then
    echo "Missing required staging smoke variables:"
    for name in "${missing[@]}"; do
      echo "  - $name"
    done
    exit 1
  fi
  echo "STRUCTURAL STAGING SMOKE PASS"
  exit 0
fi

if [[ "$MODE" != "live" ]]; then
  echo "STAGING_SMOKE_MODE must be structural or live" >&2
  exit 1
fi

if [[ "${RUN_LIVE_STAGING_CHECKS:-}" != "true" ]]; then
  echo "Live staging smoke refused: set RUN_LIVE_STAGING_CHECKS=true" >&2
  exit 1
fi

for name in "${required_structural[@]}"; do
  if [[ -z "${!name:-}" ]]; then
    echo "Missing required live smoke variable: $name" >&2
    exit 1
  fi
done

base_url="${STAGING_BASE_URL%/}"
token_a="${STAGING_TEST_ACCESS_TOKEN_TENANT_A}"
token_b="${STAGING_TEST_ACCESS_TOKEN_TENANT_B:-}"
metrics_token="${STAGING_METRICS_AUTH_TOKEN}"

echo "BoundaryLayer staging smoke check (live)"
echo "Target: $base_url"

curl -sf "$base_url/health" >/dev/null
echo "PASS GET /health"

curl -sf -H "Authorization: Bearer $metrics_token" "$base_url/metrics" >/dev/null
echo "PASS GET /metrics (authenticated)"

curl -sf -H "Authorization: Bearer $token_a" "$base_url/labs" >/dev/null
echo "PASS GET /labs (authenticated tenant A)"

curl -sf -X POST "$base_url/labs/redis/run" \
  -H "Authorization: Bearer $token_a" \
  -H "Content-Type: application/json" \
  -d '{"mode":"hardened"}' >/dev/null
echo "PASS POST /labs/redis/run"

curl -sf -X POST "$base_url/labs/prompt-cache-isolation/run" \
  -H "Authorization: Bearer $token_a" \
  -H "Content-Type: application/json" \
  -d '{"mode":"hardened"}' >/dev/null
echo "PASS POST /labs/prompt-cache-isolation/run"

status="$(curl -s -o /dev/null -w '%{http_code}' "$base_url/labs")"
if [[ "$status" != "401" ]]; then
  echo "FAIL unauthenticated GET /labs expected 401, got $status" >&2
  exit 1
fi
echo "PASS unauthenticated GET /labs returns 401"

status="$(curl -s -o /dev/null -w '%{http_code}' -H "Authorization: Bearer invalid-token" "$base_url/labs")"
if [[ "$status" != "401" ]]; then
  echo "FAIL invalid token GET /labs expected 401, got $status" >&2
  exit 1
fi
echo "PASS invalid token GET /labs returns 401"

if [[ -n "$token_b" ]]; then
  status="$(curl -s -o /dev/null -w '%{http_code}' \
    -H "Authorization: Bearer $token_b" \
    "$base_url/labs/governance/run?tenant_id=other-tenant")"
  if [[ "$status" != "403" && "$status" != "401" ]]; then
    echo "FAIL cross-tenant request expected 401/403, got $status" >&2
    exit 1
  fi
  echo "PASS cross-tenant request denied"
else
  echo "SKIP cross-tenant check — STAGING_TEST_ACCESS_TOKEN_TENANT_B not set"
fi

echo "STAGING SMOKE PASS"
