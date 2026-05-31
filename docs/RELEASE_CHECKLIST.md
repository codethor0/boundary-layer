# Release Checklist

Use this checklist before tagging a BoundaryLayer release or publishing a GitHub release.

## Pre-release validation

- [ ] Run `make setup`
- [ ] Run `make test` (173 tests passing)
- [ ] Run `make lint`
- [ ] Run `docker compose down -v && make up`
- [ ] Run `make validate` or follow [E2E_VALIDATION.md](E2E_VALIDATION.md) for live Docker checks
- [ ] Run secret scan (included in `make validate`)
- [ ] Verify Prometheus health at http://localhost:9090/-/healthy
- [ ] Verify Alertmanager health at http://localhost:9093/-/healthy
- [ ] Verify alert webhook health at http://localhost:8081/health
- [ ] Confirm `BoundaryLayerInferenceCircuitBreakerOpen` alert delivery (included in validate)

## Repository hygiene

- [ ] Verify no prompt artifacts are tracked in Git
- [ ] Verify no generated reports are tracked (`COMMAND_TRANSCRIPT.txt`, `VALIDATION_LOG.md`, etc.)
- [ ] Verify no editor or tooling artifacts are tracked (`.cursor/`, `.vscode/`, `.idea/`)
- [ ] Verify `.env` is not tracked
- [ ] Verify `git status` is clean before tagging
- [ ] Confirm logo SVG validation passes in `make validate`
- [ ] Confirm README architecture diagrams render on GitHub
- [ ] Confirm [E2E_VALIDATION.md](E2E_VALIDATION.md) matches current endpoints

## Bundle (local only)

- [ ] Run `make bundle` after validation
- [ ] Confirm bundle path under `~/Downloads/boundary-layer-bundle-v1.0.*.zip`
- [ ] Confirm bundle includes generated reports but not `.cursor/`
- [ ] Confirm bundle includes generated reports but GitHub repo does not

## CI and hygiene

Release owners should confirm:

- [ ] GitHub Actions CI workflow passes on `main` (see https://github.com/codethor0/boundary-layer/actions)
- [ ] Manual Docker Validate workflow is available (`.github/workflows/docker-validate.yml`)
- [ ] Local `make validate` remains authoritative for full-stack release validation
- [ ] Confirm GitHub Actions CI passes on `main` (or will pass after merge)
- [ ] Run local hygiene check:
  ```bash
  git ls-files | grep -Ei '(^|/)\.cursor/|COMMAND_TRANSCRIPT|VALIDATION_LOG|TEST_RESULTS|IMPLEMENTATION_REPORT|DEPENDENCY_REPORT|NEXT_STEPS|GIT_STATUS|TREE|docker-compose-logs|prompt-artifact|cursor-prompt|agent-prompt|agent-report|cursor_boundarylayer|project_requiremen' && exit 1 || true
  ```

## Deep QA (v1.0.9)

- [ ] Run deeper QA per [DEEP_QA.md](DEEP_QA.md)
- [ ] Confirm invalid inputs fail closed (422)
- [ ] Confirm metrics families present after lab runs
- [ ] Confirm Redis keys are namespaced under `boundary_layer:lab:*`
- [ ] Confirm PostgreSQL governance and write storm state matches expected behavior
- [ ] Confirm Prometheus targets healthy and six required alert rules load
- [ ] Confirm restart recovery (API and observability stack)
- [ ] Inspect service log tails for tracebacks or fatal errors

## Live release gate (v1.0.8)

- [ ] Run full live Docker gate per [LIVE_RELEASE_GATE.md](LIVE_RELEASE_GATE.md)
- [ ] Confirm 18 lab JSON outputs have required shape
- [ ] Confirm Prometheus targets and required alert rules load
- [ ] Confirm `BoundaryLayerInferenceCircuitBreakerOpen` delivery within 60 seconds
- [ ] Inspect service log tails for tracebacks or fatal errors

## Public provenance (v1.0.3)

- [ ] Confirm commit history shows intended project owner identity only
- [ ] Confirm old release tags that expose prior history are removed from GitHub
- [ ] Publish `v1.0.3` as the clean public release tag
- [ ] Note: GitHub contributor display may cache; verify commit history as source of truth

## GitHub release

- [ ] Create or verify public repo at https://github.com/codethor0/boundary-layer
- [ ] Push `main`
- [ ] Tag release (for example `v1.0.0`)
- [ ] Push tag
- [ ] Create GitHub release with notes from CHANGELOG.md

See [GITHUB_RELEASE.md](GITHUB_RELEASE.md) for push and tag commands.
