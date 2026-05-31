# DR and On-Call Runbook (Starter)

**Status:** Documented only. DR and on-call procedures are **not tested** unless explicitly validated and recorded in [LIVE_STAGING_EVIDENCE_TEMPLATE.md](LIVE_STAGING_EVIDENCE_TEMPLATE.md) or operator runbooks.

## Targets (placeholders)

| Metric | Staging target | Production target (future) |
|--------|----------------|----------------------------|
| RTO | 4 hours | 1 hour |
| RPO | 24 hours | 15 minutes |

## Backup verification

- RDS automated backups enabled (staging minimum 7-day retention)
- S3 versioning enabled on artifact bucket
- Secrets Manager rotation policy documented
- Quarterly restore drill (not yet performed)

## Restore verification

```bash
# Local lab proof (not staging DR):
make validate-restore-fresh-volume
```

Staging RDS point-in-time restore: operator procedure in cloud console; **not automated in repo**.

## Incident severity levels

| Level | Description | Response |
|-------|-------------|----------|
| SEV1 | Staging API down, auth broken, data exposure suspected | Immediate operator response |
| SEV2 | Degraded performance, single managed service failure | Respond within 1 hour |
| SEV3 | Non-critical monitoring gap | Next business day |
| SEV4 | Documentation/tooling issue | Backlog |

## Pager escalation (placeholder)

- Primary: operator on-call rotation (not configured in repo)
- Secondary: platform lead
- Escalation tool: PagerDuty/Opsgenie (integrate with Alertmanager in future pass)

## Runbook: Database outage

1. Confirm RDS status in AWS console
2. Check connection errors in API logs (no secrets in tickets)
3. Fail over to Multi-AZ standby if enabled
4. If restore required, use latest snapshot or PITR
5. Re-run migrations if needed (`BOUNDARY_LAYER_RUN_MIGRATIONS=true` in controlled deploy)
6. Run `make live-staging-validation-package` after recovery

## Runbook: Redis outage

1. Confirm ElastiCache cluster status
2. API may degrade rate limiting; verify fail-closed behavior in production-saas
3. Restore from snapshot or rebuild empty cache (tenant keys are ephemeral except audit-critical paths)
4. Re-run live Redis managed-service check

## Runbook: OIDC outage

1. Confirm IdP status page
2. Staging API should reject invalid/missing tokens (401)
3. Do not disable auth in production-saas profile
4. Communicate staging maintenance window

## Runbook: Secret manager outage

1. Confirm Secrets Manager API availability
2. Restart tasks if secret cache TTL expired during outage
3. Rotate compromised secrets if exposure suspected
4. Re-run secret manager live check (value never logged)

## Runbook: Object storage outage

1. Confirm S3 bucket and IAM policies
2. Labs requiring object storage may fail; verify error responses
3. Restore bucket policy from IaC if misconfigured

## Rollback procedure

1. Identify last known good ECS task definition / image digest
2. Update service to previous revision
3. Run staging smoke live
4. Document in incident ticket

## Post-incident review template

- Timeline (UTC)
- Root cause
- Customer/tenant impact (staging: internal only)
- What went well
- Action items with owners
- Follow-up date

## Future validation checklist

- [ ] Staging RDS restore drill performed and documented
- [ ] ECS rollback drill performed
- [ ] On-call rotation configured with paging
- [ ] Tabletop exercise completed
- [ ] RTO/RPO measured against targets
