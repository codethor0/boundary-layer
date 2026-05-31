#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

API_URL="${API_URL:-http://localhost:8000}"
ALERT_WEBHOOK_URL="${ALERT_WEBHOOK_URL:-http://localhost:8081}"
ASSETS_DIR="${ROOT}/docs/assets"
OUTPUT="${ASSETS_DIR}/demo-transcript.txt"
CAST_OUTPUT="${ASSETS_DIR}/boundary-layer-demo.cast"

mkdir -p "${ASSETS_DIR}"

if ! curl -sf "${API_URL}/health" >/dev/null 2>&1; then
  echo "BoundaryLayer API is not running. Run make up first." >&2
  exit 1
fi

sanitize() {
  sed -E \
    -e "s#${HOME}#~#g" \
    -e 's#/Users/[^/[:space:]]+#~#g' \
    -e 's#/home/[^/[:space:]]+#~#g' \
    -e 's/sk-[a-zA-Z0-9]{20,}/[REDACTED]/g' \
    -e 's/AKIA[0-9A-Z]{16}/[REDACTED]/g'
}

{
  echo "# BoundaryLayer demo transcript (sanitized)"
  echo "# Generated: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
  echo "# Commands: make smoke, make demo, metrics sample, alerts sample"
  echo ""
  echo "## make smoke"
  bash scripts/smoke.sh 2>&1 || true
  echo ""
  echo "## make demo"
  bash scripts/demo.sh 2>&1 || true
  echo ""
  echo "## metrics sample"
  curl -sf "${API_URL}/metrics" | grep -E \
    "boundary_layer_lab_runs_total|boundary_layer_inference_circuit_breaker_state|boundary_layer_redis_tamper" \
    | head -8 || true
  echo ""
  echo "## alerts sample"
  curl -sf "${ALERT_WEBHOOK_URL}/alerts" | head -c 1200 || true
  echo ""
} | sanitize > "${OUTPUT}"

echo "Wrote ${OUTPUT}"

if command -v asciinema >/dev/null 2>&1; then
  echo "asciinema found; recording cast to ${CAST_OUTPUT}"
  asciinema rec --overwrite -c "bash scripts/smoke.sh && bash scripts/demo.sh" "${CAST_OUTPUT}" || \
    echo "WARN: asciinema recording failed or was skipped"
else
  echo "asciinema not available; cast not recorded"
fi

if command -v agg >/dev/null 2>&1 && [[ -f "${CAST_OUTPUT}" ]]; then
  agg "${CAST_OUTPUT}" "${ASSETS_DIR}/boundary-layer-demo.gif" && \
    echo "Wrote ${ASSETS_DIR}/boundary-layer-demo.gif" || \
    echo "WARN: GIF generation failed"
else
  echo "GIF not generated because agg/asciinema capture tooling was not available."
fi
