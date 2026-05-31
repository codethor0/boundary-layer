#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

EVIDENCE_DIR="${EVIDENCE_DIR:-$ROOT/artifacts/live-evidence}"
REPORT_FILE="$EVIDENCE_DIR/LIVE_STAGING_EVIDENCE.md"
TIMESTAMP="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
GIT_SHA="$(git rev-parse --short HEAD 2>/dev/null || echo unknown)"

mkdir -p "$EVIDENCE_DIR"

echo "BoundaryLayer production SaaS evidence runner"

if ! bash scripts/check-live-staging-prereqs.sh >"$EVIDENCE_DIR/prereqs.txt" 2>&1; then
  cat "$EVIDENCE_DIR/prereqs.txt"
  echo ""
  echo "LIVE STAGING EVIDENCE CANNOT RUN"
  echo "Score remains capped at 6/10."
  exit 1
fi

failures=0
results=()

run_capture() {
  local label="$1"
  shift
  local outfile="$EVIDENCE_DIR/${label}.txt"
  if "$@" >"$outfile" 2>&1; then
    results+=("PASS $label")
  else
    results+=("FAIL $label")
    failures=$((failures + 1))
  fi
}

run_capture "managed-services-live" make production-saas-managed-services-live-check
run_capture "staging-smoke-live" make staging-smoke-live
run_capture "live-validation-package" make live-staging-validation-package

if bash scripts/waf-live-check.sh >"$EVIDENCE_DIR/waf-live.txt" 2>&1; then
  if grep -q "WAF LIVE CHECK SKIPPED" "$EVIDENCE_DIR/waf-live.txt"; then
    results+=("SKIP waf-live")
  else
    results+=("PASS waf-live")
  fi
else
  results+=("FAIL waf-live")
  failures=$((failures + 1))
fi

if bash scripts/audit-sink-live-check.sh >"$EVIDENCE_DIR/audit-sink-live.txt" 2>&1; then
  if grep -q "AUDIT SINK LIVE CHECK SKIPPED" "$EVIDENCE_DIR/audit-sink-live.txt"; then
    results+=("SKIP audit-sink-live")
  else
    results+=("PASS audit-sink-live")
  fi
else
  results+=("FAIL audit-sink-live")
  failures=$((failures + 1))
fi

if bash scripts/dr-restore-live-check.sh >"$EVIDENCE_DIR/dr-restore-live.txt" 2>&1; then
  if grep -q "DR LIVE CHECK SKIPPED" "$EVIDENCE_DIR/dr-restore-live.txt"; then
    results+=("SKIP dr-restore-live")
  else
    results+=("PASS dr-restore-live")
  fi
else
  results+=("FAIL dr-restore-live")
  failures=$((failures + 1))
fi

{
  echo "# Live Staging Evidence (sanitized)"
  echo ""
  echo "- Timestamp (UTC): $TIMESTAMP"
  echo "- Git commit: $GIT_SHA"
  echo "- RUN_LIVE_STAGING_CHECKS: true"
  echo "- STAGING_BASE_URL: configured (value redacted)"
  echo ""
  echo "## Step results"
  for line in "${results[@]}"; do
    echo "- $line"
  done
  echo ""
  if [[ "$failures" -gt 0 ]]; then
    echo "Overall: LIVE STAGING EVIDENCE FAIL"
  else
    echo "Overall: LIVE STAGING EVIDENCE PASS (core checks)"
  fi
  echo ""
  echo "See companion logs in artifacts/live-evidence/*.txt (no secrets stored)."
} >"$REPORT_FILE"

cat "$REPORT_FILE"

if [[ "$failures" -gt 0 ]]; then
  exit 1
fi

echo "Evidence report: $REPORT_FILE"
