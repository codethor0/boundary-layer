# Dependency Report

## Phase 3 additions

No new runtime dependencies were added in Phase 3.

JWKS validation uses existing `PyJWT` and `cryptography` packages already pinned in `apps/api/requirements.txt`.

Object storage and secret manager scaffolds are interface-only and do not add cloud SDKs (`boto3`, `google-cloud-storage`, etc.) in this pass.

## Known advisories (unchanged)

Run `pip-audit -r apps/api/requirements.txt` before release. Prior advisories on pinned `pyjwt` and `cryptography` versions should be tracked and upgraded in a dedicated dependency pass.
