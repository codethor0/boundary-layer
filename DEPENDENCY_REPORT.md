# Dependency Report

## Fast Track advisory remediation (Phase Fast Track)

Upgraded pinned dependencies with available fixes:

| Package | Before | After | Advisory IDs addressed |
|---------|--------|-------|------------------------|
| PyJWT | 2.10.1 | 2.12.0 | PYSEC-2026-120, PYSEC-2025-183 |
| cryptography | 44.0.1 | 46.0.7 | PYSEC-2026-35, GHSA-r6ph-v2qm-q3c2, PYSEC-2026-36 |

Verify with:

```bash
pip-audit -r apps/api/requirements.txt
```

Compensating controls if future advisories appear without fixes: pin review in CI Security Scan, Trivy container scan, minimal dependency surface.

## Phase 6 additions

No new **required** runtime dependencies. Phase 6 adds operator scripts and documentation only; cloud CLIs remain optional.

## Optional cloud SDKs (lazy import)

| Adapter | Optional package |
|---------|------------------|
| S3 / R2 | `boto3` |
| GCS | `google-cloud-storage` |
| AWS Secrets Manager | `boto3` |
| GCP Secret Manager | `google-cloud-secret-manager` |
| Azure Key Vault | `azure-identity`, `azure-keyvault-secrets` |
| Vault | `hvac` |

Object storage and secret manager adapters fail clearly when optional SDKs are not installed. Local lab and CI do not require cloud SDKs.
