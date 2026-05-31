# Add a Lab to BoundaryLayer

Guide for contributors adding a new defensive infrastructure lab without changing existing lab API shapes.

## Lab folder structure

```
labs/
  your_lab.py              # run_vulnerable / run_hardened logic
  NN-your-lab-name/
    README.md              # risk, controls, curl examples
tests/
  test_your_lab.py
  test_api_your_lab.py     # if API wiring needs coverage
```

Numbered subfolders (`01-`, `02-`, …) are documentation anchors; Python module lives at `labs/your_lab.py`.

## Python module pattern

1. Define `RISK` and `HARDENED_CONTROL` strings.
2. Implement `run_vulnerable(...)` returning a dict with keys: `lab`, `mode`, `blocked`, `risk`, `control`, `events`, `summary`.
3. Implement `run_hardened(...)` with `blocked: True` when control applies.
4. Call metrics helpers from `apps/api/metrics.py` (for example `record_lab_run`, domain-specific counters).
5. Keep execution deterministic and local-safe. Use live Redis/PostgreSQL only when justified; document fallback behavior.

## API route pattern

In `apps/api/main.py`:

1. Add Pydantic request model if the lab needs extra fields (follow `LabRequest`, `WriteStormLabRequest`, etc.).
2. Register `POST /labs/{slug}/run` handler that validates input, calls lab module, strips internal keys, returns JSON.
3. Add lab slug to `GET /labs` list.

**Do not change response shapes of existing labs.**

## Vulnerable vs hardened expectations

| Mode | `blocked` | Purpose |
|------|-----------|---------|
| vulnerable | `false` (usually) | Show unsafe default blast radius |
| hardened | `true` (usually) | Show defensive control blocking or mitigating |

Both modes must increment `boundary_layer_lab_runs_total` with correct `result` label.

## Metrics requirements

1. Add counters/gauges/histograms in `apps/api/metrics.py` with `boundary_layer_` prefix.
2. Expose recording helpers; call from lab module.
3. Document in [docs/METRICS.md](METRICS.md) and [docs/CONTROLS_MAP.md](CONTROLS_MAP.md).

## Prometheus alert requirements

1. Add rule(s) to `detections/prometheus/alerts.yml` under the appropriate group.
2. Use `increase(...[5m])` or gauge thresholds consistent with existing rules.
3. Prefer alert names prefixed with `BoundaryLayer`.
4. If delivery should be gated, add check to `scripts/validate-alerts.sh` only when stable (avoid flaky CI).

## Validation script updates

Update `scripts/validate.sh`:

1. Add lab to vulnerable/hardened curl matrix if not already covered generically.
2. Add metric name to `REQUIRED_METRICS` if new.
3. Run `make validate` locally before submitting.

## Test requirements

1. Unit tests for lab module (`tests/test_*.py`).
2. API tests for route, validation errors (422), and JSON shape.
3. No secrets, no emojis, no skipped assertions that fake success.

## Lab README requirements

Each `labs/NN-*/README.md` should include:

- Risk statement
- Vulnerable and hardened curl examples
- Expected JSON excerpts
- Metrics and alert names
- Live vs simulated note

## Documentation updates

When adding a lab, update:

- [README.md](../README.md) labs table
- [docs/EXAMPLES.md](EXAMPLES.md)
- [docs/LIVE_VS_SIMULATED.md](LIVE_VS_SIMULATED.md)
- [docs/WORKSHOP.md](WORKSHOP.md) if workshop-relevant
- [CHANGELOG.md](../CHANGELOG.md) under Unreleased

## Bundle and release

Run `make bundle` locally before release; new docs must appear in the ZIP. Do not commit bundles to Git.

## Checklist

### Code

- [ ] Lab module with vulnerable/hardened paths
- [ ] API route and request validation
- [ ] Listed in `GET /labs`

### Tests

- [ ] Lab unit tests
- [ ] API integration tests
- [ ] `make test` passes

### Metrics

- [ ] Prometheus metrics with helpers
- [ ] `REQUIRED_METRICS` updated if needed

### Alerts

- [ ] `alerts.yml` rules added
- [ ] CONTROLS_MAP updated

### Docs

- [ ] Lab README
- [ ] EXAMPLES, LIVE_VS_SIMULATED, METRICS

### Validation

- [ ] `make smoke` and `make validate` pass with stack up

### Bundle

- [ ] `make bundle` includes new docs (local only)

### Known limitations

- [ ] Document what the lab does **not** simulate

## Related

- [CONTRIBUTING.md](../CONTRIBUTING.md)
- [RELEASE_CHECKLIST.md](RELEASE_CHECKLIST.md)
- [E2E_VALIDATION.md](E2E_VALIDATION.md)
