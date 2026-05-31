#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "==> Production SaaS auth and tenancy unit smoke"
.venv/bin/pytest tests/unit/test_auth.py tests/unit/test_tenancy.py tests/unit/test_production_saas_api.py -q
echo "Production SaaS auth smoke complete."
