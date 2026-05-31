# Container Release

BoundaryLayer container release guidance for future hosted Production SaaS. **No registry push or production deploy is performed in the local lab repository pass.**

## Image strategy

- Build from `apps/api/Dockerfile` (multi-stage, non-root).
- Tag format: `boundary-layer:<semver>-<git-sha>` for releases; `boundary-layer:staging-<date>` for staging.
- Never bake `.env`, `.env.staging`, or secrets into images.

## Local readiness check

```bash
make container-image-check
```

Verifies Dockerfile presence, rejects `.env` copy patterns, optionally builds locally, and checks `/health` in an ephemeral container.

## SBOM plan (not implemented)

- Generate SBOM with Syft during CI release job.
- Store SBOM artifact alongside image digest.
- Gate releases on critical CVE policy (Trivy already runs in CI).

## Signature plan (not implemented)

- Sign release images with cosign or registry-native signing.
- Verify signatures in staging/prod deploy pipelines before rollout.

## Registry strategy (placeholder)

- Staging: private container registry in cloud account (ECR/GCR/ACR/GHCR).
- Production: separate registry path or repository with stricter retention/immutability.
- Do not commit registry credentials; use CI OIDC or short-lived tokens.

## Rollback strategy

- Keep previous image digest tagged as `previous` or stored in deploy metadata.
- Roll back container service to prior digest; run forward-fix migration plan if schema changed.
- Re-run staging smoke after rollback.

## Related documents

- [STAGING_ENVIRONMENT_CONTRACT.md](STAGING_ENVIRONMENT_CONTRACT.md)
- [DEPLOYMENT_ARCHITECTURE.md](DEPLOYMENT_ARCHITECTURE.md)
- [CI_CD_PRODUCTION_PLAN.md](CI_CD_PRODUCTION_PLAN.md)
