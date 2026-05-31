# Terraform Modules

Planned module boundaries for a future hosted Production SaaS deployment.

## Modules

| Name | Responsibility |
|------|----------------|
| `network` | VPC, private subnets, NAT, security groups |
| `database` | Managed PostgreSQL, backups, TLS |
| `cache` | Managed Redis, auth, TLS |
| `storage` | Object storage bucket, lifecycle, KMS optional |
| `secrets` | Secret manager integration |
| `compute` | API container service, autoscaling |
| `observability` | Logs, metrics, traces, alert routing |
| `edge` | WAF, CDN, TLS certificates |

No module code ships in this pass. Each module should be added with its own README, variables, outputs, and staging/prod environment wrappers before any apply.
