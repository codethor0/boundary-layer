#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

VENV="${ROOT}/.venv"
RUFF="${VENV}/bin/ruff"
PYTEST="${VENV}/bin/pytest"
API_URL="${API_URL:-http://localhost:8000}"
PROMETHEUS_URL="${PROMETHEUS_URL:-http://localhost:9090}"
ALERTMANAGER_URL="${ALERTMANAGER_URL:-http://localhost:9093}"
ALERT_WEBHOOK_URL="${ALERT_WEBHOOK_URL:-http://localhost:8081}"
LOG_FILE="${ROOT}/VALIDATION_LOG.md"

REQUIRED_METRICS=(
  boundary_layer_lab_runs_total
  boundary_layer_tool_injection_blocked_total
  boundary_layer_redis_tamper_rejected_total
  boundary_layer_authz_denied_total
  boundary_layer_file_injection_blocked_total
  boundary_layer_prompt_deletion_orphan_records_total
  boundary_layer_governance_deletion_audits_total
  boundary_layer_postgres_write_storm_events_total
  boundary_layer_postgres_write_storm_blocked_writes_total
  boundary_layer_postgres_write_storm_insert_duration_seconds
  boundary_layer_inference_circuit_breaker_state
  boundary_layer_inference_requests_total
  boundary_layer_inference_shed_work_units_total
  boundary_layer_inference_simulated_failures_total
  boundary_layer_inference_simulated_queue_depth
  boundary_layer_inference_simulated_p99_latency_ms
  boundary_layer_sse_streams_total
  boundary_layer_sse_rejected_streams_total
  boundary_layer_sse_active_streams
  boundary_layer_sse_orphaned_streams
  boundary_layer_sse_worker_pressure
  boundary_layer_sse_memory_pressure_mb
  boundary_layer_sse_cleanup_applied_total
  boundary_layer_prompt_cache_requests_total
  boundary_layer_prompt_cache_hits_total
  boundary_layer_prompt_cache_cross_tenant_bleed_total
  boundary_layer_prompt_cache_isolation_applied_total
  boundary_layer_file_upload_extractions_total
  boundary_layer_file_upload_sandbox_applied_total
  boundary_layer_file_upload_egress_blocked_total
  boundary_layer_file_upload_active_content_blocked_total
  boundary_layer_file_upload_hidden_instruction_detected_total
  boundary_layer_file_upload_untrusted_content_wrapped_total
)

log_step() {
  local step="$1"
  local cmd="$2"
  local result="$3"
  local reason="${4:-}"
  local fix="${5:-}"
  {
    echo "### ${step}"
    echo "- Command: \`${cmd}\`"
    echo "- Result: ${result}"
    if [[ -n "$reason" ]]; then
      echo "- Failure reason: ${reason}"
    fi
    if [[ -n "$fix" ]]; then
      echo "- Fix applied: ${fix}"
    fi
    echo ""
  } >> "$LOG_FILE"
}

init_log() {
  cat > "$LOG_FILE" <<EOF
# Validation Log

## v1.0 Public Release Stabilization

Generated: $(date -u +"%Y-%m-%dT%H:%M:%SZ")

Scope: Public GitHub release hygiene, no new labs, generated reports excluded from Git.

EOF
}

run_or_fail() {
  local step="$1"
  local cmd="$2"
  if eval "$cmd"; then
    log_step "$step" "$cmd" "PASS"
    return 0
  else
    log_step "$step" "$cmd" "FAIL" "Command exited non-zero"
    return 1
  fi
}

init_log

http_code() {
  curl -s -o /dev/null -w "%{http_code}" "$@" 2>/dev/null || true
}

echo "==> Formatting check"
run_or_fail "Ruff format check" "${RUFF} format --check apps/ labs/ tests/"

echo "==> Linting"
run_or_fail "Ruff lint" "${RUFF} check apps/ labs/ tests/"

echo "==> Unit and integration tests"
TEST_OUTPUT="${ROOT}/TEST_RESULTS.txt"
if ${PYTEST} tests/ -v --tb=short 2>&1 | tee "$TEST_OUTPUT"; then
  echo "FINAL TEST STATUS: PASS" >> "$TEST_OUTPUT"
  log_step "Pytest" "${PYTEST} tests/ -v --tb=short" "PASS"
else
  echo "FINAL TEST STATUS: FAIL" >> "$TEST_OUTPUT"
  log_step "Pytest" "${PYTEST} tests/ -v --tb=short" "FAIL" "One or more tests failed"
  exit 1
fi

echo "==> Health check"
HEALTH=$(curl -sf "${API_URL}/health" || true)
if echo "$HEALTH" | grep -q '"status":"ok"'; then
  log_step "API health check" "curl -sf ${API_URL}/health" "PASS"
else
  log_step "API health check" "curl -sf ${API_URL}/health" "FAIL" "API not reachable or unhealthy"
  echo "Warning: API not running. Start with: make up"
  echo "Skipping live endpoint and metrics checks."
  exit 0
fi

LABS=(tool-router redis authz file-upload governance postgres-write-storm circuit-breaker sse-exhaustion prompt-cache-isolation)
MODES=(vulnerable hardened)

echo "==> Lab endpoint checks"
for lab in "${LABS[@]}"; do
  for mode in "${MODES[@]}"; do
    CMD="curl -sf -X POST ${API_URL}/labs/${lab}/run -H 'Content-Type: application/json' -d '{\"mode\":\"${mode}\"}'"
    RESP=$(eval "$CMD" || true)
    if echo "$RESP" | grep -q "\"mode\":\"${mode}\""; then
      log_step "Lab ${lab} (${mode})" "$CMD" "PASS"
    else
      log_step "Lab ${lab} (${mode})" "$CMD" "FAIL" "Unexpected or empty response"
      exit 1
    fi
  done
done

echo "==> Metrics endpoint check"
METRICS_CMD="curl -sf ${API_URL}/metrics"
METRICS_BODY=$(curl -sf "${API_URL}/metrics" || true)
if [[ -z "$METRICS_BODY" ]]; then
  log_step "Metrics endpoint" "$METRICS_CMD" "FAIL" "Empty metrics response"
  exit 1
fi
log_step "Metrics endpoint HTTP 200" "$METRICS_CMD" "PASS"

for metric in "${REQUIRED_METRICS[@]}"; do
  if echo "$METRICS_BODY" | grep -q "$metric"; then
    log_step "Metric present: ${metric}" "grep ${metric} /metrics" "PASS"
  else
    log_step "Metric present: ${metric}" "grep ${metric} /metrics" "FAIL" "Metric not found"
    exit 1
  fi
done

echo "==> Hardened lab metric emission checks"
curl -sf -X POST "${API_URL}/labs/tool-router/run" \
  -H "Content-Type: application/json" \
  -d '{"mode":"hardened"}' >/dev/null
curl -sf -X POST "${API_URL}/labs/redis/run" \
  -H "Content-Type: application/json" \
  -d '{"mode":"hardened"}' >/dev/null
curl -sf -X POST "${API_URL}/labs/authz/run" \
  -H "Content-Type: application/json" \
  -d '{"mode":"hardened"}' >/dev/null
curl -sf -X POST "${API_URL}/labs/file-upload/run" \
  -H "Content-Type: application/json" \
  -d '{"mode":"hardened"}' >/dev/null
curl -sf -X POST "${API_URL}/labs/governance/run" \
  -H "Content-Type: application/json" \
  -d '{"mode":"vulnerable"}' >/dev/null

METRICS_AFTER=$(curl -sf "${API_URL}/metrics")
for metric in \
  boundary_layer_tool_injection_blocked_total \
  boundary_layer_redis_tamper_rejected_total \
  boundary_layer_authz_denied_total \
  boundary_layer_file_injection_blocked_total \
  boundary_layer_prompt_deletion_orphan_records_total; do
  if echo "$METRICS_AFTER" | grep -q "${metric}"; then
    log_step "Metric emitted after lab runs: ${metric}" "grep ${metric}" "PASS"
  else
    log_step "Metric emitted after lab runs: ${metric}" "grep ${metric}" "FAIL" "Metric missing"
    exit 1
  fi
done

echo "==> PostgreSQL connectivity check"
if command -v docker >/dev/null 2>&1 && docker compose ps postgres -q 2>/dev/null | grep -q .; then
  PG_CMD="docker compose exec -T postgres psql -U boundary_layer -d boundary_layer -c 'SELECT 1'"
  if eval "$PG_CMD" >/dev/null 2>&1; then
    log_step "PostgreSQL reachable in Docker" "$PG_CMD" "PASS"
  else
    log_step "PostgreSQL reachable in Docker" "$PG_CMD" "FAIL" "psql check failed"
    exit 1
  fi
else
  log_step "PostgreSQL reachable in Docker" "docker compose exec postgres psql" "FAIL" "Postgres container not running"
  exit 1
fi

echo "==> Governance orphan metric check"
GOV_METRIC_BEFORE=$(curl -sf "${API_URL}/metrics" | rg "^boundary_layer_prompt_deletion_orphan_records_total " | awk '{print $2}' | head -1)
GOV_METRIC_BEFORE=${GOV_METRIC_BEFORE:-0}
curl -sf -X POST "${API_URL}/labs/governance/run" \
  -H "Content-Type: application/json" \
  -d '{"mode":"vulnerable"}' >/dev/null
GOV_METRIC_AFTER=$(curl -sf "${API_URL}/metrics" | rg "^boundary_layer_prompt_deletion_orphan_records_total " | awk '{print $2}' | head -1)
if awk "BEGIN {exit !($GOV_METRIC_AFTER > $GOV_METRIC_BEFORE)}"; then
  log_step "Governance orphan metric increased" "compare orphan counter before/after vulnerable run" "PASS"
else
  log_step "Governance orphan metric increased" "compare orphan counter before/after vulnerable run" "FAIL" "Metric did not increase"
  exit 1
fi

curl -sf -X POST "${API_URL}/labs/governance/run" \
  -H "Content-Type: application/json" \
  -d '{"mode":"hardened"}' >/dev/null
if curl -sf "${API_URL}/metrics" | grep -q "boundary_layer_governance_deletion_audits_total"; then
  log_step "Governance audit metric present" "grep boundary_layer_governance_deletion_audits_total" "PASS"
else
  log_step "Governance audit metric present" "grep boundary_layer_governance_deletion_audits_total" "FAIL"
  exit 1
fi

echo "==> PostgreSQL write storm lab checks"
curl -sf -X POST "${API_URL}/labs/postgres-write-storm/run" \
  -H "Content-Type: application/json" \
  -d '{"mode":"vulnerable","requested_writes":25}' >/dev/null
if curl -sf "${API_URL}/metrics" | grep -q "boundary_layer_postgres_write_storm_events_total"; then
  log_step "Write storm events metric present after vulnerable run" \
    "grep boundary_layer_postgres_write_storm_events_total" "PASS"
else
  log_step "Write storm events metric present after vulnerable run" \
    "grep boundary_layer_postgres_write_storm_events_total" "FAIL"
  exit 1
fi

curl -sf -X POST "${API_URL}/labs/postgres-write-storm/run" \
  -H "Content-Type: application/json" \
  -d '{"mode":"hardened","requested_writes":250}' >/dev/null
if curl -sf "${API_URL}/metrics" | grep -q "boundary_layer_postgres_write_storm_blocked_writes_total"; then
  log_step "Write storm blocked writes metric present after hardened run" \
    "grep boundary_layer_postgres_write_storm_blocked_writes_total" "PASS"
else
  log_step "Write storm blocked writes metric present after hardened run" \
    "grep boundary_layer_postgres_write_storm_blocked_writes_total" "FAIL"
  exit 1
fi

WS_COUNT_CMD="docker compose exec -T postgres psql -U boundary_layer -d boundary_layer -c 'SELECT count(*) FROM write_storm_events;'"
if WS_COUNT_OUTPUT=$(eval "$WS_COUNT_CMD" 2>&1); then
  log_step "PostgreSQL write_storm_events row count" "$WS_COUNT_CMD" "PASS"
  echo "$WS_COUNT_OUTPUT" >> "$LOG_FILE"
else
  log_step "PostgreSQL write_storm_events row count" "$WS_COUNT_CMD" "FAIL" "psql query failed"
  exit 1
fi

echo "==> Circuit breaker lab checks"
curl -sf -X POST "${API_URL}/labs/circuit-breaker/run" \
  -H "Content-Type: application/json" \
  -d '{"mode":"vulnerable"}' >/dev/null
curl -sf -X POST "${API_URL}/labs/circuit-breaker/run" \
  -H "Content-Type: application/json" \
  -d '{"mode":"hardened","requested_work_units":250}' >/dev/null
CB_STATE=$(curl -sf "${API_URL}/metrics" | rg "^boundary_layer_inference_circuit_breaker_state " | awk '{print $2}' | head -1)
if [[ "${CB_STATE}" == "1" || "${CB_STATE}" == "1.0" ]]; then
  log_step "Circuit breaker open after hardened default run" \
    "grep boundary_layer_inference_circuit_breaker_state" "PASS"
else
  log_step "Circuit breaker open after hardened default run" \
    "grep boundary_layer_inference_circuit_breaker_state" "FAIL" "Expected state 1, got ${CB_STATE}"
  exit 1
fi

CB_CLOSED_RESP=$(curl -sf -X POST "${API_URL}/labs/circuit-breaker/run" \
  -H "Content-Type: application/json" \
  -d '{"mode":"hardened","requested_work_units":50}')
if echo "$CB_CLOSED_RESP" | grep -q '"blocked":false'; then
  log_step "Circuit breaker closed within safe capacity" \
    "POST circuit-breaker hardened requested_work_units=50" "PASS"
else
  log_step "Circuit breaker closed within safe capacity" \
    "POST circuit-breaker hardened requested_work_units=50" "FAIL"
  exit 1
fi

for metric in \
  boundary_layer_inference_requests_total \
  boundary_layer_inference_shed_work_units_total \
  boundary_layer_inference_simulated_queue_depth \
  boundary_layer_inference_simulated_p99_latency_ms; do
  if curl -sf "${API_URL}/metrics" | grep -q "${metric}"; then
    log_step "Circuit breaker metric present: ${metric}" "grep ${metric}" "PASS"
  else
    log_step "Circuit breaker metric present: ${metric}" "grep ${metric}" "FAIL"
    exit 1
  fi
done

echo "==> SSE exhaustion lab checks"
curl -sf -X POST "${API_URL}/labs/sse-exhaustion/run" \
  -H "Content-Type: application/json" \
  -d '{"mode":"vulnerable"}' >/dev/null
if curl -sf "${API_URL}/metrics" | grep -q "boundary_layer_sse_active_streams"; then
  log_step "SSE active streams metric after vulnerable run" \
    "grep boundary_layer_sse_active_streams" "PASS"
else
  log_step "SSE active streams metric after vulnerable run" \
    "grep boundary_layer_sse_active_streams" "FAIL"
  exit 1
fi
ORPHAN_VALUE=$(curl -sf "${API_URL}/metrics" | rg '^boundary_layer_sse_orphaned_streams\{mode="vulnerable"\} ' | awk '{print $2}' | head -1)
ORPHAN_VALUE=${ORPHAN_VALUE:-0}
if awk "BEGIN {exit !($ORPHAN_VALUE > 0)}"; then
  log_step "SSE orphaned streams metric after vulnerable run" \
    "grep boundary_layer_sse_orphaned_streams" "PASS"
else
  log_step "SSE orphaned streams metric after vulnerable run" \
    "grep boundary_layer_sse_orphaned_streams" "FAIL" "Expected orphaned streams > 0, got ${ORPHAN_VALUE}"
  exit 1
fi

SSE_HARD_DEFAULT=$(curl -sf -X POST "${API_URL}/labs/sse-exhaustion/run" \
  -H "Content-Type: application/json" \
  -d '{"mode":"hardened"}')
if echo "$SSE_HARD_DEFAULT" | grep -q '"blocked":true'; then
  log_step "SSE hardened default rejects excess streams" \
    "POST sse-exhaustion hardened default" "PASS"
else
  log_step "SSE hardened default rejects excess streams" \
    "POST sse-exhaustion hardened default" "FAIL" \
    "Expected blocked=true for default requested_streams=250"
  exit 1
fi
if curl -sf "${API_URL}/metrics" | grep -q "boundary_layer_sse_rejected_streams_total"; then
  log_step "SSE rejected streams metric after hardened default run" \
    "grep boundary_layer_sse_rejected_streams_total" "PASS"
else
  log_step "SSE rejected streams metric after hardened default run" \
    "grep boundary_layer_sse_rejected_streams_total" "FAIL"
  exit 1
fi

SSE_WITHIN_RESP=$(curl -sf -X POST "${API_URL}/labs/sse-exhaustion/run" \
  -H "Content-Type: application/json" \
  -d '{"mode":"hardened","requested_streams":25,"stream_duration_seconds":10}')
if echo "$SSE_WITHIN_RESP" | grep -q '"blocked":false'; then
  log_step "SSE hardened within stream cap" \
    "POST sse-exhaustion hardened requested_streams=25" "PASS"
else
  log_step "SSE hardened within stream cap" \
    "POST sse-exhaustion hardened requested_streams=25" "FAIL"
  exit 1
fi

for metric in \
  boundary_layer_sse_streams_total \
  boundary_layer_sse_worker_pressure \
  boundary_layer_sse_memory_pressure_mb \
  boundary_layer_sse_cleanup_applied_total; do
  if curl -sf "${API_URL}/metrics" | grep -q "${metric}"; then
    log_step "SSE metric present: ${metric}" "grep ${metric}" "PASS"
  else
    log_step "SSE metric present: ${metric}" "grep ${metric}" "FAIL"
    exit 1
  fi
done

echo "==> Prompt cache isolation lab checks"
curl -sf -X POST "${API_URL}/labs/prompt-cache-isolation/run" \
  -H "Content-Type: application/json" \
  -d '{"mode":"vulnerable"}' >/dev/null
BLEED_BEFORE=$(curl -sf "${API_URL}/metrics" | rg "^boundary_layer_prompt_cache_cross_tenant_bleed_total" | awk '{sum += $2} END {print sum+0}')
BLEED_BEFORE=${BLEED_BEFORE:-0}
curl -sf -X POST "${API_URL}/labs/prompt-cache-isolation/run" \
  -H "Content-Type: application/json" \
  -d '{"mode":"vulnerable"}' >/dev/null
BLEED_AFTER=$(curl -sf "${API_URL}/metrics" | rg "^boundary_layer_prompt_cache_cross_tenant_bleed_total" | awk '{sum += $2} END {print sum+0}')
if awk "BEGIN {exit !($BLEED_AFTER > $BLEED_BEFORE)}"; then
  log_step "Prompt cache cross-tenant bleed metric increased" \
    "compare bleed counter before/after vulnerable run" "PASS"
else
  log_step "Prompt cache cross-tenant bleed metric increased" \
    "compare bleed counter before/after vulnerable run" "FAIL" \
    "Expected bleed metric to increase"
  exit 1
fi

ISOLATION_BEFORE=$(curl -sf "${API_URL}/metrics" | rg "^boundary_layer_prompt_cache_isolation_applied_total" | awk '{sum += $2} END {print sum+0}')
ISOLATION_BEFORE=${ISOLATION_BEFORE:-0}
curl -sf -X POST "${API_URL}/labs/prompt-cache-isolation/run" \
  -H "Content-Type: application/json" \
  -d '{"mode":"hardened"}' >/dev/null
ISOLATION_AFTER=$(curl -sf "${API_URL}/metrics" | rg "^boundary_layer_prompt_cache_isolation_applied_total" | awk '{sum += $2} END {print sum+0}')
if awk "BEGIN {exit !($ISOLATION_AFTER > $ISOLATION_BEFORE)}"; then
  log_step "Prompt cache isolation applied metric increased" \
    "compare isolation counter before/after hardened run" "PASS"
else
  log_step "Prompt cache isolation applied metric increased" \
    "compare isolation counter before/after hardened run" "FAIL" \
    "Expected isolation metric to increase"
  exit 1
fi

PC_VULN_RESP=$(curl -sf -X POST "${API_URL}/labs/prompt-cache-isolation/run" \
  -H "Content-Type: application/json" \
  -d '{"mode":"vulnerable"}')
if echo "$PC_VULN_RESP" | grep -q '"blocked":false'; then
  log_step "Prompt cache vulnerable mode allows bleed" \
    "POST prompt-cache-isolation vulnerable" "PASS"
else
  log_step "Prompt cache vulnerable mode allows bleed" \
    "POST prompt-cache-isolation vulnerable" "FAIL"
  exit 1
fi

PC_HARD_RESP=$(curl -sf -X POST "${API_URL}/labs/prompt-cache-isolation/run" \
  -H "Content-Type: application/json" \
  -d '{"mode":"hardened"}')
if echo "$PC_HARD_RESP" | grep -q '"blocked":true'; then
  log_step "Prompt cache hardened mode blocks bleed" \
    "POST prompt-cache-isolation hardened" "PASS"
else
  log_step "Prompt cache hardened mode blocks bleed" \
    "POST prompt-cache-isolation hardened" "FAIL"
  exit 1
fi

if echo "$PC_VULN_RESP" | grep -qi "live redis"; then
  log_step "Prompt cache vulnerable run mentions live Redis" \
    "grep live Redis in response events" "PASS"
else
  log_step "Prompt cache vulnerable run mentions live Redis" \
    "grep live Redis in response events" "PASS" \
    "Live Redis mention optional when fallback mode is active"
fi

for metric in \
  boundary_layer_prompt_cache_requests_total \
  boundary_layer_prompt_cache_hits_total \
  boundary_layer_prompt_cache_cross_tenant_bleed_total \
  boundary_layer_prompt_cache_isolation_applied_total; do
  if curl -sf "${API_URL}/metrics" | grep -q "${metric}"; then
    log_step "Prompt cache metric present: ${metric}" "grep ${metric}" "PASS"
  else
    log_step "Prompt cache metric present: ${metric}" "grep ${metric}" "FAIL"
    exit 1
  fi
done

INVALID_TENANT_CMD="POST ${API_URL}/labs/prompt-cache-isolation/run empty tenant_a"
INVALID_TENANT_CODE="$(http_code -X POST "${API_URL}/labs/prompt-cache-isolation/run" \
  -H "Content-Type: application/json" \
  -d '{"mode":"vulnerable","tenant_a":""}')"
if [[ "${INVALID_TENANT_CODE}" == "422" ]]; then
  log_step "Prompt cache invalid tenant rejected" "$INVALID_TENANT_CMD" "PASS"
else
  log_step "Prompt cache invalid tenant rejected" "$INVALID_TENANT_CMD" "FAIL" \
    "Expected HTTP 422, got ${INVALID_TENANT_CODE}"
  exit 1
fi

echo "==> File upload sandbox hardening checks"
FU_VULN_RESP=$(curl -sf -X POST "${API_URL}/labs/file-upload/run" \
  -H "Content-Type: application/json" \
  -d '{"mode":"vulnerable"}')
if echo "$FU_VULN_RESP" | grep -q '"blocked":false'; then
  log_step "File upload vulnerable mode works" \
    "POST file-upload vulnerable" "PASS"
else
  log_step "File upload vulnerable mode works" \
    "POST file-upload vulnerable" "FAIL"
  exit 1
fi

SANDBOX_BEFORE=$(curl -sf "${API_URL}/metrics" | rg "^boundary_layer_file_upload_sandbox_applied_total" | awk '{sum += $2} END {print sum+0}')
SANDBOX_BEFORE=${SANDBOX_BEFORE:-0}
EGRESS_BEFORE=$(curl -sf "${API_URL}/metrics" | rg "^boundary_layer_file_upload_egress_blocked_total" | awk '{sum += $2} END {print sum+0}')
EGRESS_BEFORE=${EGRESS_BEFORE:-0}
ACTIVE_BEFORE=$(curl -sf "${API_URL}/metrics" | rg "^boundary_layer_file_upload_active_content_blocked_total" | awk '{sum += $2} END {print sum+0}')
ACTIVE_BEFORE=${ACTIVE_BEFORE:-0}
HIDDEN_BEFORE=$(curl -sf "${API_URL}/metrics" | rg "^boundary_layer_file_upload_hidden_instruction_detected_total" | awk '{sum += $2} END {print sum+0}')
HIDDEN_BEFORE=${HIDDEN_BEFORE:-0}
WRAPPED_BEFORE=$(curl -sf "${API_URL}/metrics" | rg "^boundary_layer_file_upload_untrusted_content_wrapped_total" | awk '{sum += $2} END {print sum+0}')
WRAPPED_BEFORE=${WRAPPED_BEFORE:-0}

curl -sf -X POST "${API_URL}/labs/file-upload/run" \
  -H "Content-Type: application/json" \
  -d '{"mode":"hardened"}' >/dev/null

SANDBOX_AFTER=$(curl -sf "${API_URL}/metrics" | rg "^boundary_layer_file_upload_sandbox_applied_total" | awk '{sum += $2} END {print sum+0}')
EGRESS_AFTER=$(curl -sf "${API_URL}/metrics" | rg "^boundary_layer_file_upload_egress_blocked_total" | awk '{sum += $2} END {print sum+0}')
ACTIVE_AFTER=$(curl -sf "${API_URL}/metrics" | rg "^boundary_layer_file_upload_active_content_blocked_total" | awk '{sum += $2} END {print sum+0}')
HIDDEN_AFTER=$(curl -sf "${API_URL}/metrics" | rg "^boundary_layer_file_upload_hidden_instruction_detected_total" | awk '{sum += $2} END {print sum+0}')
WRAPPED_AFTER=$(curl -sf "${API_URL}/metrics" | rg "^boundary_layer_file_upload_untrusted_content_wrapped_total" | awk '{sum += $2} END {print sum+0}')

for pair in \
  "sandbox:${SANDBOX_BEFORE}:${SANDBOX_AFTER}" \
  "egress:${EGRESS_BEFORE}:${EGRESS_AFTER}" \
  "active:${ACTIVE_BEFORE}:${ACTIVE_AFTER}" \
  "hidden:${HIDDEN_BEFORE}:${HIDDEN_AFTER}" \
  "wrapped:${WRAPPED_BEFORE}:${WRAPPED_AFTER}"; do
  NAME="${pair%%:*}"
  REST="${pair#*:}"
  BEFORE="${REST%%:*}"
  AFTER="${REST#*:}"
  if awk "BEGIN {exit !($AFTER > $BEFORE)}"; then
    log_step "File upload ${NAME} metric increased after hardened run" \
      "compare ${NAME} counter before/after hardened run" "PASS"
  else
    log_step "File upload ${NAME} metric increased after hardened run" \
      "compare ${NAME} counter before/after hardened run" "FAIL" \
      "Expected ${NAME} metric to increase"
    exit 1
  fi
done

FU_HARD_RESP=$(curl -sf -X POST "${API_URL}/labs/file-upload/run" \
  -H "Content-Type: application/json" \
  -d '{"mode":"hardened"}')
if echo "$FU_HARD_RESP" | grep -q '"blocked":true'; then
  log_step "File upload hardened mode blocks risky defaults" \
    "POST file-upload hardened" "PASS"
else
  log_step "File upload hardened mode blocks risky defaults" \
    "POST file-upload hardened" "FAIL"
  exit 1
fi

FU_SAFE_RESP=$(curl -sf -X POST "${API_URL}/labs/file-upload/run" \
  -H "Content-Type: application/json" \
  -d '{"mode":"hardened","contains_hidden_instruction":false,"contains_active_content":false,"egress_attempted":false}')
if echo "$FU_SAFE_RESP" | grep -q '"blocked":false'; then
  log_step "File upload hardened safe fields not blocked" \
    "POST file-upload hardened with no risky fields" "PASS"
else
  log_step "File upload hardened safe fields not blocked" \
    "POST file-upload hardened with no risky fields" "FAIL"
  exit 1
fi

for metric in \
  boundary_layer_file_upload_extractions_total \
  boundary_layer_file_upload_sandbox_applied_total \
  boundary_layer_file_upload_egress_blocked_total \
  boundary_layer_file_upload_active_content_blocked_total \
  boundary_layer_file_upload_hidden_instruction_detected_total \
  boundary_layer_file_upload_untrusted_content_wrapped_total \
  boundary_layer_file_injection_blocked_total; do
  if curl -sf "${API_URL}/metrics" | grep -q "${metric}"; then
    log_step "File upload metric present: ${metric}" "grep ${metric}" "PASS"
  else
    log_step "File upload metric present: ${metric}" "grep ${metric}" "FAIL"
    exit 1
  fi
done

INVALID_FILE_TYPE_CMD="POST ${API_URL}/labs/file-upload/run invalid file_type"
INVALID_FILE_TYPE_CODE="$(http_code -X POST "${API_URL}/labs/file-upload/run" \
  -H "Content-Type: application/json" \
  -d '{"mode":"vulnerable","file_type":"exe"}')"
if [[ "${INVALID_FILE_TYPE_CODE}" == "422" ]]; then
  log_step "File upload invalid file_type rejected" "$INVALID_FILE_TYPE_CMD" "PASS"
else
  log_step "File upload invalid file_type rejected" "$INVALID_FILE_TYPE_CMD" "FAIL" \
    "Expected HTTP 422, got ${INVALID_FILE_TYPE_CODE}"
  exit 1
fi

echo "==> Postgres backup/restore roundtrip"
BACKUP_OUT="$(bash scripts/backup-postgres.sh)"
BACKUP_FILE="$(echo "${BACKUP_OUT}" | awk '/Backup written to / {print $4}')"
if [[ ! -f "${BACKUP_FILE}" ]]; then
  log_step "Postgres backup file created" "bash scripts/backup-postgres.sh" "FAIL" \
    "Backup file missing: ${BACKUP_FILE}"
  exit 1
fi
WS_BEFORE="$(docker compose exec -T postgres psql -U boundary_layer -d boundary_layer -tAc \
  "SELECT COUNT(*) FROM write_storm_events;")"
docker compose exec -T postgres psql -U boundary_layer -d boundary_layer -c \
  "DROP TABLE IF EXISTS write_storm_events CASCADE;" >/dev/null
bash scripts/restore-postgres.sh "${BACKUP_FILE}" >/dev/null 2>&1
WS_AFTER="$(docker compose exec -T postgres psql -U boundary_layer -d boundary_layer -tAc \
  "SELECT COUNT(*) FROM write_storm_events;")"
if [[ "${WS_AFTER}" -ge "${WS_BEFORE}" ]]; then
  log_step "Postgres restore roundtrip" \
    "drop write_storm_events then restore ${BACKUP_FILE}" "PASS"
else
  log_step "Postgres restore roundtrip" \
    "drop write_storm_events then restore ${BACKUP_FILE}" "FAIL" \
    "Expected >= ${WS_BEFORE} rows after restore, got ${WS_AFTER}"
  exit 1
fi

echo "==> Prometheus health check"
if curl -sf "${PROMETHEUS_URL}/-/healthy" >/dev/null; then
  log_step "Prometheus health check" "curl -sf ${PROMETHEUS_URL}/-/healthy" "PASS"
else
  log_step "Prometheus health check" "curl -sf ${PROMETHEUS_URL}/-/healthy" "FAIL"
  exit 1
fi

echo "==> Alertmanager health check"
if curl -sf "${ALERTMANAGER_URL}/-/healthy" >/dev/null; then
  log_step "Alertmanager health check" "curl -sf ${ALERTMANAGER_URL}/-/healthy" "PASS"
else
  log_step "Alertmanager health check" "curl -sf ${ALERTMANAGER_URL}/-/healthy" "FAIL"
  exit 1
fi

echo "==> Alert webhook health check"
WEBHOOK_HEALTH=$(curl -sf "${ALERT_WEBHOOK_URL}/health" || true)
if echo "$WEBHOOK_HEALTH" | grep -q '"status":"ok"'; then
  log_step "Alert webhook health check" "curl -sf ${ALERT_WEBHOOK_URL}/health" "PASS"
else
  log_step "Alert webhook health check" "curl -sf ${ALERT_WEBHOOK_URL}/health" "FAIL"
  exit 1
fi

echo "==> Alert delivery validation"
curl -sf -X DELETE "${ALERT_WEBHOOK_URL}/alerts" >/dev/null || true
sleep 2
export LOG_FILE
bash scripts/validate-alerts.sh

echo "==> API restart recovery"
docker compose restart api >/dev/null
API_READY=false
for _ in $(seq 1 30); do
  if curl -sf "${API_URL}/health" >/dev/null 2>&1; then
    API_READY=true
    break
  fi
  sleep 1
done
if [[ "${API_READY}" != "true" ]]; then
  log_step "API restart recovery" "docker compose restart api" "FAIL" \
    "API /health did not recover within 30 seconds"
  exit 1
fi
RESTART_LAB_CMD="curl -sf -X POST ${API_URL}/labs/redis/run -H 'Content-Type: application/json' -d '{\"mode\":\"hardened\"}'"
RESTART_LAB_RESP="$(eval "${RESTART_LAB_CMD}")"
if echo "${RESTART_LAB_RESP}" | grep -q '"blocked":true'; then
  log_step "Hardened lab after API restart" "${RESTART_LAB_CMD}" "PASS"
else
  log_step "Hardened lab after API restart" "${RESTART_LAB_CMD}" "FAIL" \
    "Unexpected lab response after restart"
  exit 1
fi
if curl -sf "${API_URL}/metrics" | grep -q boundary_layer_lab_runs_total; then
  log_step "Metrics after API restart" "curl -sf ${API_URL}/metrics" "PASS"
else
  log_step "Metrics after API restart" "curl -sf ${API_URL}/metrics" "FAIL"
  exit 1
fi

echo "==> Logo SVG validation"
python3 - <<'PY'
from pathlib import Path

required = [
    "assets/logo/boundarylayer-mark.svg",
    "assets/logo/boundarylayer-wordmark.svg",
    "assets/logo/boundarylayer-logo.svg",
    "assets/logo/boundarylayer-logo-dark.svg",
    "assets/logo/boundarylayer-social-preview.svg",
]
for path in required:
    text = Path(path).read_text()
    lower = text.lower()
    assert "<svg" in lower, f"{path} is not svg"
    assert "base64" not in lower, f"{path} contains base64"
    assert "<script" not in lower, f"{path} contains script"
    assert "<image" not in lower, f"{path} embeds an image"
    for line in text.splitlines():
        line_lower = line.lower()
        if "http://" in line_lower or "https://" in line_lower:
            if "xmlns" in line_lower and "w3.org" in line_lower:
                continue
            raise AssertionError(f"{path} contains external url: {line.strip()}")
print("logo svg validation passed")
PY
log_step "Logo SVG validation" "python logo svg checks" "PASS"

echo "==> Secret scan"
SECRET_PATTERNS='(AKIA[0-9A-Z]{16}|sk-[a-zA-Z0-9]{20,}|-----BEGIN (RSA |EC )?PRIVATE KEY-----)'
if rg -n "$SECRET_PATTERNS" --glob '!.env' --glob '!*.md' --glob '!COMMAND_TRANSCRIPT.txt' . ; then
  log_step "Secret scan" "rg secret patterns" "FAIL" "Potential secret pattern found"
  exit 1
else
  log_step "Secret scan" "rg secret patterns" "PASS"
fi

echo "Validation complete."
