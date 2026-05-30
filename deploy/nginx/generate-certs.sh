#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CERT_DIR="${SCRIPT_DIR}/certs"
mkdir -p "${CERT_DIR}"

openssl req -x509 -nodes -days 825 -newkey rsa:2048 \
  -keyout "${CERT_DIR}/boundary-layer.key" \
  -out "${CERT_DIR}/boundary-layer.crt" \
  -subj "/CN=boundary-layer.local/O=BoundaryLayer/C=US"

echo "Generated self-signed certificate in ${CERT_DIR}"
