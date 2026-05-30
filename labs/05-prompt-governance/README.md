# Prompt Governance Tracker Lab

Demonstrates incomplete prompt lifecycle deletion leaving downstream PostgreSQL records.

## Modes

- **vulnerable**: Deletes only the primary `prompt_requests` row; downstream tables retain orphaned records.
- **hardened**: Cascade-deletes downstream records, verifies zero orphans, and writes a `deletion_audit` row.

## Live PostgreSQL Mode

When `BOUNDARY_LAYER_POSTGRES_LIVE=true` (default in Docker Compose):

- Connects to `POSTGRES_HOST` / `POSTGRES_DB`
- Initializes schema via `apps/api/db.py`
- Uses IDs prefixed with `boundary-layer-governance-`

When `BOUNDARY_LAYER_POSTGRES_LIVE=false`:

- Uses deterministic in-memory fallback for unit tests

## Validation

```bash
curl -X POST http://localhost:8000/labs/governance/run \
  -H "Content-Type: application/json" \
  -d '{"mode":"vulnerable"}'

curl -X POST http://localhost:8000/labs/governance/run \
  -H "Content-Type: application/json" \
  -d '{"mode":"hardened"}'

curl -sf http://localhost:8000/metrics | grep boundary_layer_prompt_deletion_orphan_records_total
```

## Risk

Incomplete prompt deletion leaves retrievable downstream artifacts in logs, tools, eval, and training queues.

## Control

Downstream dependency audit, cascade deletion, and PostgreSQL audit records.
