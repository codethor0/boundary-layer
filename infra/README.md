# BoundaryLayer Infrastructure

This directory contains **Infrastructure-as-Code skeletons only**.

BoundaryLayer has **not** applied this infrastructure to any cloud account. There are no provider credentials, account IDs, or live domains in this repository.

## Intended staging topology

- Container service for the FastAPI API
- Managed PostgreSQL with TLS and private networking
- Managed Redis with TLS and auth
- Object storage bucket with tenant prefixes
- Cloud secret manager for runtime secrets
- VPC/private subnets and egress controls
- Edge WAF and rate limiting
- Centralized logging, metrics, and alert routing
- CI/CD deploy role with staging smoke gates

## Status

| Component | Status |
|-----------|--------|
| Terraform skeleton | Documented, not applied |
| Managed Postgres | Not provisioned |
| Managed Redis | Not provisioned |
| Object storage | Config scaffold only |
| Secret manager | Config scaffold only |
| WAF / edge | Not provisioned |
| Live staging deploy | Not performed |

See `terraform/README.md` for module layout and safety warnings.
