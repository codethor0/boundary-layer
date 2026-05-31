#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CERT_DIR="${SCRIPT_DIR}/certs"
ARCHIVE_DIR="${CERT_DIR}/archive/$(date -u +%Y%m%dT%H%M%SZ)"
PROD_COMPOSE=(docker compose --env-file .env.production -f docker-compose.prod.yml -p boundary-layer-prod)

mkdir -p "${ARCHIVE_DIR}"

if [[ -f "${CERT_DIR}/boundary-layer.crt" ]]; then
  cp "${CERT_DIR}/boundary-layer.crt" "${ARCHIVE_DIR}/"
  cp "${CERT_DIR}/boundary-layer.key" "${ARCHIVE_DIR}/"
  echo "Archived existing certificate to ${ARCHIVE_DIR}"
fi

if [[ $# -eq 2 ]]; then
  install -m 0644 "$1" "${CERT_DIR}/boundary-layer.crt"
  install -m 0600 "$2" "${CERT_DIR}/boundary-layer.key"
  echo "Installed external certificate pair"
else
  bash "${SCRIPT_DIR}/generate-certs.sh"
fi

if "${PROD_COMPOSE[@]}" ps nginx -q 2>/dev/null | grep -q .; then
  "${PROD_COMPOSE[@]}" exec -T nginx nginx -s reload
  echo "Reloaded production nginx"
fi

echo "Certificate rotation complete"
