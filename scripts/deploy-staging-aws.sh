#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

dry_run=true
if [[ "${DEPLOY_STAGING:-}" == "true" && "${CONFIRM_STAGING_DEPLOY:-}" == "true" ]]; then
  dry_run=false
fi

echo "BoundaryLayer AWS ECS/Fargate staging deploy"
if [[ "$dry_run" == "true" ]]; then
  echo "Mode: DRY RUN ONLY"
else
  echo "Mode: DEPLOY REQUESTED (requires configured AWS credentials)"
fi
echo ""

required_env=(
  AWS_REGION
  AWS_ACCOUNT_ID
  ECS_CLUSTER_NAME
  ECS_SERVICE_NAME
  STAGING_RELEASE_IMAGE
  BOUNDARY_LAYER_PUBLIC_BASE_URL
)

missing=()
for name in "${required_env[@]}"; do
  if [[ -z "${!name:-}" ]]; then
    missing+=("$name")
  fi
done

if ((${#missing[@]} > 0)); then
  if [[ "$dry_run" == "true" ]]; then
    echo "Using placeholder values for dry run (missing: ${missing[*]})"
    AWS_REGION="${AWS_REGION:-us-east-1}"
    AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID:-123456789012}"
    ECS_CLUSTER_NAME="${ECS_CLUSTER_NAME:-boundary-layer-staging}"
    ECS_SERVICE_NAME="${ECS_SERVICE_NAME:-boundary-layer-api}"
    STAGING_RELEASE_IMAGE="${STAGING_RELEASE_IMAGE:-123456789012.dkr.ecr.us-east-1.amazonaws.com/boundary-layer-api:staging}"
    BOUNDARY_LAYER_PUBLIC_BASE_URL="${BOUNDARY_LAYER_PUBLIC_BASE_URL:-https://staging.example.com}"
  else
    echo "Missing required environment variables:"
    for name in "${missing[@]}"; do
      echo "  - $name"
    done
    echo ""
    echo "Next steps:"
    echo "  1. Provision staging account resources (see docs/STAGING_DEPLOYMENT_RUNBOOK.md)"
    echo "  2. Configure GitHub Environment staging secrets (see docs/GITHUB_ENVIRONMENT_SETUP.md)"
    echo "  3. Set DEPLOY_STAGING=true and CONFIRM_STAGING_DEPLOY=true only after review"
    exit 1
  fi
fi

echo "Target region: ${AWS_REGION}"
echo "Target account: ${AWS_ACCOUNT_ID}"
echo "ECS cluster: ${ECS_CLUSTER_NAME}"
echo "ECS service: ${ECS_SERVICE_NAME}"
echo "Release image reference present: yes"
echo "Public base URL: ${BOUNDARY_LAYER_PUBLIC_BASE_URL}"
echo ""

if [[ "$dry_run" == "true" ]]; then
  echo "DRY RUN ONLY: no ECS update, no task definition registration, no destructive operations."
  echo "To deploy after review:"
  echo "  export DEPLOY_STAGING=true"
  echo "  export CONFIRM_STAGING_DEPLOY=true"
  echo "  bash scripts/deploy-staging-aws.sh"
  exit 0
fi

if ! command -v aws >/dev/null 2>&1; then
  echo "FAIL AWS CLI not installed" >&2
  exit 1
fi

echo "Validating AWS caller identity (account redacted in logs)..."
caller_account="$(aws sts get-caller-identity --query Account --output text 2>/dev/null || true)"
if [[ -z "$caller_account" ]]; then
  echo "FAIL unable to authenticate with AWS CLI" >&2
  exit 1
fi
if [[ "$caller_account" != "${AWS_ACCOUNT_ID}" ]]; then
  echo "FAIL AWS caller account does not match AWS_ACCOUNT_ID" >&2
  exit 1
fi
echo "PASS AWS authentication"

echo "Deploy placeholder: update ECS service ${ECS_SERVICE_NAME} with image ${STAGING_RELEASE_IMAGE}"
echo "This repository pass does not execute ECS service updates automatically."
echo "Operator must run reviewed deploy commands from docs/STAGING_DEPLOYMENT_RUNBOOK.md"
echo ""
echo "After deploy, run:"
echo "  RUN_LIVE_STAGING_CHECKS=true make live-staging-validation-package"
exit 0
