#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TEMPLATE="${ROOT}/deploy/alertmanager/alertmanager.prod.yml.template"
OUTPUT="${ROOT}/deploy/alertmanager/alertmanager.prod.yml"

: "${BOUNDARY_LAYER_ALERT_WEBHOOK_TOKEN:?BOUNDARY_LAYER_ALERT_WEBHOOK_TOKEN is required}"
: "${SLACK_WEBHOOK_URL:=https://hooks.slack.com/services/REPLACE/ME}"
: "${SLACK_ALERT_CHANNEL:=#boundary-layer-alerts}"
: "${PAGERDUTY_ROUTING_KEY:=replace-with-pagerduty-routing-key}"

export BOUNDARY_LAYER_ALERT_WEBHOOK_TOKEN
envsubst '${BOUNDARY_LAYER_ALERT_WEBHOOK_TOKEN}' \
  < "${TEMPLATE}" > "${OUTPUT}"
echo "Rendered ${OUTPUT}"
