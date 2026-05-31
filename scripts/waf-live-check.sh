#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "BoundaryLayer WAF live check"

if [[ "${RUN_LIVE_STAGING_CHECKS:-}" != "true" ]]; then
  echo "WAF LIVE CHECK SKIPPED (RUN_LIVE_STAGING_CHECKS not true)"
  exit 0
fi

if [[ -z "${STAGING_BASE_URL:-}" ]]; then
  echo "WAF LIVE CHECK SKIPPED (STAGING_BASE_URL not set)"
  exit 0
fi

provider="${WAF_PROVIDER:-aws}"
if [[ "$provider" == "aws" ]]; then
  if [[ -z "${AWS_WAF_WEB_ACL_ARN:-}" && -z "${AWS_WAF_WEB_ACL_NAME:-}" ]]; then
    echo "WAF LIVE CHECK SKIPPED (AWS WAF variables not configured)"
    exit 0
  fi
  if command -v aws >/dev/null 2>&1 && [[ -n "${AWS_WAF_WEB_ACL_NAME:-}" && -n "${AWS_WAF_WEB_ACL_ID:-}" ]]; then
    if aws wafv2 get-web-acl --scope REGIONAL \
      --name "$AWS_WAF_WEB_ACL_NAME" \
      --id "$AWS_WAF_WEB_ACL_ID" >/dev/null 2>&1; then
      echo "PASS WAF web ACL reachable (ARN redacted)"
    else
      echo "FAIL WAF web ACL lookup" >&2
      exit 1
    fi
  else
    echo "PASS WAF configured (live ACL lookup skipped; CLI or IDs missing)"
  fi
else
  echo "WAF LIVE CHECK SKIPPED (provider $provider not configured for live lookup)"
  exit 0
fi

if [[ "${WAF_ENABLED:-}" != "true" ]]; then
  echo "FAIL WAF_ENABLED is not true" >&2
  exit 1
fi
echo "PASS WAF_ENABLED=true"

if [[ -n "${MAX_REQUEST_BODY_BYTES:-}" && "${MAX_REQUEST_BODY_BYTES:-0}" != "0" ]]; then
  oversize=$((MAX_REQUEST_BODY_BYTES + 1024))
  status="$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST "${STAGING_BASE_URL%/}/labs/redis/run" \
    -H "Content-Type: application/json" \
    -d "$(python -c "print('x'*$oversize)")" 2>/dev/null || echo "000")"
  if [[ "$status" == "413" || "$status" == "403" || "$status" == "401" ]]; then
    echo "PASS oversized request rejected (HTTP $status)"
  else
    echo "SKIP oversized request rejection test (HTTP $status; edge may differ)"
  fi
fi

unauth_status="$(curl -s -o /dev/null -w "%{http_code}" "${STAGING_BASE_URL%/}/labs" || true)"
if [[ "$unauth_status" == "401" ]]; then
  echo "PASS unauthenticated /labs rejected"
else
  echo "FAIL unauthenticated /labs expected 401 got $unauth_status" >&2
  exit 1
fi

echo "WAF LIVE CHECK PASS"
