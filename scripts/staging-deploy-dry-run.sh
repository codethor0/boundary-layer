#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "BoundaryLayer staging deploy dry run"
echo "Mode: DRY RUN ONLY — no deployment will occur"
echo ""

required_env=(
  BOUNDARY_LAYER_PROFILE
  BOUNDARY_LAYER_ENV
  DATABASE_URL
  REDIS_URL
  SECRET_MANAGER_PROVIDER
  OBJECT_STORAGE_BUCKET
  BOUNDARY_LAYER_PUBLIC_BASE_URL
)

missing=()
for name in "${required_env[@]}"; do
  if [[ -z "${!name:-}" ]]; then
    missing+=("$name")
  fi
done

if ((${#missing[@]} > 0)); then
  echo "Missing required environment variables:"
  for name in "${missing[@]}"; do
    echo "  - $name"
  done
  exit 1
fi

required_paths=(
  infra/terraform/main.tf
  infra/terraform/envs/staging/README.md
  infra/terraform/modules/network/README.md
  infra/terraform/modules/container_service/README.md
  infra/terraform/modules/postgres/README.md
  infra/terraform/modules/redis/README.md
  infra/terraform/modules/object_storage/README.md
  infra/terraform/modules/secret_manager/README.md
)

for path in "${required_paths[@]}"; do
  if [[ ! -f "$path" ]]; then
    echo "Missing required IaC path: $path" >&2
    exit 1
  fi
done

release_image="${STAGING_RELEASE_IMAGE:-${RELEASE_IMAGE:-}}"
if [[ -z "$release_image" ]]; then
  echo "Missing STAGING_RELEASE_IMAGE or RELEASE_IMAGE (image tag reference required)." >&2
  exit 1
fi

echo "Environment profile: ${BOUNDARY_LAYER_PROFILE}"
echo "Environment name: ${BOUNDARY_LAYER_ENV}"
echo "Release image reference present: yes"
echo "Secret references present:"
echo "  - DATABASE_URL"
echo "  - REDIS_URL"
echo "  - SECRET_MANAGER_PROVIDER=${SECRET_MANAGER_PROVIDER}"
echo "  - SECRET_MANAGER_PROJECT_OR_PATH=${SECRET_MANAGER_PROJECT_OR_PATH:-<unset>}"
echo ""
echo "DRY RUN ONLY: deployment commands were not executed."
