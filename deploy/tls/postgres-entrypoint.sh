#!/bin/sh
set -eu

TLS_INPUT="${TLS_INPUT:-/etc/postgresql/tls-input}"
TLS_DIR="/var/lib/postgresql/tls"

mkdir -p "${TLS_DIR}"
cp "${TLS_INPUT}/postgres-server.crt" "${TLS_DIR}/postgres-server.crt"
cp "${TLS_INPUT}/postgres-server.key" "${TLS_DIR}/postgres-server.key"
chmod 600 "${TLS_DIR}/postgres-server.key"
chmod 644 "${TLS_DIR}/postgres-server.crt"
chown -R postgres:postgres "${TLS_DIR}"

exec /usr/local/bin/docker-entrypoint.sh postgres \
  -c ssl=on \
  -c ssl_cert_file="${TLS_DIR}/postgres-server.crt" \
  -c ssl_key_file="${TLS_DIR}/postgres-server.key"
