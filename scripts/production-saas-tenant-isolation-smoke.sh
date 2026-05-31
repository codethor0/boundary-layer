#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "==> Production SaaS tenant isolation unit smoke"
.venv/bin/pytest \
  tests/unit/test_production_saas_tenant_isolation.py \
  tests/unit/test_db.py \
  tests/unit/test_tenancy.py \
  tests/unit/test_auth.py::test_resolve_request_tenant_denies_cross_tenant_in_production_saas \
  tests/unit/test_auth.py::test_resolve_request_tenant_allows_admin_override \
  -q
echo "Production SaaS tenant isolation smoke complete."
