#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

API_URL="${API_URL:-http://localhost:8000}"
ALERT_WEBHOOK_URL="${ALERT_WEBHOOK_URL:-http://localhost:8081}"
LOG_FILE="${LOG_FILE:-}"
DEFAULT_POLL_SECONDS="${POLL_SECONDS:-120}"
SCRAPE_WAIT_SECONDS="${SCRAPE_WAIT_SECONDS:-18}"

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
  local poll_seconds="${2:-$DEFAULT_POLL_SECONDS}"
  local elapsed=0
  while [[ "$elapsed" -lt "$poll_seconds" ]]; do
    local body
    body=$(curl -sf "${ALERT_WEBHOOK_URL}/alerts" 2>/dev/null || true)
    if WEBHOOK_BODY="$body" EXPECTED_ALERT="$expected" python3 - <<'PY'
import json
import os
import sys

raw = os.environ.get("WEBHOOK_BODY", "")
expected = os.environ.get("EXPECTED_ALERT", "")
try:
    payload = json.loads(raw or "{}")
except json.JSONDecodeError:
    sys.exit(1)

for alert in payload.get("alerts", []):
    if alert.get("status") != "firing":
        continue
    labels = alert.get("labels") or {}
    if labels.get("alertname") == expected:
        sys.exit(0)
sys.exit(1)
PY
    then
      echo "$body"
      return 0
    fi
    sleep 2
    elapsed=$((elapsed + 2))
  done
  return 1
}

clear_webhook() {
  curl -sf -X DELETE "${ALERT_WEBHOOK_URL}/alerts" >/dev/null
}

metric_present() {
  local metric_name="$1"
  curl -sf "${API_URL}/metrics" | grep -E "^${metric_name}(\\{| )" >/dev/null
}

validate_alert_delivery() {
  local alert_name="$1"
  local trigger_desc="$2"
  local trigger_cmd="$3"
  local metric_grep="${4:-}"
  local poll_seconds="${5:-$DEFAULT_POLL_SECONDS}"

  echo "==> ${alert_name}"
  clear_webhook
  log_step "Clear alert webhook store" "DELETE ${ALERT_WEBHOOK_URL}/alerts" "PASS"

  eval "$trigger_cmd"

  if [[ -n "$metric_grep" ]]; then
    sleep "${SCRAPE_WAIT_SECONDS}"
    if metric_present "$metric_grep"; then
      log_step "Metric present: ${metric_grep}" "grep ${metric_grep}" "PASS"
    else
      log_step "Metric present: ${metric_grep}" "grep ${metric_grep}" "FAIL"
      echo "FAIL: metric ${metric_grep} missing after ${trigger_desc}" >&2
      exit 1
    fi
  fi

  if poll_webhook_alert "$alert_name" "$poll_seconds"; then
    log_step "Alert delivered: ${alert_name}" "GET ${ALERT_WEBHOOK_URL}/alerts" "PASS"
    echo "PASS ${alert_name}"
  else
    log_step "Alert delivered: ${alert_name}" "GET ${ALERT_WEBHOOK_URL}/alerts" "FAIL" \
      "Not received within ${poll_seconds}s"
    echo "FAIL: ${alert_name} not received within ${poll_seconds}s" >&2
    exit 1
  fi
}

echo "==> Extended alert delivery validation"

clear_webhook
sleep 2

clear_webhook
curl -sf -X POST "${API_URL}/labs/circuit-breaker/run" \
  -H "Content-Type: application/json" \
  -d '{"mode":"hardened","requested_work_units":250}' >/dev/null
CB_STATE=$(curl -sf "${API_URL}/metrics" | awk '/^boundary_layer_inference_circuit_breaker_state / {print $2; exit}')
if [[ "${CB_STATE}" == "1" || "${CB_STATE}" == "1.0" ]]; then
  log_step "Circuit breaker metric open" "grep boundary_layer_inference_circuit_breaker_state" "PASS"
else
  echo "FAIL: circuit breaker gauge not open (got ${CB_STATE:-empty})" >&2
  exit 1
fi
sleep "${SCRAPE_WAIT_SECONDS}"
if poll_webhook_alert "BoundaryLayerInferenceCircuitBreakerOpen"; then
  echo "PASS BoundaryLayerInferenceCircuitBreakerOpen"
else
  echo "FAIL: BoundaryLayerInferenceCircuitBreakerOpen not received within ${DEFAULT_POLL_SECONDS}s" >&2
  exit 1
fi

validate_alert_delivery \
  "BoundaryLayerAuthzDenied" \
  "authz hardened" \
  "curl -sf -X POST ${API_URL}/labs/authz/run -H 'Content-Type: application/json' -d '{\"mode\":\"hardened\"}' >/dev/null" \
  "boundary_layer_authz_denied_total"

validate_alert_delivery \
  "BoundaryLayerRedisTamperRejected" \
  "redis hardened" \
  "curl -sf -X POST ${API_URL}/labs/redis/run -H 'Content-Type: application/json' -d '{\"mode\":\"hardened\"}' >/dev/null" \
  "boundary_layer_redis_tamper_rejected_total" \
  150

validate_alert_delivery \
  "BoundaryLayerPostgresWriteStormMitigated" \
  "postgres write storm hardened" \
  "curl -sf -X POST ${API_URL}/labs/postgres-write-storm/run -H 'Content-Type: application/json' -d '{\"mode\":\"hardened\",\"requested_writes\":250}' >/dev/null" \
  "boundary_layer_postgres_write_storm_blocked_writes_total"

validate_alert_delivery \
  "BoundaryLayerSSEBackpressureTriggered" \
  "sse exhaustion hardened default" \
  "curl -sf -X POST ${API_URL}/labs/sse-exhaustion/run -H 'Content-Type: application/json' -d '{\"mode\":\"hardened\"}' >/dev/null" \
  "boundary_layer_sse_rejected_streams_total"

validate_alert_delivery \
  "BoundaryLayerPromptDeletionIncomplete" \
  "governance vulnerable" \
  "curl -sf -X POST ${API_URL}/labs/governance/run -H 'Content-Type: application/json' -d '{\"mode\":\"vulnerable\"}' >/dev/null" \
  "boundary_layer_prompt_deletion_orphan_records_total"

echo "Alert validation complete (6 alerts)."
