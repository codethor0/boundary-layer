#!/usr/bin/env bash
set -euo pipefail

API_URL="${API_URL:-http://localhost:8000}"
PROMETHEUS_URL="${PROMETHEUS_URL:-http://localhost:9090}"
ALERT_WEBHOOK_URL="${ALERT_WEBHOOK_URL:-http://localhost:8081}"

fail() {
  echo "SMOKE FAIL: $*" >&2
  exit 1
}

require_api() {
  if ! curl -sf "${API_URL}/health" >/dev/null 2>&1; then
    echo "BoundaryLayer API is not running. Run make up first." >&2
    exit 1
  fi
}

echo "==> BoundaryLayer smoke check"
require_api

HEALTH=$(curl -sf "${API_URL}/health")
echo "PASS health: ${HEALTH}"

LABS=$(curl -sf "${API_URL}/labs")
echo "$LABS" | grep -q '"labs"' || fail "GET /labs missing labs array"
echo "PASS GET /labs"

METRICS=$(curl -sf "${API_URL}/metrics")
echo "$METRICS" | grep -q boundary_layer_lab_runs_total || fail "metrics missing lab runs counter"
echo "PASS GET /metrics"

if curl -sf "${PROMETHEUS_URL}/-/healthy" >/dev/null 2>&1; then
  echo "PASS Prometheus healthy"
else
  echo "WARN Prometheus not reachable (optional for smoke)"
fi

if curl -sf "${ALERT_WEBHOOK_URL}/health" >/dev/null 2>&1; then
  echo "PASS alert webhook healthy"
else
  echo "WARN alert webhook not reachable (optional for smoke)"
fi

VULN=$(curl -sf -X POST "${API_URL}/labs/redis/run" \
  -H "Content-Type: application/json" -d '{"mode":"vulnerable"}')
echo "$VULN" | grep -q '"blocked":false' || fail "redis vulnerable should not be blocked"
echo "PASS redis vulnerable"

HARD=$(curl -sf -X POST "${API_URL}/labs/redis/run" \
  -H "Content-Type: application/json" -d '{"mode":"hardened"}')
echo "$HARD" | grep -q '"blocked":true' || fail "redis hardened should be blocked"
echo "PASS redis hardened"

curl -sf -X POST "${API_URL}/labs/circuit-breaker/run" \
  -H "Content-Type: application/json" -d '{"mode":"hardened"}' >/dev/null || fail "circuit breaker run failed"
CB=$(curl -sf "${API_URL}/metrics" | awk '/^boundary_layer_inference_circuit_breaker_state / {print $2; exit}')
if [[ "${CB}" == "1" || "${CB}" == "1.0" ]]; then
  echo "PASS circuit breaker metric open"
else
  echo "WARN circuit breaker gauge not open (got ${CB:-empty})"
fi

echo "Smoke check complete."
