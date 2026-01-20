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

if [[ -z "${ROUNDHOUSE_BACKEND_HOST:-}" ]]; then
  echo "ROUNDHOUSE_BACKEND_HOST not set"
  exit 1
fi

if [[ -z "${ROUNDHOUSE_BACKEND_PORT:-}" ]]; then
  echo "ROUNDHOUSE_BACKEND_PORT not set"
  exit 1
fi

cd "$SCRIPT_DIR"

export PYTHONPATH="${ROOT_DIR}:${PYTHONPATH:-}"

exec python -m uvicorn main:app \
  --host "$ROUNDHOUSE_BACKEND_HOST" \
  --port "$ROUNDHOUSE_BACKEND_PORT"
