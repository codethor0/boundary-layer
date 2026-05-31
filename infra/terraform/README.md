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

## Validation

If Terraform is installed locally:

```bash
terraform -chdir=infra/terraform fmt -check
terraform -chdir=infra/terraform validate
```

These commands are optional in CI and may be skipped when Terraform is not installed.
