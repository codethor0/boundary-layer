#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

API_URL="${API_URL:-http://localhost:8000}"
export BACKUP_DIR="${BACKUP_DIR:-${ROOT}/backups/postgres/restore-validation}"
KEEP_RESTORE_ARTIFACTS="${KEEP_RESTORE_ARTIFACTS:-false}"
WAIT_SECONDS="${WAIT_SECONDS:-120}"
mkdir -p "${BACKUP_DIR}"

fail() {
  echo "RESTORE VALIDATION FAIL: $*" >&2
  exit 1
}

log() {
  echo "==> $*"
}

wait_for_postgres() {
  local elapsed=0
  while [[ "$elapsed" -lt "$WAIT_SECONDS" ]]; do
    if docker compose exec -T postgres pg_isready -U boundary_layer -d boundary_layer >/dev/null 2>&1; then
      return 0
    fi
    sleep 2
    elapsed=$((elapsed + 2))
  done
  fail "PostgreSQL not ready within ${WAIT_SECONDS}s"
}

wait_for_api() {
  local elapsed=0
  while [[ "$elapsed" -lt "$WAIT_SECONDS" ]]; do
    if curl -sf "${API_URL}/health" >/dev/null 2>&1; then
      return 0
    fi
    sleep 2
    elapsed=$((elapsed + 2))
  done
  fail "API not ready within ${WAIT_SECONDS}s"
}

table_count() {
  local table="$1"
  docker compose exec -T postgres psql -U boundary_layer -d boundary_layer -tAc \
    "SELECT COUNT(*) FROM ${table};" | tr -d '[:space:]'
}

start_stack() {
  log "Starting fresh Docker Compose stack"
  docker compose up -d --build
  wait_for_postgres
  wait_for_api
}

SEED_REQUESTED_WRITES=25

seed_lab_data() {
  log "Seeding governance (hardened) and write storm (vulnerable, requested_writes=${SEED_REQUESTED_WRITES})"
  curl -sf -X POST "${API_URL}/labs/governance/run" \
    -H "Content-Type: application/json" -d '{"mode":"hardened"}' >/dev/null \
    || fail "governance lab run failed"
  curl -sf -X POST "${API_URL}/labs/postgres-write-storm/run" \
    -H "Content-Type: application/json" -d "{\"mode\":\"vulnerable\",\"requested_writes\":${SEED_REQUESTED_WRITES}}" >/dev/null \
    || fail "postgres write storm lab run failed"
}

log "Fresh-volume PostgreSQL restore validation (local dev stack only)"
log "This removes BoundaryLayer dev Compose volumes and recreates them."

log "Tearing down dev stack and volumes"
docker compose down -v >/dev/null

start_stack
seed_lab_data

WS_BEFORE="$(table_count write_storm_events)"
AUDIT_BEFORE="$(table_count deletion_audit)"

if [[ "${WS_BEFORE}" -lt 1 ]]; then
  fail "Expected write_storm_events rows before backup, got ${WS_BEFORE}"
fi
if [[ "${WS_BEFORE}" -ne "${SEED_REQUESTED_WRITES}" ]]; then
  fail "Expected write_storm_events=${SEED_REQUESTED_WRITES} before backup, got ${WS_BEFORE}"
fi
if [[ "${AUDIT_BEFORE}" -lt 1 ]]; then
  fail "Expected deletion_audit rows before backup, got ${AUDIT_BEFORE}"
fi

log "Row counts before backup: write_storm_events=${WS_BEFORE}, deletion_audit=${AUDIT_BEFORE}"

BACKUP_OUT="$(bash scripts/backup-postgres.sh)"
BACKUP_FILE="$(echo "${BACKUP_OUT}" | awk '/Backup written to / {print $4}')"
if [[ ! -f "${BACKUP_FILE}" ]]; then
  fail "Backup file missing: ${BACKUP_FILE}"
fi
log "Backup path: ${BACKUP_FILE}"

log "Destroying PostgreSQL volume (simulated volume loss)"
docker compose down -v >/dev/null

start_stack

log "Restoring full database from backup into fresh volume"
bash scripts/restore-postgres.sh "${BACKUP_FILE}" >/dev/null

WS_AFTER="$(table_count write_storm_events)"
AUDIT_AFTER="$(table_count deletion_audit)"

log "Row counts after restore: write_storm_events=${WS_AFTER}, deletion_audit=${AUDIT_AFTER}"

if [[ "${WS_AFTER}" -lt "${WS_BEFORE}" ]]; then
  fail "write_storm_events count dropped (${WS_BEFORE} -> ${WS_AFTER})"
fi
if [[ "${WS_AFTER}" -ne "${SEED_REQUESTED_WRITES}" ]]; then
  fail "Expected write_storm_events=${SEED_REQUESTED_WRITES} after restore, got ${WS_AFTER}"
fi
if [[ "${AUDIT_AFTER}" -lt "${AUDIT_BEFORE}" ]]; then
  fail "deletion_audit count dropped (${AUDIT_BEFORE} -> ${AUDIT_AFTER})"
fi

if [[ "${KEEP_RESTORE_ARTIFACTS}" != "true" ]]; then
  rm -f "${BACKUP_FILE}"
  log "Removed temporary backup (set KEEP_RESTORE_ARTIFACTS=true to keep)"
else
  log "Kept backup at ${BACKUP_FILE}"
fi

echo "RESTORE VALIDATION PASS"
echo "Tables checked: write_storm_events, deletion_audit"
echo "Before backup: write_storm_events=${WS_BEFORE}, deletion_audit=${AUDIT_BEFORE}"
echo "After restore: write_storm_events=${WS_AFTER}, deletion_audit=${AUDIT_AFTER}"
