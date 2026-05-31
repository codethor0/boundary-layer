#!/usr/bin/env bash
set -euo pipefail

API_URL="${API_URL:-http://localhost:8000}"
ALERT_WEBHOOK_URL="${ALERT_WEBHOOK_URL:-http://localhost:8081}"
POLL_SECONDS="${POLL_SECONDS:-60}"

fail() {
  echo "DEMO FAIL: $*" >&2
  exit 1
}

require_api() {
  if ! curl -sf "${API_URL}/health" >/dev/null 2>&1; then
    echo "BoundaryLayer API is not running. Run make up first." >&2
    exit 1
  fi
}

poll_alert() {
  local name="$1"
  local elapsed=0
  while [[ "$elapsed" -lt "$POLL_SECONDS" ]]; do
    local body
    body=$(curl -sf "${ALERT_WEBHOOK_URL}/alerts" 2>/dev/null || true)
    if echo "$body" | grep -q "$name"; then
      echo "$body"
      return 0
    fi
    sleep 2
    elapsed=$((elapsed + 2))
  done
  return 1
}

echo "==> BoundaryLayer demo (local defensive security lab)"
require_api

HEALTH=$(curl -sf "${API_URL}/health")
echo "Health: ${HEALTH}"
echo ""

echo "==> Redis tampering (live Redis)"
VULN=$(curl -sf -X POST "${API_URL}/labs/redis/run" \
  -H "Content-Type: application/json" -d '{"mode":"vulnerable"}')
echo "$VULN" | grep -q '"blocked":false' || fail "redis vulnerable expected blocked=false"
echo "Vulnerable: blocked=false (privilege escalation accepted)"

HARD=$(curl -sf -X POST "${API_URL}/labs/redis/run" \
  -H "Content-Type: application/json" -d '{"mode":"hardened"}')
echo "$HARD" | grep -q '"blocked":true' || fail "redis hardened expected blocked=true"
echo "Hardened: blocked=true (HMAC verification rejected tamper)"
echo ""

echo "==> Prompt cache isolation (live Redis)"
PCV=$(curl -sf -X POST "${API_URL}/labs/prompt-cache-isolation/run" \
  -H "Content-Type: application/json" -d '{"mode":"vulnerable"}')
echo "$PCV" | grep -q '"blocked":false' || fail "prompt cache vulnerable expected blocked=false"
echo "Vulnerable: cross-tenant cache bleed possible"

PCH=$(curl -sf -X POST "${API_URL}/labs/prompt-cache-isolation/run" \
  -H "Content-Type: application/json" -d '{"mode":"hardened"}')
echo "$PCH" | grep -q '"blocked":true' || fail "prompt cache hardened expected blocked=true"
echo "Hardened: tenant-scoped isolation applied"
echo ""

echo "==> Key metrics"
curl -sf "${API_URL}/metrics" | grep -E \
  "boundary_layer_redis_tamper_rejected_total|boundary_layer_prompt_cache_isolation_applied_total|boundary_layer_lab_runs_total" \
  | head -6 || true
echo ""

echo "==> Circuit breaker alert path"
curl -sf -X DELETE "${ALERT_WEBHOOK_URL}/alerts" >/dev/null || fail "could not clear webhook"
curl -sf -X POST "${API_URL}/labs/circuit-breaker/run" \
  -H "Content-Type: application/json" -d '{"mode":"hardened"}' >/dev/null || fail "circuit breaker run failed"

CB=$(curl -sf "${API_URL}/metrics" | awk '/^boundary_layer_inference_circuit_breaker_state / {print $2; exit}')
if [[ "${CB}" != "1" && "${CB}" != "1.0" ]]; then
  fail "circuit breaker gauge not open (got ${CB:-empty})"
fi
echo "Metric boundary_layer_inference_circuit_breaker_state=1"

echo "Waiting up to ${POLL_SECONDS}s for BoundaryLayerInferenceCircuitBreakerOpen..."
if ALERT_BODY=$(poll_alert "BoundaryLayerInferenceCircuitBreakerOpen"); then
  echo "Alert delivered to local webhook."
  echo "$ALERT_BODY" | head -20
else
  fail "BoundaryLayerInferenceCircuitBreakerOpen not received within ${POLL_SECONDS}s"
fi

echo ""
echo "Demo complete."
echo "Next: make validate (full gate) | docs/OBSERVABILITY_WALKTHROUGH.md | docs/WORKSHOP.md"
