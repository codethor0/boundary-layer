# Backup and Restore

BoundaryLayer stores lab state in PostgreSQL (governance records, write storm events). Redis holds ephemeral lab session/cache data and is not backed up by default.

## Backup

With the production or local stack running:

```bash
make backup
# or
bash scripts/backup-postgres.sh
```

Backups are written to `backups/postgres/boundary-layer-<timestamp>.sql.gz` (gitignored).

The script auto-detects whether the production (`boundary-layer-prod`) or local compose stack is running.

## Restore

```bash
make restore BACKUP=backups/postgres/boundary-layer-20260101T120000Z.sql.gz
# or
bash scripts/restore-postgres.sh backups/postgres/boundary-layer-20260101T120000Z.sql.gz
```

Restore runs against the currently running Postgres container. Stop write traffic before restoring production data.

## Validation scope (honest limits)

`make validate` and `make validate-prod` include a backup/restore **roundtrip smoke test** that drops and restores the `write_storm_events` table from a `pg_dump` backup.

### What table-scoped restore proves (`make validate`)

- `pg_dump` scripts run successfully against the live compose Postgres container.
- The `write_storm_events` table can be dropped and recovered from a compressed backup without manual SQL surgery.
- Backup and restore scripts detect dev vs production-like compose project names.

### Fresh-volume restore validation (`make validate-restore-fresh-volume`)

Script: `scripts/validate-restore-fresh-volume.sh`

```bash
make validate-restore-fresh-volume
```

This local-only proof:

1. Destroys dev Compose volumes (`docker compose down -v`).
2. Starts a fresh stack and seeds governance (hardened) + write storm lab data (`requested_writes: 25`).
3. Creates a full `pg_dump` backup via `scripts/backup-postgres.sh`.
4. Destroys volumes again (simulated volume loss).
5. Restores the full dump into a fresh Postgres volume via `scripts/restore-postgres.sh`.
6. Verifies row counts in `write_storm_events` (expected 25) and `deletion_audit` match pre-loss counts.

**Warning:** `make validate-restore-fresh-volume` resets BoundaryLayer's local Docker Compose volumes. It is safe for the lab, but it will delete local lab data.

Temporary backups land in `backups/postgres/restore-validation/` (gitignored) unless `KEEP_RESTORE_ARTIFACTS=true`.

### What fresh-volume validation proves

- Full database dump and restore works against a **new** Docker Postgres volume in the dev lab.
- Governance and write storm records survive volume replacement when restored from backup.

### What it still does not prove

- Off-host backup storage, replication failover, or point-in-time recovery.
- Production-like compose project restore without manual steps.
- Redis session/cache recovery (Redis is ephemeral in the lab by design).

## Production schedule (recommended)

1. Daily `pg_dump` via cron or your orchestrator backup agent
2. Store backups off-host (S3, GCS, encrypted volume snapshots)
3. Test restore quarterly with `make restore`

## Volume snapshots

For Docker volume-level backup of `boundary-layer-prod_postgres_data`:

```bash
docker run --rm \
  -v boundary-layer-prod_postgres_data:/volume \
  -v "$(pwd)/backups/postgres:/backup" \
  alpine tar czf /backup/postgres-volume-$(date -u +%Y%m%dT%H%M%SZ).tar.gz -C /volume .
```

Restore requires stopping Postgres and extracting the archive into a fresh volume.

## Validation

`make validate-prod` runs a backup smoke test before tearing down the production stack.
