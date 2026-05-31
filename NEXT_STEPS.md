# Next Steps

BoundaryLayer v1.3.5 remains a **complete local defensive security lab**. Production SaaS score is **capped at 6/10** until live staging evidence passes via `make production-saas-evidence-runner`.

## Immediate priorities (execute with real credentials)

1. Populate GitHub Environment `staging` secrets per `docs/STAGING_SECRETS_INVENTORY.md`
2. Provision AWS staging account per `docs/STAGING_DEPLOYMENT_RUNBOOK.md`
3. Run `RUN_LIVE_STAGING_CHECKS=true make check-live-staging-prereqs`
4. Run `RUN_LIVE_STAGING_CHECKS=true make production-saas-evidence-runner`
5. Fill `docs/LIVE_STAGING_EVIDENCE_TEMPLATE.md` and `artifacts/live-evidence/LIVE_STAGING_EVIDENCE.md`
6. Complete legal/compliance checklist in `docs/LEGAL_COMPLIANCE_READINESS.md`

## Validation commands (Fast Track)

```bash
make check-live-staging-prereqs          # expect MISSING without .env.staging
make production-saas-evidence-runner     # expect CANNOT RUN without live env
make waf-live-check                      # expect SKIPPED
make audit-sink-live-check               # expect SKIPPED or PASS with live DB
make dr-restore-live-check               # expect SKIPPED
make generate-sbom                       # SKIP or PASS if syft installed
make container-security-scan             # SKIP or PASS if trivy/grype installed
```

Manual CI: `.github/workflows/production-saas-live-validation.yml`

## Scoring

See `docs/PRODUCTION_10_10_EVIDENCE_MATRIX.md`. Do not inflate score without evidence.

## Recommended next prompt

**BoundaryLayer Production SaaS Phase 7 — Staging Account Apply and Live Evidence Capture**

## References

- [docs/PRODUCTION_10_10_EVIDENCE_MATRIX.md](docs/PRODUCTION_10_10_EVIDENCE_MATRIX.md)
- [docs/PRODUCTION_READINESS_REVIEW.md](docs/PRODUCTION_READINESS_REVIEW.md)
- [docs/STAGING_DEPLOYMENT_RUNBOOK.md](docs/STAGING_DEPLOYMENT_RUNBOOK.md)
