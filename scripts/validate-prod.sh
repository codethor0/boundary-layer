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
  echo "Missing ${PROD_ENV_FILE}. Copy .env.production.example and set secrets." >&2
  exit 1
fi

set -a
# shellcheck disable=SC1090
source "${PROD_ENV_FILE}"
set +a

require_var() {
  local name="$1"
  if [[ -z "${!name:-}" ]]; then
    echo "Missing required variable: ${name}" >&2
    exit 1
  fi
}

for var in \
  BOUNDARY_LAYER_API_KEY \
  BOUNDARY_LAYER_METRICS_TOKEN \
  BOUNDARY_LAYER_ALERT_WEBHOOK_TOKEN \
  POSTGRES_PASSWORD \
  SESSION_HMAC_SECRET \
  REDIS_PASSWORD; do
  require_var "$var"
done

echo "==> Rendering production observability configs"
bash deploy/scripts/render-prometheus-config.sh
bash deploy/scripts/render-alertmanager-config.sh

if [[ ! -f deploy/nginx/certs/boundary-layer.crt ]]; then
  echo "==> Generating self-signed TLS certificate"
  bash deploy/nginx/generate-certs.sh
fi

echo "==> Generating internal Postgres/Redis TLS material"
bash deploy/tls/generate-internal-ca.sh

echo "==> Stopping local and production stacks if running"
docker compose down --remove-orphans >/dev/null 2>&1 || true
"${PROD_COMPOSE[@]}" down -v --remove-orphans >/dev/null 2>&1 || true

echo "==> Starting production stack"
"${PROD_COMPOSE[@]}" up -d --build
sleep 15

echo "==> TLS health check"
"${CURL_FAIL[@]}" "${API_URL}/health" | grep -q '"version":"1.3.1"'

echo "==> Readiness check"
"${CURL_FAIL[@]}" \
  -H "Authorization: Bearer ${BOUNDARY_LAYER_METRICS_TOKEN}" \
  "${API_URL}/ready" | grep -q '"status":"ready"'

echo "==> OpenAPI docs disabled in production"
code="$("${CURL[@]}" -o /dev/null -w "%{http_code}" "${API_URL}/docs")" || true
[[ "$code" == "404" ]]

echo "==> Observability UIs not exposed via nginx"
code="$("${CURL[@]}" -o /dev/null -w "%{http_code}" "${API_URL}/prometheus/")" || true
[[ "$code" == "404" ]]
code="$("${CURL[@]}" -o /dev/null -w "%{http_code}" "${API_URL}/alertmanager/")" || true
[[ "$code" == "404" ]]

echo "==> Unauthenticated lab access rejected"
code="$("${CURL[@]}" -o /dev/null -w "%{http_code}" \
  -X POST "${API_URL}/labs/redis/run" \
  -H "Content-Type: application/json" \
  -d '{"mode":"hardened"}')" || true
[[ "$code" == "401" ]]

echo "==> Vulnerable mode blocked in production"
code="$("${CURL[@]}" -o /dev/null -w "%{http_code}" \
  -X POST "${API_URL}/labs/redis/run" \
  -H "Authorization: Bearer ${BOUNDARY_LAYER_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"mode":"vulnerable"}')" || true
[[ "$code" == "403" ]]

echo "==> Authenticated hardened lab run"
"${CURL_FAIL[@]}" \
  -X POST "${API_URL}/labs/redis/run" \
  -H "Authorization: Bearer ${BOUNDARY_LAYER_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"mode":"hardened"}' | grep -q '"blocked":true'

echo "==> Metrics auth enforced"
code="$("${CURL[@]}" -o /dev/null -w "%{http_code}" "${API_URL}/metrics")" || true
[[ "$code" == "401" ]]
"${CURL_FAIL[@]}" \
  -H "Authorization: Bearer ${BOUNDARY_LAYER_METRICS_TOKEN}" \
  "${API_URL}/metrics" | grep -q boundary_layer_lab_runs_total

echo "==> Webhook auth enforced (internal service check)"
code="$("${PROD_COMPOSE[@]}" exec -T alert-webhook \
  curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/alerts)" || true
[[ "$code" == "401" ]]

echo "==> Clearing alerts and triggering circuit breaker alert"
"${PROD_COMPOSE[@]}" exec -T alert-webhook \
  curl -sf -X DELETE \
  -H "Authorization: Bearer ${BOUNDARY_LAYER_ALERT_WEBHOOK_TOKEN}" \
  http://localhost:8080/alerts >/dev/null
"${CURL_FAIL[@]}" \
  -X POST "${API_URL}/labs/circuit-breaker/run" \
  -H "Authorization: Bearer ${BOUNDARY_LAYER_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"mode":"hardened"}' >/dev/null

for _ in $(seq 1 75); do
  if "${PROD_COMPOSE[@]}" exec -T alert-webhook \
    curl -sf \
    -H "Authorization: Bearer ${BOUNDARY_LAYER_ALERT_WEBHOOK_TOKEN}" \
    http://localhost:8080/alerts | grep -q BoundaryLayerInferenceCircuitBreakerOpen; then
    break
  fi
  sleep 1
done

"${PROD_COMPOSE[@]}" exec -T alert-webhook \
  curl -sf \
  -H "Authorization: Bearer ${BOUNDARY_LAYER_ALERT_WEBHOOK_TOKEN}" \
  http://localhost:8080/alerts | grep -q BoundaryLayerInferenceCircuitBreakerOpen

echo "==> Postgres backup smoke test"
bash scripts/backup-postgres.sh

echo "==> Stopping production stack"
"${PROD_COMPOSE[@]}" down -v --remove-orphans >/dev/null 2>&1 || true

echo "Production validation complete."
