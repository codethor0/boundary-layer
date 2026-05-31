#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TLS_DIR="${SCRIPT_DIR}/internal"
mkdir -p "${TLS_DIR}"

if [[ -f "${TLS_DIR}/ca.crt" && -f "${TLS_DIR}/postgres-server.crt" && -f "${TLS_DIR}/redis-server.crt" ]]; then
  echo "Internal TLS material already exists in ${TLS_DIR}"
  # Redis runs as non-root in the container and must read mounted key material.
  chmod 0644 "${TLS_DIR}/ca.crt" "${TLS_DIR}/postgres-server.crt" \
    "${TLS_DIR}/postgres-server.key" "${TLS_DIR}/redis-server.crt" \
    "${TLS_DIR}/redis-server.key" 2>/dev/null || true
  exit 0
fi

WORK_DIR="$(mktemp -d)"
trap 'rm -rf "${WORK_DIR}"' EXIT

openssl genrsa -out "${WORK_DIR}/ca.key" 4096
openssl req -x509 -new -nodes -key "${WORK_DIR}/ca.key" -sha256 -days 825 \
  -out "${WORK_DIR}/ca.crt" \
  -subj "/CN=BoundaryLayer Internal CA/O=BoundaryLayer/C=US"

issue_server_cert() {
  local name="$1"
  local dns_name="$2"
  openssl genrsa -out "${WORK_DIR}/${name}.key" 2048
  openssl req -new -key "${WORK_DIR}/${name}.key" \
    -out "${WORK_DIR}/${name}.csr" \
    -subj "/CN=${dns_name}/O=BoundaryLayer/C=US"
  printf 'subjectAltName=DNS:%s\nextendedKeyUsage=serverAuth\n' "${dns_name}" \
    > "${WORK_DIR}/${name}.ext"
  openssl x509 -req -in "${WORK_DIR}/${name}.csr" \
    -CA "${WORK_DIR}/ca.crt" -CAkey "${WORK_DIR}/ca.key" -CAcreateserial \
    -out "${WORK_DIR}/${name}.crt" -days 825 -sha256 \
    -extfile "${WORK_DIR}/${name}.ext"
}

issue_server_cert "postgres-server" "postgres"
issue_server_cert "redis-server" "redis"

install -m 0644 "${WORK_DIR}/ca.crt" "${TLS_DIR}/ca.crt"
install -m 0600 "${WORK_DIR}/ca.key" "${TLS_DIR}/ca.key"
install -m 0644 "${WORK_DIR}/postgres-server.crt" "${TLS_DIR}/postgres-server.crt"
install -m 0644 "${WORK_DIR}/postgres-server.key" "${TLS_DIR}/postgres-server.key"
install -m 0644 "${WORK_DIR}/redis-server.crt" "${TLS_DIR}/redis-server.crt"
install -m 0644 "${WORK_DIR}/redis-server.key" "${TLS_DIR}/redis-server.key"

echo "Generated internal TLS material in ${TLS_DIR}"
