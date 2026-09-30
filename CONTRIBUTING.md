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
- No local bundle outputs or generated transcripts committed (`TEST_RESULTS.txt`, `COMMAND_TRANSCRIPT.txt`, etc.)
- No prompt, model transcript, local editor metadata, or agent artifacts committed
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

Maintained project documentation may include implementation, dependency, validation, and next-step records. Local bundle outputs and command transcripts belong in ZIP bundles only. Do not commit:

- `COMMAND_TRANSCRIPT.txt`
- `TEST_RESULTS.txt`
- `GIT_STATUS.txt`
- `TREE.txt`
- `docker-compose-logs.txt`
- Local editor metadata or tooling directories
