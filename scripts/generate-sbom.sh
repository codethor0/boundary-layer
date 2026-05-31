#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

OUT_DIR="${SBOM_OUTPUT_DIR:-$ROOT/artifacts/security}"
OUT_FILE="$OUT_DIR/sbom.spdx.json"

mkdir -p "$OUT_DIR"

echo "BoundaryLayer SBOM generation"

if ! command -v syft >/dev/null 2>&1; then
  echo "SKIP syft not installed (install: https://github.com/anchore/syft)"
  exit 0
fi

git_sha="$(git rev-parse --short HEAD 2>/dev/null || echo unknown)"
syft packages dir:"$ROOT/apps/api" -o spdx-json >"$OUT_FILE"
echo "PASS SBOM written to $OUT_FILE (git-sha=$git_sha)"
