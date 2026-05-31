#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

dockerfile="apps/api/Dockerfile"
if [[ ! -f "$dockerfile" ]]; then
  echo "FAIL missing $dockerfile" >&2
  exit 1
fi

git_sha="$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")"
version_tag="${BOUNDARY_LAYER_VERSION:-1.3.5}"
image_repo="${CONTAINER_IMAGE_REPO:-boundary-layer-api}"
image_sha="${image_repo}:${git_sha}"
image_version="${image_repo}:${version_tag}"
image_staging="${image_repo}:staging"

echo "BoundaryLayer container build"
echo "Tags: ${image_sha}, ${image_version}, ${image_staging}"

if ! command -v docker >/dev/null 2>&1; then
  echo "SKIP docker build (docker not available)"
  exit 0
fi

docker build -f "$dockerfile" -t "$image_sha" -t "$image_version" -t "$image_staging" "$ROOT"
echo "PASS docker build"

if [[ "${PUSH_IMAGE:-}" == "true" ]]; then
  registry="${CONTAINER_REGISTRY:-}"
  if [[ -z "$registry" ]]; then
    echo "FAIL PUSH_IMAGE=true requires CONTAINER_REGISTRY" >&2
    exit 1
  fi
  remote_sha="${registry}/${image_sha}"
  remote_version="${registry}/${image_version}"
  remote_staging="${registry}/${image_staging}"
  docker tag "$image_sha" "$remote_sha"
  docker tag "$image_version" "$remote_version"
  docker tag "$image_staging" "$remote_staging"
  docker push "$remote_sha"
  docker push "$remote_version"
  docker push "$remote_staging"
  echo "PASS image push (digest not printed)"
else
  echo "SKIP image push (set PUSH_IMAGE=true and CONTAINER_REGISTRY to push)"
fi

echo "Container build complete."
