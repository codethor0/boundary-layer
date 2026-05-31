#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "BoundaryLayer DR restore live check"

if [[ "${CONFIRM_STAGING_DR_TEST:-}" != "true" ]]; then
  echo "DR LIVE CHECK SKIPPED (set CONFIRM_STAGING_DR_TEST=true to run)"
  exit 0
fi

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "DR LIVE CHECK SKIPPED (DATABASE_URL not set)"
  exit 0
fi

provider="${DR_BACKUP_PROVIDER:-aws-rds}"
if [[ "$provider" == "aws-rds" ]]; then
  if ! command -v aws >/dev/null 2>&1; then
    echo "DR LIVE CHECK SKIPPED (aws CLI not installed)"
    exit 0
  fi
  instance_id="${RDS_INSTANCE_ID:-}"
  if [[ -z "$instance_id" ]]; then
    echo "DR LIVE CHECK SKIPPED (RDS_INSTANCE_ID not set)"
    exit 0
  fi
  latest="$(aws rds describe-db-snapshots \
    --db-instance-identifier "$instance_id" \
    --snapshot-type automated \
    --query 'DBSnapshots | sort_by(@, &SnapshotCreateTime) | [-1].SnapshotCreateTime' \
    --output text 2>/dev/null || true)"
  if [[ -z "$latest" || "$latest" == "None" ]]; then
    echo "FAIL no automated RDS snapshot found for $instance_id" >&2
    exit 1
  fi
  echo "PASS latest automated snapshot exists (timestamp redacted in logs)"
  echo "DR LIVE CHECK PASS (non-destructive backup verification only)"
  exit 0
fi

echo "DR LIVE CHECK SKIPPED (provider $provider not implemented)"
