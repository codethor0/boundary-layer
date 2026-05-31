# Staging Deployment Runbook

This runbook describes how to provision and deploy BoundaryLayer to a **staging** environment for Production SaaS validation.

**Default recommended target:** AWS ECS/Fargate with RDS PostgreSQL, ElastiCache Redis, S3, Secrets Manager, and AWS WAF.

Alternative paths (Render/Fly.io, GCP Cloud Run, Azure Container Apps) are noted where they differ. This repository does **not** auto-provision cloud resources.

## Validation states

| State | Meaning |
|-------|---------|
| Local lab | Default Docker Compose; no cloud |
| Structural staging | Config/policy checks only; no network |
| Live staging | Real managed-service and HTTP validation |
| Deployed staging evidence | Documented proof after live checks pass |

## Prerequisites

### Cloud account

- Dedicated **staging AWS account** (never share with production)
- IAM admin or scoped deploy role for operator
- Billing alerts enabled (estimated **$150–400/month** for minimal staging: Fargate + RDS db.t4g.small + ElastiCache t4g.micro + S3 + NAT optional)
- Remote Terraform state bucket with locking (S3 + DynamoDB)

### Managed services to create

| Service | AWS resource | Purpose |
|---------|--------------|---------|
| API | ECS Fargate + ALB | HTTPS API |
| Database | RDS PostgreSQL | Tenant data, audit events |
| Cache | ElastiCache Redis (TLS) | Rate limits, tenant namespaces |
| Object storage | S3 bucket | Tenant artifacts (`tenants/` prefix) |
| Secrets | Secrets Manager | Runtime secrets, health-check secret |
| Edge | AWS WAF on ALB | Rate limits, request size, bot rules |
| Registry | ECR | Container images |
| DNS | Route 53 or external | `staging.example.com` (placeholder) |

### OIDC provider

- Auth0, Clerk, Cognito, or similar
- Register staging API audience (e.g. `boundary-layer-api-staging`)
- Configure tenant and roles custom claims per `docs/STAGING_ENVIRONMENT_CONTRACT.md`
- Issue test JWTs for tenant A and tenant B smoke tests

### GitHub

- GitHub Environment named `staging` with protection rules
- Secrets listed in `docs/STAGING_SECRETS_INVENTORY.md`
- Manual approval for deploy workflow recommended

## Deployment sequence

### 1. Provision infrastructure (plan only in repo)

```bash
make infra-validate
CONFIRM_STAGING_PLAN=true make infra-plan-staging
```

Review Terraform plan with operator. **Do not run `terraform apply` from CI without human review.**

Apply from operator workstation after plan approval (outside default repo validation).

### 2. Configure GitHub Environment

Follow `docs/GITHUB_ENVIRONMENT_SETUP.md`. Populate all staging secrets.

### 3. Build container image

```bash
make container-build
# Optional push after ECR login:
# export PUSH_IMAGE=true CONTAINER_REGISTRY=<account>.dkr.ecr.<region>.amazonaws.com/boundary-layer-api
# make container-build
```

### 4. Deploy (manual workflow)

GitHub Actions: **Staging Deploy** workflow (`workflow_dispatch`).

- Default: `DEPLOY_STAGING=false` — **DRY RUN ONLY**
- Live deploy: set repository variable/secret `DEPLOY_STAGING=true` and confirm operator review

Or locally:

```bash
export AWS_REGION=us-east-1
export AWS_ACCOUNT_ID=123456789012
export ECS_CLUSTER_NAME=boundary-layer-staging
export ECS_SERVICE_NAME=boundary-layer-api
export STAGING_RELEASE_IMAGE=<account>.dkr.ecr.<region>.amazonaws.com/boundary-layer-api:<git-sha>
export BOUNDARY_LAYER_PUBLIC_BASE_URL=https://staging.example.com
bash scripts/deploy-staging-aws.sh
```

Live deploy requires `DEPLOY_STAGING=true` and `CONFIRM_STAGING_DEPLOY=true`.

### 5. Live validation

```bash
export RUN_LIVE_STAGING_CHECKS=true
# source untracked .env.staging
make live-staging-validation-package
make staging-release-gate
```

Fill `docs/LIVE_STAGING_EVIDENCE_TEMPLATE.md` after success.

## What is created

- Staging ECS service behind HTTPS load balancer
- Managed Postgres, Redis, S3, Secrets Manager references
- ECR image tags: `<git-sha>`, `staging`, `<version>`
- WAF web ACL association (operator-configured)

## What is not created

- Production environment or production DNS
- Billing/subscription system
- Immutable audit/SIEM sink (Phase 5 shells only)
- Legal/compliance documents
- Customer onboarding UI

## DNS assumptions

- Public HTTPS URL (e.g. `https://staging.example.com`)
- TLS certificate on ALB (ACM)
- `BOUNDARY_LAYER_PUBLIC_BASE_URL` and `BOUNDARY_LAYER_ALLOWED_ORIGINS` match staging URL

## Rollback plan

1. Record previous ECS task definition revision and image digest
2. Update ECS service to previous task definition
3. Run `make staging-smoke-live` (with live env)
4. If schema migration involved, follow forward-fix plan in `docs/DR_ONCALL_RUNBOOK.md`

## Destroy plan

1. Scale ECS service to zero
2. Snapshot RDS if data retention needed; otherwise skip
3. Delete ElastiCache cluster, ECS service, ALB, WAF (if dedicated)
4. Empty and delete S3 bucket after object review
5. Remove Secrets Manager secrets per retention policy
6. Destroy Terraform staging workspace **only** with explicit operator approval

**Warning:** Destroy operations are irreversible. Never run destroy from CI.

## Safety warnings

- Never commit `.env.staging`, credentials, or OIDC client secrets
- Never use production account IDs, buckets, or databases in staging tfvars
- Never echo secrets in CI logs
- Do not claim live staging pass without `LIVE STAGING VALIDATION PASS` output
- Score remains **6/10** until live validation passes with evidence

## Related documents

- [STAGING_ENVIRONMENT_CONTRACT.md](STAGING_ENVIRONMENT_CONTRACT.md)
- [STAGING_SECRETS_INVENTORY.md](STAGING_SECRETS_INVENTORY.md)
- [GITHUB_ENVIRONMENT_SETUP.md](GITHUB_ENVIRONMENT_SETUP.md)
- [LIVE_STAGING_EVIDENCE_TEMPLATE.md](LIVE_STAGING_EVIDENCE_TEMPLATE.md)
- [CONTAINER_RELEASE.md](CONTAINER_RELEASE.md)
