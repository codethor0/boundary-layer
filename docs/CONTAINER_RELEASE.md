# Container Release

BoundaryLayer container release guidance for hosted Production SaaS staging and future production. **No registry push or production deploy is performed by default.**

## Registry options

| Registry | Recommended for | Notes |
|----------|-----------------|-------|
| **Amazon ECR** | AWS ECS/Fargate (default) | OIDC push from GitHub Actions |
| GitHub Container Registry (GHCR) | GitHub-centric deploys | `ghcr.io/<org>/boundary-layer-api` |
| Google Artifact Registry | GCP Cloud Run | Regional repos |
| Azure Container Registry | Azure Container Apps | Service principal or OIDC |

**Recommended default:** Amazon ECR in the staging AWS account.

## Image naming convention

Repository name: `boundary-layer-api`

| Tag | Purpose |
|-----|---------|
| `boundary-layer-api:<git-sha>` | Immutable deploy reference |
| `boundary-layer-api:<version>` | Release semver (e.g. `1.3.5`) |
| `boundary-layer-api:staging` | Rolling staging pointer |

**Do not use `latest` for production or staging deploy gates.**

## Build and smoke

```bash
make container-build          # local build; tags with git SHA
make container-smoke-local    # /health in ephemeral container
make container-image-check    # Dockerfile hygiene + build smoke
```

Push only when explicitly enabled:

```bash
export PUSH_IMAGE=true
export CONTAINER_REGISTRY=<account>.dkr.ecr.<region>.amazonaws.com/boundary-layer-api
make container-build
```

## SBOM and container security evidence

```bash
make generate-sbom
make container-security-scan
```

Outputs (gitignored): `artifacts/security/sbom.spdx.json`, `artifacts/security/container-scan.txt`

If syft/trivy/grype are unavailable, scripts report **SKIPPED** with install instructions. Do not fake scan results.

If SBOM/container scan not validated in CI, score cannot exceed **9/10** per evidence matrix.

## Image signing plan

- Sign release and staging images with cosign or ECR signing
- Verify signatures in deploy workflow before ECS service update
- Not implemented in this pass

## Rollback tag plan

- Before deploy, record current task definition image digest as `previous`
- Keep last three immutable `<git-sha>` tags in ECR
- Roll back ECS service to `previous` digest; re-run live smoke

## Related documents

- [STAGING_DEPLOYMENT_RUNBOOK.md](STAGING_DEPLOYMENT_RUNBOOK.md)
- [STAGING_ENVIRONMENT_CONTRACT.md](STAGING_ENVIRONMENT_CONTRACT.md)
- [GITHUB_ENVIRONMENT_SETUP.md](GITHUB_ENVIRONMENT_SETUP.md)
- [DEPLOYMENT_ARCHITECTURE.md](DEPLOYMENT_ARCHITECTURE.md)
- [CI_CD_PRODUCTION_PLAN.md](CI_CD_PRODUCTION_PLAN.md)
