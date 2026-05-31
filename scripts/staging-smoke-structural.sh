#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

STAGING_SMOKE_MODE=structural \
  STAGING_BASE_URL="${STAGING_BASE_URL:-https://staging.example.com}" \
  STAGING_TEST_ACCESS_TOKEN_TENANT_A="${STAGING_TEST_ACCESS_TOKEN_TENANT_A:-staging-test-token-tenant-a-minimum-24}" \
  STAGING_METRICS_AUTH_TOKEN="${STAGING_METRICS_AUTH_TOKEN:-staging-metrics-token-minimum-24}" \
  bash scripts/staging-smoke-check.sh
