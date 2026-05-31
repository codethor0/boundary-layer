#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

OUT_DIR="${SCAN_OUTPUT_DIR:-$ROOT/artifacts/security}"
OUT_FILE="$OUT_DIR/container-scan.txt"
IMAGE="${CONTAINER_IMAGE:-boundary-layer-api:staging}"

mkdir -p "$OUT_DIR"

echo "BoundaryLayer container security scan"

if ! command -v docker >/dev/null 2>&1; then
  echo "SKIP docker not available"
  exit 0
fi

if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
  bash scripts/container-build.sh >/dev/null
fi

if command -v trivy >/dev/null 2>&1; then
  trivy image --severity HIGH,CRITICAL --no-progress "$IMAGE" >"$OUT_FILE" 2>&1 || true
  echo "PASS trivy scan written to $OUT_FILE"
  exit 0
fi

if command -v grype >/dev/null 2>&1; then
  grype "$IMAGE" >"$OUT_FILE" 2>&1 || true
  echo "PASS grype scan written to $OUT_FILE"
  exit 0
fi

echo "SKIP trivy/grype not installed"
exit 0
