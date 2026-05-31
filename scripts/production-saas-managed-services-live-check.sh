#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ "${RUN_LIVE_STAGING_CHECKS:-}" != "true" ]]; then
  echo "RUN_LIVE_STAGING_CHECKS must be true for live managed-service connectivity checks." >&2
  exit 1
fi

.venv/bin/python -m apps.api.managed_services
