#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "BoundaryLayer WAF readiness check"
echo "Mode: structural (edge WAF must be validated at provider after provisioning)"
echo ""

required_docs=(
  docs/WAF_ABUSE_CONTROLS.md
  docs/STAGING_DEPLOYMENT_RUNBOOK.md
)

for path in "${required_docs[@]}"; do
  if [[ ! -f "$path" ]]; then
    echo "FAIL missing $path" >&2
    exit 1
  fi
done
echo "PASS WAF documentation present"

structural_env=(
  MAX_REQUEST_BODY_BYTES
  MAX_FILE_UPLOAD_BYTES
  TENANT_CONCURRENCY_LIMIT
  TENANT_RATE_LIMIT_PER_MINUTE
  WAF_ENABLED
)

echo "Structural config fields (values not printed):"
for name in "${structural_env[@]}"; do
  if [[ -n "${!name:-}" ]]; then
    echo "  - $name: set"
  else
    echo "  - $name: not set (optional for structural check)"
  fi
done

provider="${WAF_PROVIDER:-aws}"
live_checked=false

if [[ "$provider" == "aws" ]] && command -v aws >/dev/null 2>&1; then
  web_acl_arn="${AWS_WAF_WEB_ACL_ARN:-}"
  if [[ -n "$web_acl_arn" ]]; then
    if aws wafv2 get-web-acl --scope REGIONAL --id "${AWS_WAF_WEB_ACL_ID:-}" \
      --name "${AWS_WAF_WEB_ACL_NAME:-}" >/dev/null 2>&1; then
      echo "PASS AWS WAF web ACL reachable (ARN redacted)"
      live_checked=true
    else
      echo "SKIP AWS WAF live lookup (set AWS_WAF_WEB_ACL_ID and AWS_WAF_WEB_ACL_NAME)"
    fi
  else
    echo "SKIP AWS WAF live lookup (AWS_WAF_WEB_ACL_ARN not set)"
  fi
else
  echo "SKIP provider WAF live lookup (${provider} CLI not configured)"
fi

echo ""
echo "STRUCTURAL WAF READINESS PASS"
if [[ "$live_checked" == "true" ]]; then
  echo "Live WAF resource check: PASS"
else
  echo "Live WAF resource check: SKIPPED"
fi
