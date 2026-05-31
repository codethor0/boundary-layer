#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "BoundaryLayer container local smoke"

if ! command -v docker >/dev/null 2>&1; then
  echo "SKIP container smoke (docker not available)"
  exit 0
fi

git_sha="$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")"
image_repo="${CONTAINER_IMAGE_REPO:-boundary-layer-api}"
image_tag="${image_repo}:${git_sha}"

if ! docker image inspect "$image_tag" >/dev/null 2>&1; then
  echo "Image ${image_tag} not found; running container-build first"
  bash scripts/container-build.sh
fi

host_port="${CONTAINER_SMOKE_PORT:-18001}"
container_id="$(docker run -d -p "${host_port}:8000" \
  -e BOUNDARY_LAYER_PROFILE=local-lab \
  -e BOUNDARY_LAYER_ENV=development \
  "$image_tag")"

cleanup() {
  docker rm -f "$container_id" >/dev/null 2>&1 || true
}
trap cleanup EXIT

for _ in $(seq 1 20); do
  if curl -sf "http://127.0.0.1:${host_port}/health" >/dev/null; then
    echo "PASS container local smoke /health"
    exit 0
  fi
  sleep 1
done

echo "FAIL container local smoke /health did not become ready" >&2
exit 1
