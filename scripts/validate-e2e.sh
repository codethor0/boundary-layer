#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "==> Unit tests and lint"
make test
make lint

echo "==> Dependency audit"
"${ROOT}/.venv/bin/pip" install -q pip-audit
"${ROOT}/.venv/bin/pip-audit" -r apps/api/requirements.txt

echo "==> Production validation"
make validate-prod

echo "==> Local lab validation"
make up
make validate

echo "End-to-end validation complete."
