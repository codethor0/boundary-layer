# PostgreSQL Write Storm Lab

Lab ID: `postgres-write-storm`

Endpoint: `POST /labs/postgres-write-storm/run`

## What this lab demonstrates

This lab simulates runaway prompt logging inserts that increase PostgreSQL write pressure on a single writer. It maps to Gap 1 from the BoundaryLayer article: uncontrolled application writes can saturate a primary database even when each insert is small.

## Safety and scope

- This lab does not attempt to crash PostgreSQL.
- It uses bounded synthetic inserts (default 250, maximum 1000).
- Records are synthetic and do not store real prompts.
- IDs use the `boundary-layer-write-storm-` namespace.
- This lab is local-only and defensive.

## Modes

### Vulnerable

Inserts the full requested batch (default 250) into `write_storm_events` when live PostgreSQL is enabled. No write throttle is applied. Returns `blocked: false`.

### Hardened

Applies a tenant write budget of 50 inserts. Excess requested writes are blocked with backpressure semantics. Returns `blocked: true`.

Optional request field:

```json
{
  "mode": "hardened",
  "requested_writes": 250
}
```

## Metrics

- `boundary_layer_postgres_write_storm_events_total{mode,result}`
- `boundary_layer_postgres_write_storm_blocked_writes_total{mode}`
- `boundary_layer_postgres_write_storm_insert_duration_seconds{mode}`

## Alerts

- `BoundaryLayerPostgresWriteStormDetected` - lab write storm activity threshold
- `BoundaryLayerPostgresWriteStormMitigated` - hardened mode blocked excess writes

These alerts use lab-generated metrics. They are not the same as external production PostgreSQL saturation alerts such as `PostgresPrimarySaturation`.

## What this lab does not simulate

- Real prompt content or PII storage
- Multi-region replication lag
- Disk exhaustion or WAL bloat at production scale
- External PostgreSQL exporter saturation metrics
