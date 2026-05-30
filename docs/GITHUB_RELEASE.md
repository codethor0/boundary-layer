# GitHub Release Guide

## Repository target

- **URL:** https://github.com/codethor0/boundary-layer
- **Owner:** codethor0
- **Name:** boundary-layer

## Suggested description

Open-source LLM infrastructure security lab for simulating and hardening AI system blast-radius risks.

Longer description for release notes or About fields:

BoundaryLayer is an open-source LLM infrastructure security lab for simulating, detecting, and hardening risks across tool routing, Redis, PostgreSQL, file uploads, prompt governance, SSE, circuit breakers, prompt cache isolation, Prometheus, and Alertmanager.

## Suggested topics

`llm-security`, `ai-security`, `appsec`, `devsecops`, `prometheus`, `alertmanager`, `redis`, `postgresql`, `fastapi`, `security-lab`, `prompt-injection`, `zero-trust`

### Set topics with GitHub CLI

If `gh` is authenticated:

```bash
gh repo edit codethor0/boundary-layer \
  --description "Open-source LLM infrastructure security lab for simulating and hardening AI system blast-radius risks." \
  --add-topic llm-security \
  --add-topic ai-security \
  --add-topic appsec \
  --add-topic devsecops \
  --add-topic prometheus \
  --add-topic alertmanager \
  --add-topic redis \
  --add-topic postgresql \
  --add-topic fastapi \
  --add-topic security-lab \
  --add-topic prompt-injection \
  --add-topic zero-trust
```

### Set topics manually

1. Open https://github.com/codethor0/boundary-layer
2. Click the gear icon next to About
3. Paste the suggested description above
4. Add the topics listed in this section
5. Save changes

## Initial setup

```bash
git remote -v

# If no origin exists:
git remote add origin git@github.com:codethor0/boundary-layer.git

# Or with HTTPS:
git remote add origin https://github.com/codethor0/boundary-layer.git
```

If `origin` already points elsewhere, review the current remote before changing it.

## Create repository with GitHub CLI

Only if the repository does not exist yet:

```bash
gh repo create codethor0/boundary-layer \
  --public \
  --description "Open-source LLM infrastructure security lab for simulating and hardening AI system blast-radius risks." \
  --source=. \
  --remote=origin
```

## Release process

1. Run `make test`
2. Run `make lint`
3. Run `docker compose down -v`
4. Run `make up`
5. Run `make validate`
6. Confirm no prompt artifacts are tracked in Git
7. Confirm generated reports are untracked
8. Confirm CI hygiene checks pass locally:
   ```bash
   git ls-files | grep -Ei '(^|/)\.cursor/|COMMAND_TRANSCRIPT|VALIDATION_LOG|TEST_RESULTS|IMPLEMENTATION_REPORT|DEPENDENCY_REPORT|NEXT_STEPS|GIT_STATUS|TREE|docker-compose-logs|prompt-artifact|cursor-prompt|agent-prompt|agent-report' && exit 1 || true
   ```
9. Tag release: `git tag -a vX.Y.Z -m "BoundaryLayer vX.Y.Z"`
10. Push branch and tag: `git push origin main && git push origin vX.Y.Z`
11. Create GitHub release from tag using notes from `CHANGELOG.md`

## Continuous integration

- **CI** (`.github/workflows/ci.yml`): runs on push and pull request to `main`
- **Docker Validate** (`.github/workflows/docker-validate.yml`): manual workflow for full stack validation

Default CI does not require Docker. Local `make validate` remains authoritative for releases.

## Push and tag

```bash
git push -u origin main

git tag -a v1.0.0 -m "BoundaryLayer v1.0.0"
git push origin v1.0.0
```

## Release notes template

```markdown
## BoundaryLayer v1.0.0

First public release of BoundaryLayer, an open-source LLM infrastructure security lab.

### Highlights

- Nine security labs with vulnerable and hardened modes
- Live Redis and PostgreSQL integration
- Prometheus metrics and Alertmanager local alert routing
- 162 passing tests
- Docker Compose local stack

### Quick start

git clone https://github.com/codethor0/boundary-layer.git
cd boundary-layer
make setup
make up
make validate

See CHANGELOG.md for version history.
```

## What stays out of GitHub

Generated reports, build transcripts, and editor tooling artifacts belong in local ZIP bundles only (reports) or are excluded entirely (tooling):

- `COMMAND_TRANSCRIPT.txt`
- `VALIDATION_LOG.md`
- `TEST_RESULTS.txt`
- `IMPLEMENTATION_REPORT.md`
- `DEPENDENCY_REPORT.md`
- `NEXT_STEPS.md`
- `GIT_STATUS.txt`
- `TREE.txt`
- `docker-compose-logs.txt`
- `.cursor/`, `.vscode/`, `.idea/`

Run `make bundle` after validation to create a review bundle in `~/Downloads/`. Bundles must not include `.cursor/`.

## v1.0.7 release notes template

```markdown
## BoundaryLayer v1.0.7

Final launch gate: logo redesign, README architecture diagrams, and full E2E validation.

### Highlights

- Stronger hand-authored SVG logo assets with concept review
- Core Mermaid diagrams in README
- Expanded README explanation and E2E validation documentation
```

## v1.0.6 release notes template

```markdown
## BoundaryLayer v1.0.6

Version consistency and final launch gate.

### Highlights

- Aligned API health version with the public release version
- Re-ran full live Docker validation
- Confirmed CI, badges, diagrams, logo assets, and public repository hygiene remain clean
```

## v1.0.5 release notes template

```markdown
## BoundaryLayer v1.0.5

Visual identity, expanded architecture diagrams, and end-to-end validation documentation.

### Highlights

- Hand-authored SVG logo assets
- Thirteen Mermaid diagrams in docs/DIAGRAMS.md
- Live Docker E2E validation guide in docs/E2E_VALIDATION.md
- README badge and visual identity polish
```

## v1.0.3 release notes template

```markdown
## BoundaryLayer v1.0.3

Public repository provenance cleanup.

### Highlights

- Cleaned public repository provenance
- Removed local tooling artifacts from public history
- Recreated public release tag from clean author history
- Confirmed generated reports and prompt artifacts remain excluded from Git
```

## v1.0.1 release notes template

```markdown
## BoundaryLayer v1.0.1

Public repository hygiene and architecture documentation update.

### Highlights

- Removed editor and tooling artifacts from the public repository
- Added Mermaid architecture diagrams in docs/DIAGRAMS.md
- Confirmed generated reports remain bundle-only artifacts
```
