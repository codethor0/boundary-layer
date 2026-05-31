#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PROD_ENV_FILE="${PROD_ENV_FILE:-.env.production}"
BACKUP_DIR="${BACKUP_DIR:-${ROOT}/backups/postgres}"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUTPUT="${BACKUP_DIR}/boundary-layer-${TIMESTAMP}.sql.gz"

detect_compose() {
  if docker compose --env-file "${PROD_ENV_FILE}" -f docker-compose.prod.yml -p boundary-layer-prod ps postgres -q 2>/dev/null | grep -q .; then
    echo "prod"
    return
  fi
  if docker compose ps postgres -q 2>/dev/null | grep -q .; then
    echo "dev"
    return
  fi
  echo "none"
}

STACK="$(detect_compose)"
if [[ "${STACK}" == "none" ]]; then
  echo "No running postgres container found" >&2
  exit 1
fi

mkdir -p "${BACKUP_DIR}"

if [[ "${STACK}" == "prod" ]]; then
  docker compose --env-file "${PROD_ENV_FILE}" -f docker-compose.prod.yml -p boundary-layer-prod \
    exec -T postgres pg_dump -U boundary_layer -d boundary_layer | gzip > "${OUTPUT}"
else
  docker compose exec -T postgres pg_dump -U boundary_layer -d boundary_layer | gzip > "${OUTPUT}"
fi

echo "Backup written to ${OUTPUT}"
