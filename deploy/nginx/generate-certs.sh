#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CERT_DIR="${SCRIPT_DIR}/certs"
mkdir -p "${CERT_DIR}"

openssl ecparam -name prime256v1 -genkey -noout -out "${CERT_DIR}/boundary-layer.key"
openssl req -x509 -nodes -days 825 -key "${CERT_DIR}/boundary-layer.key" \
  -out "${CERT_DIR}/boundary-layer.crt" \
  -subj "/CN=boundary-layer.local/O=BoundaryLayer/C=US"

echo "Generated ECDSA self-signed certificate in ${CERT_DIR}"
echo "For CA-backed production certs, use deploy/nginx/install-external-certs.sh"
