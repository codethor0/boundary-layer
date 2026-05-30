#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
BUNDLE_NAME="boundary-layer-bundle-v1.0.10-${TIMESTAMP}"
STAGING_DIR="$(mktemp -d "/tmp/${BUNDLE_NAME}.XXXXXX")"
DOWNLOADS_DIR="${HOME}/Downloads"
ZIP_PATH="${DOWNLOADS_DIR}/${BUNDLE_NAME}.zip"
VENV="${REPO_ROOT}/.venv"
PYTEST="${VENV}/bin/pytest"

cleanup() {
  rm -rf "$STAGING_DIR"
}
trap cleanup EXIT

echo "==> Repository root: ${REPO_ROOT}"
echo "==> Staging directory: ${STAGING_DIR}"

echo "==> Exporting tracked source via git archive"
git archive --format=tar HEAD | tar -x -C "$STAGING_DIR"

generate_implementation_report() {
  cat > "${STAGING_DIR}/IMPLEMENTATION_REPORT.md" <<EOF
# Implementation Report (Bundle Only)

Generated: $(date -u +"%Y-%m-%dT%H:%M:%SZ")

This file is included in local release bundles only. It is not part of the public GitHub repository.

## Release

- Version: v1.0.10
- Commit: $(git rev-parse HEAD)
- Branch: $(git branch --show-current)

## Scope

BoundaryLayer v1.0.10 logo redesign and exploratory validation polish. Logo assets and documentation only. Nine security labs unchanged.

## Validation

Run \`make validate\` before creating a bundle. This report is generated at bundle time and does not replace live validation output.
EOF
}

generate_dependency_report() {
  cat > "${STAGING_DIR}/DEPENDENCY_REPORT.md" <<EOF
# Dependency Report (Bundle Only)

Generated: $(date -u +"%Y-%m-%dT%H:%M:%SZ")

## Runtime Dependencies (apps/api/requirements.txt)

| Package | Version | Purpose |
|---------|---------|---------|
| fastapi | 0.115.6 | HTTP API framework |
| uvicorn | 0.34.0 | ASGI server |
| httpx | 0.28.1 | HTTP client |
| pydantic | 2.10.4 | Request validation |
| pydantic-settings | 2.7.0 | Environment configuration |
| prometheus-client | 0.21.1 | Metrics exposition |
| redis | 5.2.1 | Live Redis lab integration |
| psycopg2-binary | 2.9.10 | Live PostgreSQL integration |

## Infrastructure Images

| Image | Purpose |
|-------|---------|
| postgres:16-alpine | Governance and write storm labs |
| redis:7-alpine | Redis and prompt cache labs |
| prom/prometheus:v2.51.0 | Metrics and alert rules |
| prom/alertmanager:v0.27.0 | Local alert routing |

See \`apps/api/requirements.txt\` and \`docker-compose.yml\` for authoritative versions.
EOF
}

generate_next_steps() {
  cat > "${STAGING_DIR}/NEXT_STEPS.md" <<EOF
# Next Steps (Bundle Only)

Generated: $(date -u +"%Y-%m-%dT%H:%M:%SZ")

## Post-v1.0 Opportunities

- Commented external Alertmanager receiver templates (Slack, PagerDuty)
- Architecture diagrams in docs
- CI workflow for \`make validate\`
- Harden in-process tool router and authz labs with richer simulations

## Known Technical Debt

- Tool router and authz labs still simulate in-process
- External Postgres saturation alert uses placeholder exporter metric name
- Alert webhook is in-memory and local-only
- Python 3.12 required locally
EOF
}

generate_command_transcript() {
  cat > "${STAGING_DIR}/COMMAND_TRANSCRIPT.txt" <<EOF
# BoundaryLayer Bundle Command Transcript

Generated: $(date -u +"%Y-%m-%dT%H:%M:%SZ")
Bundle: ${BUNDLE_NAME}.zip
Commit: $(git rev-parse HEAD)

This transcript records bundle generation context only. It is not part of the public GitHub repository.

## Repository state at bundle time

\`\`\`
$(git status --short 2>&1 || true)
\`\`\`

## Recent commits

\`\`\`
$(git log --oneline -10)
\`\`\`

## Bundle generation

\`\`\`
bash scripts/collect-bundle.sh
\`\`\`

EOF
}

overlay_local_report() {
  local name="$1"
  if [[ -f "${REPO_ROOT}/${name}" ]]; then
    cp "${REPO_ROOT}/${name}" "${STAGING_DIR}/${name}"
  fi
}

generate_or_overlay_test_results() {
  if [[ -f "${REPO_ROOT}/TEST_RESULTS.txt" ]]; then
    cp "${REPO_ROOT}/TEST_RESULTS.txt" "${STAGING_DIR}/TEST_RESULTS.txt"
    return
  fi
  if [[ -x "${PYTEST}" ]]; then
    echo "==> Generating TEST_RESULTS.txt via pytest"
    if ${PYTEST} tests/ -v --tb=short > "${STAGING_DIR}/TEST_RESULTS.txt" 2>&1; then
      echo "FINAL TEST STATUS: PASS" >> "${STAGING_DIR}/TEST_RESULTS.txt"
    else
      echo "FINAL TEST STATUS: FAIL" >> "${STAGING_DIR}/TEST_RESULTS.txt"
      exit 1
    fi
    return
  fi
  cat > "${STAGING_DIR}/TEST_RESULTS.txt" <<EOF
TEST_RESULTS.txt not found. Run make validate or make test before make bundle.
EOF
}

generate_implementation_report
generate_dependency_report
generate_next_steps
generate_command_transcript
overlay_local_report "VALIDATION_LOG.md"
if [[ ! -f "${STAGING_DIR}/VALIDATION_LOG.md" ]]; then
  cat > "${STAGING_DIR}/VALIDATION_LOG.md" <<EOF
# Validation Log (Bundle Only)

Generated: $(date -u +"%Y-%m-%dT%H:%M:%SZ")

No local VALIDATION_LOG.md was found. Run \`make validate\` before \`make bundle\` for full validation output.
EOF
fi
generate_or_overlay_test_results

echo "==> Generating TREE.txt"
find "$STAGING_DIR" -type f | sed "s|^${STAGING_DIR}/||" | sort > "${STAGING_DIR}/TREE.txt"

echo "==> Generating GIT_STATUS.txt"
{
  echo "repository_root: ${REPO_ROOT}"
  echo "branch: $(git branch --show-current)"
  echo "commit: $(git rev-parse HEAD)"
  echo "tag: $(git describe --tags --exact-match 2>/dev/null || echo none)"
  echo ""
  git status
  echo ""
  git log -5 --oneline
} > "${STAGING_DIR}/GIT_STATUS.txt"

echo "==> Capturing docker compose logs"
if command -v docker >/dev/null 2>&1 && docker compose ps -q 2>/dev/null | grep -q .; then
  docker compose logs --no-color > "${STAGING_DIR}/docker-compose-logs.txt" 2>&1 || true
else
  echo "Docker compose services not running or docker unavailable" \
    > "${STAGING_DIR}/docker-compose-logs.txt"
fi

echo "==> Creating ZIP at ${ZIP_PATH}"
(
  cd "$STAGING_DIR"
  zip -r "$ZIP_PATH" . -x "*.DS_Store" -x ".cursor/*"
)

echo "==> Verifying bundle contents"
BAD_PATTERNS=(
  "artifacts/bundle-"
  ".pytest_cache"
  ".ruff_cache"
  "__pycache__"
  ".venv"
  ".git/"
  ".env"
  ".cursor/"
  "prompt-artifacts/"
  "cursor-prompts/"
  "agent-prompts/"
)
for pattern in "${BAD_PATTERNS[@]}"; do
  if [[ "$pattern" == ".env" ]]; then
    if unzip -l "$ZIP_PATH" | grep -E '(^|/)\.env$' >/dev/null; then
      echo "ERROR: Bundle contains excluded path pattern: ${pattern}" >&2
      exit 1
    fi
  elif unzip -l "$ZIP_PATH" | grep -q "${pattern}"; then
    echo "ERROR: Bundle contains excluded path pattern: ${pattern}" >&2
    exit 1
  fi
done

REQUIRED_PATHS=(
  "README.md"
  "CHANGELOG.md"
  "Makefile"
  "docker-compose.yml"
  "apps/api/main.py"
  "docs/RELEASE_CHECKLIST.md"
  "docs/GITHUB_RELEASE.md"
  "docs/DIAGRAMS.md"
  "scripts/validate.sh"
  "scripts/collect-bundle.sh"
  "IMPLEMENTATION_REPORT.md"
  "VALIDATION_LOG.md"
  "TEST_RESULTS.txt"
  "TREE.txt"
  "GIT_STATUS.txt"
  "COMMAND_TRANSCRIPT.txt"
)
for path in "${REQUIRED_PATHS[@]}"; do
  if ! unzip -l "$ZIP_PATH" | awk '{print $4}' | grep -qx "$path"; then
    echo "ERROR: Bundle missing required path: ${path}" >&2
    exit 1
  fi
done

echo "Bundle created: ${ZIP_PATH}"
