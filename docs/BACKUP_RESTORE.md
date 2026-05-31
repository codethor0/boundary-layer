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

`make validate` and `make validate-prod` include a backup/restore **roundtrip smoke test** that drops and restores the `write_storm_events` table from a `pg_dump` backup. This proves the scripts work and basic table-level recovery is possible.

It is **not** a full fresh-volume database disaster recovery simulation. Restoring an entire Postgres data directory into a new volume is documented below but not exercised by the default validation gates.

### What table-scoped restore proves

- `pg_dump` / `pg_restore` scripts run successfully against the live compose Postgres container.
- The `write_storm_events` table can be dropped and recovered from a compressed backup without manual SQL surgery.
- Backup and restore scripts detect dev vs production-like compose project names.

### What it does not prove

- Recovery of the entire Postgres data directory into a **new Docker volume** with zero manual steps.
- Point-in-time recovery, replication failover, or off-host backup integrity.
- Redis session/cache recovery (Redis is ephemeral in the lab by design).

### Planned fresh-volume restore validation

Future maintainers can add `scripts/validate-restore-fresh-volume.sh` (not wired into `make validate` until reliable):

1. `docker compose down -v` — destroy dev volumes.
2. `make up` — create fresh Postgres volume.
3. Seed labs (governance + write storm runs) to populate tables.
4. `make backup` — write timestamped dump.
5. `docker compose down -v` again — simulate volume loss.
6. `make up` — empty database.
7. `make restore BACKUP=...` — restore full dump (not table-only).
8. Assert row counts in `write_storm_events` and governance audit tables match pre-loss expectations.

This script is optional and high-impact; document results in `VALIDATION_LOG.md` locally only. Do not commit generated reports.

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
