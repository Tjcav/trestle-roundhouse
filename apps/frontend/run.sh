#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
ENV_FILE="${ROOT_DIR}/.env"

if [[ -f "$ENV_FILE" ]]; then
  set -a
  source "$ENV_FILE"
  set +a
fi

if [[ -z "${VITE_FRONTEND_PORT:-}" ]]; then
  echo "VITE_FRONTEND_PORT not set"
  exit 1
fi

if [[ -z "${VITE_BACKEND_URL:-}" ]]; then
  echo "VITE_BACKEND_URL not set"
  exit 1
fi

cd "$SCRIPT_DIR"

exec npm run start
