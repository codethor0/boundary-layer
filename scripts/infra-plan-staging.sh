#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ "${CONFIRM_STAGING_PLAN:-}" != "true" ]]; then
  echo "Refusing to plan: set CONFIRM_STAGING_PLAN=true explicitly." >&2
  echo "This script performs terraform plan only and never applies changes." >&2
  exit 1
fi

if ! command -v terraform >/dev/null 2>&1; then
  echo "terraform is not installed" >&2
  exit 1
fi

if [[ -z "${TF_VAR_environment:-}" ]]; then
  echo "TF_VAR_environment is required (expected: staging)" >&2
  exit 1
fi

echo "BoundaryLayer staging terraform plan (plan only)"
terraform -chdir=infra/terraform init -backend=false >/dev/null
terraform -chdir=infra/terraform plan -input=false
echo "DRY PLAN ONLY: terraform apply was not executed"
