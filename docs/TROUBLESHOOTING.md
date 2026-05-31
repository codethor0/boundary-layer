# Troubleshooting

Common issues when running BoundaryLayer locally.

## Docker not running

**Symptom:** `make up` fails with Docker daemon errors.

**Fix:** Start Docker Desktop or your Docker service, then:

```bash
docker compose ps
make up
```

## Port already in use

BoundaryLayer dev stack binds these host ports:

| Port | Service |
|------|---------|
| 8000 | API |
| 9090 | Prometheus |
| 9093 | Alertmanager |
| 8081 | Alert webhook |

**Symptom:** `bind: address already in use`.

**Find process:**

```bash
lsof -i :8000
lsof -i :9090
lsof -i :9093
lsof -i :8081
```

**Fix:** Stop the conflicting process or run `make down` / `docker compose down` from another BoundaryLayer checkout. Then:

```bash
docker compose down -v
make up
make smoke
```

## API not reachable

**Symptom:** `make smoke` or `make demo` prints: `BoundaryLayer API is not running. Run make up first.`

```bash
docker compose ps
docker compose logs api --tail=100
curl -sf http://localhost:8000/health
make up
```

## Prometheus alert delay

**Symptom:** Metric updated but webhook empty for 30+ seconds.

Alerts evaluate on scrape intervals (15s) plus rule `for` durations. **Wait up to 60 seconds** after triggering a lab.

```bash
curl -sf http://localhost:9090/-/healthy
docker compose logs prometheus --tail=100
```

See [OBSERVABILITY_WALKTHROUGH.md](OBSERVABILITY_WALKTHROUGH.md).

## Alert webhook empty

```bash
curl -sf http://localhost:8081/health
curl -sf http://localhost:8081/alerts
docker compose logs alert-webhook --tail=100
docker compose logs alertmanager --tail=100
```

Clear and re-trigger:

```bash
curl -sf -X DELETE http://localhost:8081/alerts
curl -sf -X POST http://localhost:8000/labs/circuit-breaker/run \
  -H "Content-Type: application/json" -d '{"mode":"hardened"}'
```

Run `make validate-alerts` for automated delivery checks.

## Redis not healthy

```bash
docker compose ps redis
docker compose logs redis --tail=100
docker compose restart redis
```

Redis labs fall back to in-process simulation if Redis is down; metrics still update but live behavior differs.

## PostgreSQL not healthy

```bash
docker compose ps postgres
docker compose logs postgres --tail=100
docker compose restart postgres
```

Governance and write-storm labs may use fallback when Postgres is unavailable.

## make validate-prod replaced dev stack

**Symptom:** Ports conflict or dev services stopped after production validation.

`make validate-prod` uses `docker-compose.prod.yml` on a separate project name but may compete for host ports on some setups.

```bash
make prod-down
docker compose down -v
make up
make smoke
```

## Python version mismatch

BoundaryLayer targets **Python 3.12+**.

```bash
python3.12 --version
make setup
make test
```

## pip-audit not found

Install dev dependencies:

```bash
make setup
.venv/bin/pip install pip-audit
pip-audit -r apps/api/requirements.txt
```

Or run the dependency audit included in `make validate`.

## Docker compose cleanup

Full reset (destroys local volumes):

```bash
docker compose down -v
make up
make smoke
make demo
```

## Fresh-volume restore validation fails

`make validate-restore-fresh-volume` destroys dev Compose volumes. Run only on a machine you control.

```bash
docker compose down -v
make up
make validate-restore-fresh-volume
```

If restore row counts mismatch, inspect Postgres logs and retry after `make up`. Set `KEEP_RESTORE_ARTIFACTS=true` to keep the backup file for manual inspection.

## Validation failures

| Command | When to use |
|---------|-------------|
| `make smoke` | Fast sanity (~30s) |
| `make demo` | Guided demo with alert poll |
| `make validate-alerts` | Extended alert delivery |
| `make validate` | Full local gate (several minutes) |
| `make validate-restore-fresh-volume` | Fresh-volume Postgres proof (destroys dev volumes) |
| `make validate-prod` | Production-like profile on controlled machines |

Collect logs:

```bash
docker compose logs api --tail=100
docker compose logs prometheus --tail=100
docker compose logs alertmanager --tail=100
docker compose logs alert-webhook --tail=100
```

## Related

- [WORKSHOP.md](WORKSHOP.md)
- [E2E_VALIDATION.md](E2E_VALIDATION.md)
- [BACKUP_RESTORE.md](BACKUP_RESTORE.md)
