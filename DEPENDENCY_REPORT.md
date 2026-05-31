# Dependency Report

## Phase 5 additions

No new **required** runtime dependencies were added in Phase 5.

Live managed-service checks use existing dependencies (`psycopg`, `redis`, `httpx`) when `RUN_LIVE_STAGING_CHECKS=true`. Cloud SDKs remain optional (lazy import) as documented in Phase 4.

## Phase 4 additions

No new **required** runtime dependencies were added in Phase 4.

Cloud adapter SDKs are **optional** and loaded lazily:

| Adapter | Optional package |
|---------|------------------|
| S3 / R2 | `boto3` |
| GCS | `google-cloud-storage` |
| AWS Secrets Manager | `boto3` |
| GCP Secret Manager | `google-cloud-secret-manager` |
| Azure Key Vault | `azure-identity`, `azure-keyvault-secrets` |
| Vault | `hvac` |

Object storage and secret manager adapters fail clearly when optional SDKs are not installed. Local lab and CI do not require cloud SDKs.

## Known advisories (unchanged)

Run `pip-audit -r apps/api/requirements.txt` before release. Prior advisories on pinned `pyjwt` and `cryptography` versions should be tracked and upgraded in a dedicated dependency pass.
