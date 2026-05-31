# Terraform Skeleton

**Warning:** This Terraform skeleton is not applied and is not production-ready.

Do not run `terraform apply` from this repository without a reviewed staging plan, remote state backend, and cloud credentials managed outside Git.

## Layout

```
infra/terraform/
  main.tf           # Root module placeholder
  variables.tf      # Input variables (no secrets)
  outputs.tf        # Output placeholders
  envs/staging/     # Staging environment notes
  modules/          # Intended module boundaries
```

## Intended modules (not implemented)

| Module | Purpose |
|--------|---------|
| network | VPC, subnets, security groups |
| database | Managed PostgreSQL, private access, backups |
| cache | Managed Redis with TLS |
| storage | Object storage bucket and IAM |
| secrets | Secret manager references |
| compute | Container service / load balancer |
| observability | Log/metric sinks, alert routing |
| edge | WAF, TLS termination |

## Backend recommendation

Use a remote backend with state locking (S3 + DynamoDB, GCS + state lock, Terraform Cloud, etc.). Do not commit state files or credentials.

## Required cloud permissions (staging operator)

- Read/write Terraform state backend
- VPC/network create in staging account only
- Managed Postgres/Redis provisioning
- Object storage bucket IAM
- Secret manager read for deploy roles
- Container service deploy + load balancer
- WAF/edge policy attach (when implemented)

Use least-privilege IAM scoped to staging account/project.

## Plan/apply workflow

1. `make infra-validate`
2. Export cloud credentials via OIDC or short-lived session (never commit)
3. `CONFIRM_STAGING_PLAN=true make infra-plan-staging`
4. Human review of plan output
5. Apply only from approved operator workstation or CI job with environment protection

**Destroy protection:** enable deletion protection on stateful resources; require manual approval for destroy plans.

**Cost warning:** staging accounts still incur cost; set billing alerts.

**Secrets warning:** never store secrets in `.tfvars` committed to Git; use secret manager references.

## Avoid accidental production deploy

- Separate AWS/GCP/Azure accounts or projects for staging vs production
- Distinct Terraform workspaces or state keys (`env/staging` vs `env/production`)
- Require `CONFIRM_STAGING_PLAN=true` and staging workspace name checks before plan
- Do not reuse production domain names or buckets in staging tfvars examples

## Validation

```bash
make infra-validate
CONFIRM_STAGING_PLAN=true make infra-plan-staging
```

These commands are optional when Terraform is not installed; scripts report skipped steps clearly.
