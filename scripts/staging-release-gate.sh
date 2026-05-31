#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "BoundaryLayer staging release gate"
echo ""

bash scripts/production-saas-staging-readiness-check.sh
bash scripts/production-saas-managed-services-check.sh
bash scripts/staging-deploy-dry-run.sh

if [[ -n "${STAGING_BASE_URL:-}" ]]; then
  bash scripts/staging-smoke-check.sh
else
  echo "SKIP staging-smoke-check — STAGING_BASE_URL not set"
fi

echo ""
echo "Staging release gate complete."
