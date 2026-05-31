#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

API_URL="${API_URL:-http://localhost:8000}"
ALERT_WEBHOOK_URL="${ALERT_WEBHOOK_URL:-http://localhost:8081}"
LOG_FILE="${LOG_FILE:-}"
POLL_SECONDS="${POLL_SECONDS:-60}"

log_step() {
  [[ -n "$LOG_FILE" ]] || return 0
  local step="$1"
  local cmd="$2"
  local result="$3"
  local reason="${4:-}"
  {
    echo "### ${step}"
    echo "- Command: \`${cmd}\`"
    echo "- Result: ${result}"
    if [[ -n "$reason" ]]; then
      echo "- Failure reason: ${reason}"
    fi
    echo ""
  } >> "$LOG_FILE"
}

poll_webhook_alert() {
  local expected="$1"
  local elapsed=0
  while [[ "$elapsed" -lt "$POLL_SECONDS" ]]; do
    local body
    body=$(curl -sf "${ALERT_WEBHOOK_URL}/alerts" 2>/dev/null || true)
    if echo "$body" | grep -q "${expected}"; then
      echo "$body"
      return 0
    fi
    sleep 2
    elapsed=$((elapsed + 2))
  done
  return 1
}

echo "==> Extended alert delivery validation"

curl -sf -X DELETE "${ALERT_WEBHOOK_URL}/alerts" >/dev/null
log_step "Clear alert webhook store" "DELETE ${ALERT_WEBHOOK_URL}/alerts" "PASS"

echo "==> Circuit breaker alert"
curl -sf -X POST "${API_URL}/labs/circuit-breaker/run" \
  -H "Content-Type: application/json" \
  -d '{"mode":"hardened","requested_work_units":250}' >/dev/null
CB_STATE=$(curl -sf "${API_URL}/metrics" | awk '/^boundary_layer_inference_circuit_breaker_state / {print $2; exit}')
if [[ "${CB_STATE}" == "1" || "${CB_STATE}" == "1.0" ]]; then
  log_step "Circuit breaker metric open" "grep boundary_layer_inference_circuit_breaker_state" "PASS"
else
  log_step "Circuit breaker metric open" "grep boundary_layer_inference_circuit_breaker_state" "FAIL" "Expected 1, got ${CB_STATE}"
  echo "FAIL: circuit breaker gauge not open" >&2
  exit 1
fi

CB_ALERT="BoundaryLayerInferenceCircuitBreakerOpen"
if CB_BODY=$(poll_webhook_alert "$CB_ALERT"); then
  log_step "Alert delivered: ${CB_ALERT}" "GET ${ALERT_WEBHOOK_URL}/alerts" "PASS"
  echo "PASS ${CB_ALERT}"
else
  log_step "Alert delivered: ${CB_ALERT}" "GET ${ALERT_WEBHOOK_URL}/alerts" "FAIL" "Not received within ${POLL_SECONDS}s"
  echo "FAIL: ${CB_ALERT} not received within ${POLL_SECONDS}s" >&2
  exit 1
fi

curl -sf -X DELETE "${ALERT_WEBHOOK_URL}/alerts" >/dev/null

echo "==> Authz denial alert"
curl -sf -X POST "${API_URL}/labs/authz/run" \
  -H "Content-Type: application/json" -d '{"mode":"hardened"}' >/dev/null
if curl -sf "${API_URL}/metrics" | grep -q boundary_layer_authz_denied_total; then
  log_step "Authz denial metric present" "grep boundary_layer_authz_denied_total" "PASS"
else
  log_step "Authz denial metric present" "grep boundary_layer_authz_denied_total" "FAIL"
  echo "FAIL: boundary_layer_authz_denied_total missing" >&2
  exit 1
fi

AUTHZ_ALERT="BoundaryLayerAuthzDenied"
if AUTHZ_BODY=$(poll_webhook_alert "$AUTHZ_ALERT"); then
  log_step "Alert delivered: ${AUTHZ_ALERT}" "GET ${ALERT_WEBHOOK_URL}/alerts" "PASS"
  echo "PASS ${AUTHZ_ALERT}"
else
  log_step "Alert delivered: ${AUTHZ_ALERT}" "GET ${ALERT_WEBHOOK_URL}/alerts" "FAIL" "Not received within ${POLL_SECONDS}s"
  echo "FAIL: ${AUTHZ_ALERT} not received within ${POLL_SECONDS}s" >&2
  exit 1
fi

echo "Alert validation complete."
