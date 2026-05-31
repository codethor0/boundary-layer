# Audit and SIEM Plan

BoundaryLayer Production SaaS audit logging is **foundational only** today. The `audit_events` table and auth/cross-tenant decision writes exist in production-saas, but logs are **not immutable** and are **not exported to a SIEM**.

## Current state

| Capability | Status |
|------------|--------|
| Database-backed audit events | Implemented (production-saas) |
| Audit export interface | Implemented (`apps/api/audit_export.py`; local Postgres sink) |
| External immutable sink adapters | Shell only (fail closed) |
| SIEM export | Not implemented |
| Retention enforcement | Config scaffolding only |
| Operator runbook | Not implemented |

## Target architecture

```text
API auth/tenancy decisions -> audit writer -> immutable sink -> SIEM/export pipeline
```

### Recommended immutable sinks

| Provider | `AUDIT_SINK_PROVIDER` | Notes |
|----------|----------------------|-------|
| PostgreSQL (current) | `postgres` | Mutable; acceptable for local lab only |
| S3 object lock | `s3` | WORM bucket with versioning + lifecycle |
| CloudWatch Logs | `cloudwatch` | AWS-native with retention policies |
| GCP Cloud Logging | `gcp_logging` | Centralized logging with export |
| Azure Monitor | `azure_monitor` | Diagnostic settings + export |
| Splunk HEC | `splunk` | Enterprise SIEM ingestion |
| Datadog Logs | `datadog` | SaaS observability platform |

## Configuration scaffolding

```bash
AUDIT_SINK_PROVIDER=postgres|s3|cloudwatch|gcp_logging|azure_monitor|splunk|datadog
AUDIT_IMMUTABLE_REQUIRED=true
AUDIT_RETENTION_DAYS=365
AUDIT_EXPORT_ENABLED=false
```

When `AUDIT_IMMUTABLE_REQUIRED=true`, production-saas managed-service policy checks reject `AUDIT_SINK_PROVIDER=postgres` until an immutable sink adapter is implemented.

## Required work before 10/10

1. Implement immutable audit sink adapter(s) behind a writer interface.
2. Enforce append-only writes with tamper detection.
3. Configure retention and legal hold policies.
4. Export to SIEM with correlation IDs tied to request context.
5. Validate export path in staging with synthetic audit events.
6. Document operator procedures for audit retrieval and incident response.

## Score note

Audit remains **foundational (3/10)** until an immutable sink is implemented and validated in staging. Do not claim SIEM readiness based on config fields alone.
