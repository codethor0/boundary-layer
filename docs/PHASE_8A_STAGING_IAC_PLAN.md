# Phase 8A — Minimal Staging IaC Implementation Plan

**Status:** Required before `terraform apply` can run. Current Terraform under `infra/terraform/` is a **skeleton only** (no providers, no resources).

Phase 8 stopped at operator prerequisites (AWS CLI missing, GitHub CLI token invalid). This document is the precise implementation plan to convert the skeleton into executable staging IaC.

## Target architecture (staging only)

| Component | AWS resource | Name prefix |
|-----------|--------------|-------------|
| Network | VPC, public/private subnets, NAT (optional) | `boundary-layer-staging` |
| API | ECS Fargate + ALB + HTTPS | `boundary-layer-staging-api` |
| Database | RDS PostgreSQL (TLS required) | `boundary-layer-staging-db` |
| Cache | ElastiCache Redis (TLS/auth) | `boundary-layer-staging-redis` |
| Object storage | S3 bucket | `boundary-layer-staging-artifacts` |
| Secrets | AWS Secrets Manager | `boundary-layer/staging/*` |
| Edge | AWS WAF on ALB | `boundary-layer-staging-waf` |
| Registry | ECR | `boundary-layer-api` |
| Logs | CloudWatch log groups | `/ecs/boundary-layer-staging` |

Tags on all resources:

```
Project=BoundaryLayer
Environment=staging
ManagedBy=terraform
```

## Implementation steps

### Step 1 — Root module wiring

File: `infra/terraform/main.tf`

- Add `terraform` block with S3 backend (remote state bucket + DynamoDB lock table — created manually or via bootstrap module)
- Add `provider "aws"` with `region = var.aws_region`
- Add `data "aws_caller_identity" "current"`
- Instantiate modules: `network`, `postgres`, `redis`, `object_storage`, `secret_manager`, `container_service`, `waf`, `observability`
- Pass `environment = "staging"`, `name_prefix = "boundary-layer-staging"`

### Step 2 — Network module

File: `infra/terraform/modules/network/main.tf`

- VPC `/16`, 2 AZs
- Public subnets (ALB), private subnets (ECS, RDS, ElastiCache)
- Security groups: ALB ingress 443, ECS from ALB only, RDS/Redis from ECS SG only
- Optional NAT gateway for ECS egress (document cost tradeoff)

Outputs: `vpc_id`, `private_subnet_ids`, `public_subnet_ids`, `ecs_security_group_id`, `alb_security_group_id`

### Step 3 — Postgres module

- RDS PostgreSQL 15+, `db.t4g.small` (staging), storage encrypted, `publicly_accessible = false`
- Parameter group: `ssl = on`
- Output `DATABASE_URL` to Secrets Manager (not plain output)
- Output non-secret: `endpoint`, `port`, `db_name`

### Step 4 — Redis module

- ElastiCache Redis 7+, `cache.t4g.micro`, transit encryption enabled, auth token in Secrets Manager
- Output `REDIS_URL` to Secrets Manager (rediss://)

### Step 5 — Object storage module

- S3 bucket with versioning, encryption (SSE-S3 or KMS), block public access
- Prefix policy for `tenants/` tenant isolation
- Output: `bucket_name`, `region`

### Step 6 — Secret manager module

- Secrets Manager secrets under `boundary-layer/staging/`
- Health-check secret placeholder for live validation
- IAM policy for ECS task role: `secretsmanager:GetSecretValue` scoped to prefix

### Step 7 — Container service module

- ECR repository `boundary-layer-api`
- ECS cluster + Fargate service
- ALB with ACM certificate (DNS validation — operator supplies domain or uses placeholder)
- Task definition referencing secrets from Secrets Manager and env from staging contract
- Health check path `/health`

Outputs: `alb_dns_name`, `ecr_repository_url`, `ecs_cluster_name`, `ecs_service_name`

### Step 8 — WAF module

- AWS WAFv2 Web ACL associated with ALB
- Rules: rate limit, body size limit, AWS managed common rule set (staging-tuned)
- Output: `web_acl_arn`

### Step 9 — Observability module

- CloudWatch log group for ECS
- Optional metric alarms (5xx rate, CPU)

### Step 10 — Staging env entrypoint

File: `infra/terraform/envs/staging/main.tf` (new)

- Backend config pointing to staging state bucket
- Module source `../../` with staging tfvars
- `terraform.tfvars.example` already exists — extend with `aws_region`, `domain_name`, `certificate_arn`

### Step 11 — Makefile / scripts

- Update `scripts/infra-plan-staging.sh` to use `infra/terraform/envs/staging` not root skeleton
- Add `CONFIRM_TERRAFORM_APPLY=true` gate for apply (never auto-apply in CI)

### Step 12 — Post-apply outputs → secrets

After apply, operator runs (values from terraform output / AWS console, never committed):

```bash
gh secret set DATABASE_URL --env staging
gh secret set REDIS_URL --env staging
gh secret set OBJECT_STORAGE_BUCKET --env staging
# ... see docs/PHASE_8_OPERATOR_RUNBOOK.md
```

## Validation gates

| Gate | Command |
|------|---------|
| Format | `terraform fmt -check -recursive infra/terraform` |
| Validate | `terraform -chdir=infra/terraform/envs/staging validate` |
| Plan | `CONFIRM_STAGING_PLAN=true TF_VAR_environment=staging make infra-plan-staging` |
| Apply | `CONFIRM_TERRAFORM_APPLY=true terraform apply` (operator only, after plan review) |

## Out of scope for 8A

- Production environment
- Multi-region DR
- Automated CI apply
- OIDC IdP provisioning (external — Auth0/Cognito/Clerk)

## Estimated effort

| Task | Estimate |
|------|----------|
| Network + SGs | 1 day |
| RDS + ElastiCache + S3 | 1 day |
| ECS + ALB + ECR | 1–2 days |
| WAF + IAM + secrets wiring | 1 day |
| Plan/apply testing in staging account | 1 day |

## Next prompt after 8A implementation

**BoundaryLayer Production SaaS Phase 8B — Apply Staging Terraform and Run Live Evidence Runner**
