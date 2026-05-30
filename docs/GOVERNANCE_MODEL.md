# Governance Model

## Prompt Lifecycle

BoundaryLayer models prompt lifecycle as a graph of dependent artifacts stored in PostgreSQL when live mode is enabled:

```
prompt_requests (primary)
  -> prompt_logs
  -> tool_records
  -> evaluation_queue
  -> training_queue
  -> deletion_audit (hardened mode evidence)
```

## Schema

Tables are created automatically by `apps/api/db.py`:

- `prompt_requests` - primary prompt request records
- `prompt_logs` - invocation logs
- `tool_records` - tool execution artifacts
- `evaluation_queue` - offline evaluation queue entries
- `training_queue` - training pipeline queue entries
- `deletion_audit` - hardened deletion audit evidence
- `write_storm_events` - synthetic write storm lab records

All governance lab records use IDs prefixed with `boundary-layer-governance-`. Write storm records use `boundary-layer-write-storm-`.

## Vulnerable Behavior

The primary `prompt_requests` row is soft-deleted (`deleted_at` set). Downstream rows remain active. Orphan detection counts downstream rows whose parent is deleted but child is not.

## Hardened Behavior

All downstream rows are soft-deleted. Orphan count is queried from PostgreSQL. A row is inserted into `deletion_audit` with mode, orphan count, and completion flag.

## Metrics

- `boundary_layer_prompt_deletion_orphan_records_total` increments by live orphan count when orphans exist
- `boundary_layer_governance_deletion_audits_total{mode,complete}` increments when audit rows are written

## Write Storm Metrics

- `boundary_layer_postgres_write_storm_events_total{mode,result}` increments by inserted synthetic records
- `boundary_layer_postgres_write_storm_blocked_writes_total{mode}` increments when hardened mode blocks excess writes
- `boundary_layer_postgres_write_storm_insert_duration_seconds{mode}` observes batch insert duration

Lab write storm alerts are distinct from external production PostgreSQL saturation metrics.

## Fallback Mode

When `BOUNDARY_LAYER_POSTGRES_LIVE=false`, the lab uses deterministic in-memory simulation for unit tests without requiring PostgreSQL.

## Validation

```bash
curl -X POST http://localhost:8000/labs/governance/run \
  -H "Content-Type: application/json" \
  -d '{"mode":"hardened"}'

docker compose exec -T postgres psql -U boundary_layer -d boundary_layer \
  -c "SELECT mode, orphan_count, complete FROM deletion_audit ORDER BY created_at DESC LIMIT 5;"
```
