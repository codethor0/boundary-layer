# Staging Secrets Inventory

Complete inventory of secrets and configuration values required for **live staging** validation and deploy.

**Never commit real values.** Store secrets in GitHub Environment `staging` or untracked local `.env.staging`.

## GitHub Environment: staging

| Name | Purpose | Secret | Example placeholder | Rotation | Validation |
|------|---------|--------|---------------------|----------|------------|
| `STAGING_BASE_URL` | Public API base URL | No | `https://staging.example.com` | On URL change | `make staging-smoke-live` |
| `STAGING_TEST_ACCESS_TOKEN_TENANT_A` | Tenant A JWT smoke | **Yes** | `<oidc-issued-jwt>` | Per IdP policy | Live smoke `/labs` |
| `STAGING_TEST_ACCESS_TOKEN_TENANT_B` | Cross-tenant denial test | **Yes** | `<oidc-issued-jwt>` | Per IdP policy | Live smoke 403 test |
| `STAGING_METRICS_AUTH_TOKEN` | Metrics bearer | **Yes** | `staging-metrics-token-min-24` | 90 days | Live smoke `/metrics` |
| `DEPLOY_STAGING` | Enable deploy workflow step | No | `false` | N/A | Workflow gate |
| `CONTAINER_REGISTRY` | ECR/GHCR prefix | No | `<acct>.dkr.ecr.us-east-1.amazonaws.com/boundary-layer-api` | N/A | `make container-build` push |

## OIDC provider

| Name | Purpose | Secret | Example | Rotation | Validation |
|------|---------|--------|---------|----------|------------|
| `OIDC_ISSUER_URL` | Issuer | No | `https://staging-issuer.example.com` | IdP managed | Managed-services JWKS check |
| `OIDC_AUDIENCE` | API audience | No | `boundary-layer-api-staging` | On app registration | Auth smoke |
| `OIDC_JWKS_URL` | JWKS document | No | `https://.../.well-known/jwks.json` | IdP managed | Live JWKS fetch |
| `OIDC_TENANT_CLAIM` | Tenant claim | No | `https://boundarylayer.dev/tenant_id` | Rare | Config check |
| `OIDC_ROLES_CLAIM` | Roles claim | No | `https://boundarylayer.dev/roles` | Rare | Config check |
| OIDC client secret | IdP app secret | **Yes** | `<not stored in repo>` | 90 days | IdP console only |

## Database

| Name | Purpose | Secret | Example | Rotation | Validation |
|------|---------|--------|---------|----------|------------|
| `DATABASE_URL` | Managed Postgres | **Yes** | `postgresql://user:***@rds.../db?sslmode=require` | 90 days | Live `SELECT 1` |
| `DB_SSL_MODE` | SSL enforcement | No | `require` | N/A | Policy check |
| `POSTGRES_PASSWORD` | Legacy compose compat | **Yes** | `<managed password>` | 90 days | Startup gate |

## Redis

| Name | Purpose | Secret | Example | Rotation | Validation |
|------|---------|--------|---------|----------|------------|
| `REDIS_URL` | Managed Redis TLS | **Yes** | `rediss://:***@elasticache...:6379/0` | 90 days | Live PING/set/get |
| `REDIS_KEY_PREFIX` | Tenant namespace | No | `boundary_layer:tenant` | N/A | Policy check |
| `REDIS_PASSWORD` | Auth token | **Yes** | `<redis auth>` | 90 days | Connection test |

## Object storage

| Name | Purpose | Secret | Example | Rotation | Validation |
|------|---------|--------|---------|----------|------------|
| `OBJECT_STORAGE_BUCKET` | S3 bucket | No | `boundary-layer-staging-artifacts` | N/A | Live write/read/delete |
| `OBJECT_STORAGE_REGION` | Region | No | `us-east-1` | N/A | Policy check |
| `OBJECT_STORAGE_PREFIX` | Tenant prefix | No | `tenants/` | N/A | Key path check |
| AWS access keys / IAM role | SDK auth | **Yes** | `<OIDC role in CI>` | Session | Live object check |

## Secret manager

| Name | Purpose | Secret | Example | Rotation | Validation |
|------|---------|--------|---------|----------|------------|
| `SECRET_MANAGER_PROVIDER` | Backend | No | `aws` | N/A | Policy check |
| `SECRET_MANAGER_PROJECT_OR_PATH` | Path prefix | No | `boundary-layer/staging` | N/A | Policy check |
| `BOUNDARY_LAYER_HEALTHCHECK_SECRET_NAME` | Health-check secret name | No | `boundary-layer/healthcheck` | N/A | Live presence check |
| `SECRET_ROTATION_REQUIRED` | Policy flag | No | `true` | N/A | Policy check |
| `SECRET_CACHE_TTL_SECONDS` | Cache TTL | No | `300` | N/A | Policy check |

## Application secrets

| Name | Purpose | Secret | Example | Rotation | Validation |
|------|---------|--------|---------|----------|------------|
| `BOUNDARY_LAYER_SECRET_KEY` | App signing | **Yes** | `CHANGE_ME-32-chars-minimum` | 90 days | Startup gate |
| `BOUNDARY_LAYER_API_KEY` | Legacy API key gate | **Yes** | `<32+ chars>` | 90 days | Startup gate |
| `BOUNDARY_LAYER_METRICS_TOKEN` | Metrics auth | **Yes** | `<24+ chars>` | 90 days | Metrics smoke |
| `SESSION_HMAC_SECRET` | Session HMAC | **Yes** | `<32+ chars>` | 90 days | Startup gate |

## Audit

| Name | Purpose | Secret | Example | Rotation | Validation |
|------|---------|--------|---------|----------|------------|
| `BOUNDARY_LAYER_AUDIT_LOG_ENABLED` | Enable audit | No | `true` | N/A | Startup gate |
| `AUDIT_SINK_PROVIDER` | Sink target | No | `postgres` | N/A | Policy check |
| `AUDIT_IMMUTABLE_REQUIRED` | Immutable policy | No | `false` (staging) | N/A | Policy check |

## WAF / edge

| Name | Purpose | Secret | Example | Rotation | Validation |
|------|---------|--------|---------|----------|------------|
| `WAF_ENABLED` | Edge WAF expected | No | `true` | N/A | `make waf-readiness-check` |
| `AWS_WAF_WEB_ACL_ARN` | WAF ACL | No | `arn:aws:wafv2:...` | N/A | Optional live check |
| `MAX_REQUEST_BODY_BYTES` | Body limit | No | `1048576` | N/A | App middleware |

## Container registry

| Name | Purpose | Secret | Example | Rotation | Validation |
|------|---------|--------|---------|----------|------------|
| `STAGING_RELEASE_IMAGE` | Deploy image ref | No | `<ecr>/boundary-layer-api:<sha>` | Per deploy | Deploy dry-run |
| `PUSH_IMAGE` | Push gate | No | `false` | N/A | `container-build.sh` |
| ECR/GHCR credentials | Registry auth | **Yes** | `<CI OIDC>` | Session | Push step |

## Live validation gate

| Name | Purpose | Secret | Example | Rotation | Validation |
|------|---------|--------|---------|----------|------------|
| `RUN_LIVE_STAGING_CHECKS` | Enable live checks | No | `true` | N/A | All live scripts |

## Used by script/workflow

| Secret/config | Script / workflow |
|---------------|-------------------|
| All managed-service vars | `production-saas-managed-services-live-check.sh`, `staging-live-validation.yml` |
| STAGING_* tokens | `staging-smoke-live.sh`, `live-staging-validation-package.sh` |
| DEPLOY_STAGING | `.github/workflows/staging-deploy.yml` |
| AWS_* ECS_* | `deploy-staging-aws.sh` |
| CONTAINER_REGISTRY | `container-build.sh`, staging-deploy workflow |

See [GITHUB_ENVIRONMENT_SETUP.md](GITHUB_ENVIRONMENT_SETUP.md) for setup steps.
