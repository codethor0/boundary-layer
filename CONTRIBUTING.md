# Contributing to BoundaryLayer

Thank you for contributing. BoundaryLayer values small, testable, documented changes.

## Development Setup

```bash
make setup
make up
make smoke
make demo
make test
make validate
```

## Pull Requests

GitHub Actions runs on every pull request to `main`:

- `make test`
- `make lint`
- Hygiene checks for tracked tooling artifacts and generated reports
- Secret pattern scan

Full Docker validation is not run in the default CI job. Run `make validate` locally when changing Docker, labs, metrics, or alert routing.

Use the pull request template and confirm:

- No secrets committed
- No generated reports committed (`VALIDATION_LOG.md`, `TEST_RESULTS.txt`, etc.)
- No prompt, Cursor, or agent artifacts committed
- Docs updated when behavior changes

## Pull Request Guidelines

1. One lab or one focused change per PR when possible
2. Include tests for new behavior
3. Update lab README and docs/CONTROLS_MAP.md
4. Run `make test` and `make lint` before submitting
5. Run `make validate` locally for Docker or detection changes
6. No emojis in code or documentation
7. No secrets or unsanitized logs

## Code Style

- Python 3.12+
- Ruff for lint and format
- FastAPI for API endpoints
- pytest for tests

## Definition of Done

See project README and [docs/RELEASE_CHECKLIST.md](docs/RELEASE_CHECKLIST.md) for full criteria. Changes must pass tests, lint, and relevant validation.

Adding a new lab? Follow [docs/ADD_A_LAB.md](docs/ADD_A_LAB.md).

## Repository Hygiene

Generated validation reports and command transcripts belong in local ZIP bundles only. Do not commit:

- `COMMAND_TRANSCRIPT.txt`
- `VALIDATION_LOG.md`
- `TEST_RESULTS.txt`
- `IMPLEMENTATION_REPORT.md`
- `DEPENDENCY_REPORT.md`
- `NEXT_STEPS.md`
- `.cursor/` or other editor tooling directories
