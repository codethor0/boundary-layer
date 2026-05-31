#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 /path/to/backup.sql.gz" >&2
  exit 1
fi

BACKUP_FILE="$1"
PROD_ENV_FILE="${PROD_ENV_FILE:-.env.production}"

if [[ ! -f "${BACKUP_FILE}" ]]; then
  echo "Backup file not found: ${BACKUP_FILE}" >&2
  exit 1
fi

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

restore_cmd() {
  gunzip -c "${BACKUP_FILE}"
}

if [[ "${STACK}" == "prod" ]]; then
  restore_cmd | docker compose --env-file "${PROD_ENV_FILE}" -f docker-compose.prod.yml -p boundary-layer-prod \
    exec -T postgres psql -U boundary_layer -d boundary_layer
else
  restore_cmd | docker compose exec -T postgres psql -U boundary_layer -d boundary_layer
fi

echo "Restore completed from ${BACKUP_FILE}"
