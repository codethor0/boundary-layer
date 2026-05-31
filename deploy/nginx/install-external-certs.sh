#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "Usage: $0 /path/to/fullchain.pem /path/to/privkey.pem" >&2
  exit 1
fi

FULLCHAIN="$1"
PRIVKEY="$2"

if [[ ! -f "${FULLCHAIN}" || ! -f "${PRIVKEY}" ]]; then
  echo "Both certificate files must exist" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bash "${SCRIPT_DIR}/rotate-certs.sh" "${FULLCHAIN}" "${PRIVKEY}"
