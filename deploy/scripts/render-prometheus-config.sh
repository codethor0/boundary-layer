#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TEMPLATE="${ROOT}/deploy/prometheus/prometheus.prod.yml.template"
OUTPUT="${ROOT}/deploy/prometheus/prometheus.prod.yml"

if [[ ! -f "${TEMPLATE}" ]]; then
  echo "Missing template: ${TEMPLATE}" >&2
  exit 1
fi

: "${BOUNDARY_LAYER_METRICS_TOKEN:?BOUNDARY_LAYER_METRICS_TOKEN is required}"

export BOUNDARY_LAYER_METRICS_TOKEN
envsubst '${BOUNDARY_LAYER_METRICS_TOKEN}' < "${TEMPLATE}" > "${OUTPUT}"
echo "Rendered ${OUTPUT}"
