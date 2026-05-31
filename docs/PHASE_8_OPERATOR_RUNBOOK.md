# Phase 8 Operator Runbook — Staging Provisioning and Live Evidence

Use this runbook when automated Phase 8 cannot run due to missing credentials or skeleton IaC.

**Phase 8 result (2026-05-31):** Stopped — AWS CLI not installed, GitHub CLI token invalid, Terraform skeleton not executable. No live staging was provisioned or validated.

## Prerequisites checklist

| Prerequisite | Status in Phase 8 |
|--------------|-------------------|
| AWS CLI installed (`aws`) | Missing |
| AWS credentials configured (`aws sts get-caller-identity`) | Not tested (CLI missing) |
| GitHub CLI authenticated (`gh auth status`) | Invalid token |
| Terraform >= 1.5 | Installed |
| Docker | Installed |
| Dedicated staging AWS account | Operator must create |
| OIDC IdP (Auth0/Cognito/Clerk) | Operator must configure |
| Terraform IaC executable | **No** — see `docs/PHASE_8A_STAGING_IAC_PLAN.md` |

## Step 1 — Fix local tooling

```bash
# Install AWS CLI (macOS)
brew install awscli

# Configure credentials (use staging account IAM user or SSO)
aws configure
aws sts get-caller-identity

# Re-authenticate GitHub CLI
gh auth login -h github.com
gh auth status
```

## Step 2 — Implement staging IaC (Phase 8A)

Terraform is currently a skeleton. Complete `docs/PHASE_8A_STAGING_IAC_PLAN.md` before apply.

When executable:

```bash
cd /Users/thor/Projects/boundary-layer
export TF_VAR_environment=staging
terraform -chdir=infra/terraform/envs/staging init
terraform -chdir=infra/terraform/envs/staging fmt -check
terraform -chdir=infra/terraform/envs/staging validate
CONFIRM_STAGING_PLAN=true make infra-plan-staging
# Review plan output — do not apply without review
CONFIRM_TERRAFORM_APPLY=true terraform -chdir=infra/terraform/envs/staging apply
```

Capture non-secret outputs only: ALB DNS, ECR URL, S3 bucket name, region.

## Step 3 — Create GitHub Environment `staging`

```bash
OWNER=$(gh repo view --json owner -q .owner.login)
REPO=$(gh repo view --json name -q .name)
gh api "repos/${OWNER}/${REPO}/environments/staging" --method PUT
gh secret list --env staging
gh variable list --env staging
```

Enable required reviewers in GitHub UI: Settings -> Environments -> staging.

## Step 4 — Set GitHub Environment secrets

Do not invent values. Replace placeholders with values from AWS console, RDS, ElastiCache, IdP.

```bash
# Managed services (secrets)
gh secret set DATABASE_URL --env staging
gh secret set REDIS_URL --env staging
gh secret set POSTGRES_PASSWORD --env staging
gh secret set REDIS_PASSWORD --env staging

# Application secrets
gh secret set BOUNDARY_LAYER_SECRET_KEY --env staging
gh secret set BOUNDARY_LAYER_API_KEY --env staging
gh secret set BOUNDARY_LAYER_METRICS_TOKEN --env staging
gh secret set STAGING_METRICS_AUTH_TOKEN --env staging
gh secret set SESSION_HMAC_SECRET --env staging

# OIDC smoke tokens (from IdP)
gh secret set STAGING_TEST_ACCESS_TOKEN_TENANT_A --env staging
gh secret set STAGING_TEST_ACCESS_TOKEN_TENANT_B --env staging

# OIDC config (issuer/JWKS are often variables, not secrets)
gh variable set OIDC_ISSUER_URL --env staging
gh variable set OIDC_AUDIENCE --env staging
gh variable set OIDC_JWKS_URL --env staging
gh variable set OIDC_TENANT_CLAIM --env staging
gh variable set OIDC_ROLES_CLAIM --env staging

# Staging URLs
gh variable set STAGING_BASE_URL --env staging
gh variable set BOUNDARY_LAYER_PUBLIC_BASE_URL --env staging
gh variable set BOUNDARY_LAYER_ALLOWED_ORIGINS --env staging

# Object storage
gh variable set OBJECT_STORAGE_BUCKET --env staging
gh variable set OBJECT_STORAGE_REGION --env staging
gh variable set OBJECT_STORAGE_PREFIX --env staging

# Secret manager
gh variable set SECRET_MANAGER_PROVIDER --env staging
gh variable set SECRET_MANAGER_PROJECT_OR_PATH --env staging
gh variable set BOUNDARY_LAYER_HEALTHCHECK_SECRET_NAME --env staging

# Audit
gh variable set AUDIT_SINK_PROVIDER --env staging
gh variable set BOUNDARY_LAYER_AUDIT_LOG_ENABLED --env staging

# Deploy gates
gh variable set DEPLOY_STAGING --env staging   # keep false until ready
gh variable set BOUNDARY_LAYER_PROFILE --env staging
gh variable set BOUNDARY_LAYER_ENV --env staging
gh variable set RUN_LIVE_STAGING_CHECKS --env staging

# Container registry (after ECR created)
gh variable set CONTAINER_REGISTRY --env staging
gh secret set STAGING_RELEASE_IMAGE --env staging
```

Full inventory: `docs/STAGING_SECRETS_INVENTORY.md`.

## Step 5 — Local `.env.staging` (alternative to GitHub secrets)

```bash
cp .env.staging.example .env.staging
# Edit .env.staging with real values — never commit
chmod 600 .env.staging
```

## Step 6 — Build and push container

```bash
export AWS_REGION=us-east-1
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export CONTAINER_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/boundary-layer-api"
export PUSH_IMAGE=true
make container-build
# Tag with git SHA, not latest-only
docker tag boundary-layer-api:$(git rev-parse --short HEAD) \
  "${CONTAINER_REGISTRY}:$(git rev-parse --short HEAD)"
aws ecr get-login-password --region "$AWS_REGION" | \
  docker login --username AWS --password-stdin "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
docker push "${CONTAINER_REGISTRY}:$(git rev-parse --short HEAD)"
```

## Step 7 — Deploy staging API

Dry run first:

```bash
make deploy-staging-dry-run
```

Real deploy (after ECS cluster/service exist):

```bash
export DEPLOY_STAGING=true
export CONFIRM_STAGING_DEPLOY=true
export ECS_CLUSTER_NAME=boundary-layer-staging
export ECS_SERVICE_NAME=boundary-layer-api
export STAGING_RELEASE_IMAGE="${CONTAINER_REGISTRY}:$(git rev-parse --short HEAD)"
export BOUNDARY_LAYER_PUBLIC_BASE_URL=https://staging.example.com
bash scripts/deploy-staging-aws.sh
```

## Step 8 — Run live evidence

```bash
set -a
source .env.staging
set +a
export RUN_LIVE_STAGING_CHECKS=true

make check-live-staging-prereqs
make production-saas-managed-services-live-check
make staging-smoke-live
make production-saas-evidence-runner
make waf-live-check          # if WAF configured
make audit-sink-live-check     # if audit sink configured
CONFIRM_STAGING_DR_TEST=true make dr-restore-live-check  # only if DR approved
```

Fill `artifacts/live-evidence/LIVE_STAGING_EVIDENCE.md` from sanitized output.

## Step 9 — CI live validation

Actions -> **Production SaaS Live Validation** -> Run workflow (requires Environment `staging`).

## Blockers that prevented Phase 8 automation

1. **AWS access missing** — `aws` CLI not installed
2. **GitHub CLI access missing** — invalid keyring token
3. **Terraform skeleton** — no executable plan/apply path
4. **No `.env.staging`** — operator must create from `.env.staging.example`
5. **GitHub Environment `staging`** — not created (404 in Phase 7)

## Score impact

Until Steps 1–8 complete with passing live evidence, Production SaaS score remains **6/10**.
