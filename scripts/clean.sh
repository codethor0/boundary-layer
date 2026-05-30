#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "==> Stopping Docker Compose services"
docker compose down -v 2>/dev/null || true

echo "==> Removing generated cache and artifact directories"
find . -type d -name '__pycache__' -prune -exec rm -rf {} + 2>/dev/null || true
rm -rf \
  .venv \
  .pytest_cache \
  .ruff_cache \
  .mypy_cache \
  htmlcov \
  .coverage \
  artifacts \
  2>/dev/null || true

find . -type f -name '*.pyc' -delete 2>/dev/null || true

echo "Clean complete."
