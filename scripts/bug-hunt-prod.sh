#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PROD_ENV_FILE="${PROD_ENV_FILE:-.env.production}"
PROD_COMPOSE=(docker compose --env-file "${PROD_ENV_FILE}" -f docker-compose.prod.yml -p boundary-layer-prod)
API_URL="${API_URL:-https://localhost:8443}"
CURL=(curl --config /dev/null -k -s)
CURL_FAIL=(curl --config /dev/null -k -sf)

if [[ ! -f "${PROD_ENV_FILE}" ]]; then
  echo "Missing ${PROD_ENV_FILE}" >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "${PROD_ENV_FILE}"
set +a

failures=0

check() {
  local name="$1"
  local expected="$2"
  local actual="$3"
  if [[ "${actual}" == "${expected}" ]]; then
    echo "PASS ${name} (${actual})"
  else
    echo "FAIL ${name} expected=${expected} actual=${actual}"
    failures=$((failures + 1))
  fi
}

http_code() {
  "${CURL[@]}" -o /dev/null -w "%{http_code}" "$@" || true
}

ensure_prod_stack() {
  local code
  code="$(http_code "${API_URL}/health")"
  if [[ "${code}" != "200" ]]; then
    echo "==> Production stack not reachable (${code}); starting via make prod-up"
    make prod-up
    sleep 5
  fi
}

ensure_prod_stack

echo "==> Production bug-hunt checks"

check "health" "200" "$(http_code "${API_URL}/health")"
"${CURL_FAIL[@]}" "${API_URL}/health" | grep -q '"version":"1.3.2"' && echo "PASS health version payload" || {
  echo "FAIL health version payload"
  failures=$((failures + 1))
}

check "ready with metrics token" "200" "$(http_code \
  -H "Authorization: Bearer ${BOUNDARY_LAYER_METRICS_TOKEN}" \
  "${API_URL}/ready")"
check "ready without token" "401" "$(http_code "${API_URL}/ready")"

check "x-api-key auth" "200" "$(http_code \
  -H "X-API-Key: ${BOUNDARY_LAYER_API_KEY}" \
  -X POST "${API_URL}/labs/tool-router/run" \
  -H "Content-Type: application/json" \
  -d '{"mode":"hardened"}')"

check "metrics token cannot run labs" "401" "$(http_code \
  -H "Authorization: Bearer ${BOUNDARY_LAYER_METRICS_TOKEN}" \
  -X POST "${API_URL}/labs/redis/run" \
  -H "Content-Type: application/json" \
  -d '{"mode":"hardened"}')"

echo "==> Rate limit returns 429 not 503"
declare -A rate_counts=()
for _ in $(seq 1 120); do
  code="$(http_code \
    -H "Authorization: Bearer ${BOUNDARY_LAYER_API_KEY}" \
    "${API_URL}/labs")"
  rate_counts["${code}"]=$(( ${rate_counts["${code}"]:-0} + 1 ))
done
for code in "${!rate_counts[@]}"; do
  echo "  HTTP ${code}: ${rate_counts[${code}]}"
done
[[ -n "${rate_counts[429]:-}" ]] && echo "PASS saw HTTP 429" || {
  echo "FAIL no HTTP 429 under burst"
  failures=$((failures + 1))
}
[[ -z "${rate_counts[503]:-}" ]] && echo "PASS no HTTP 503 under burst" || {
  echo "FAIL saw HTTP 503 under burst"
  failures=$((failures + 1))
}

echo "==> Webhook storage cap (internal)"
"${PROD_COMPOSE[@]}" exec -T alert-webhook \
  curl -sf -X DELETE \
  -H "Authorization: Bearer ${BOUNDARY_LAYER_ALERT_WEBHOOK_TOKEN}" \
  http://localhost:8080/alerts >/dev/null || true

webhook_code="$("${PROD_COMPOSE[@]}" exec -T alert-webhook \
  curl -s -o /dev/null -w "%{http_code}" \
  -X POST http://localhost:8080/alerts \
  -H "Authorization: Bearer ${BOUNDARY_LAYER_ALERT_WEBHOOK_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "$(python3 -c 'import json; print(json.dumps({"alerts":[{"labels":{"a":"x"}}]*1001}))')")"
check "webhook rejects batch over cap" "413" "${webhook_code}"

echo "==> Backup roundtrip smoke"
backup_out="$(bash scripts/backup-postgres.sh)"
echo "${backup_out}"
backup_file="$(echo "${backup_out}" | awk '/Backup written to / {print $4}')"
if [[ ! -f "${backup_file}" ]]; then
  echo "FAIL backup file missing"
  failures=$((failures + 1))
else
  echo "PASS backup file created"
fi

if [[ "${failures}" -gt 0 ]]; then
  echo "Bug-hunt finished with ${failures} failure(s)"
  exit 1
fi

echo "Bug-hunt finished clean"
