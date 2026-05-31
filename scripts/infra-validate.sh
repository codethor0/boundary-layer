#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "BoundaryLayer infra validation"

if ! command -v terraform >/dev/null 2>&1; then
  echo "SKIP terraform fmt -check (terraform not installed)"
  echo "SKIP terraform validate (terraform not installed)"
  exit 0
fi

terraform -chdir=infra/terraform fmt -check -recursive
echo "PASS terraform fmt -check"

if [[ -d infra/terraform/.terraform ]]; then
  terraform -chdir=infra/terraform validate
  echo "PASS terraform validate"
else
  echo "SKIP terraform validate (providers not initialized; run terraform init manually)"
fi

for module in network container_service postgres redis object_storage secret_manager waf observability; do
  test -f "infra/terraform/modules/${module}/README.md"
done
echo "PASS terraform module skeleton present"
