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
