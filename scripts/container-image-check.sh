#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "BoundaryLayer container image readiness check"

dockerfile="apps/api/Dockerfile"
if [[ ! -f "$dockerfile" ]]; then
  echo "FAIL missing $dockerfile" >&2
  exit 1
fi
echo "PASS Dockerfile present"

if grep -q '\.env' "$dockerfile"; then
  echo "FAIL Dockerfile references .env" >&2
  exit 1
fi
echo "PASS Dockerfile does not copy .env"

if ! command -v docker >/dev/null 2>&1; then
  echo "SKIP docker build (docker not available)"
  exit 0
fi

image_tag="boundary-layer-container-check:local"
docker build -f "$dockerfile" -t "$image_tag" "$ROOT" >/dev/null
echo "PASS docker build"

container_id="$(docker run -d -p 18000:8000 \
  -e BOUNDARY_LAYER_PROFILE=local-lab \
  -e BOUNDARY_LAYER_ENV=development \
  "$image_tag")"

cleanup() {
  docker rm -f "$container_id" >/dev/null 2>&1 || true
}
trap cleanup EXIT

for _ in $(seq 1 20); do
  if curl -sf http://127.0.0.1:18000/health >/dev/null; then
    echo "PASS container /health"
    exit 0
  fi
  sleep 1
done

echo "FAIL container /health did not become ready" >&2
exit 1
