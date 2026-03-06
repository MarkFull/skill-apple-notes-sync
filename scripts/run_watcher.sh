#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

: "${NOTES_INGEST_URL:?NOTES_INGEST_URL is required}"
: "${INGEST_TOKEN:?INGEST_TOKEN is required}"

# Make source tree importable without installing package metadata.
export PYTHONPATH="$PWD/src:${PYTHONPATH:-}"
export PYTHONUNBUFFERED="${PYTHONUNBUFFERED:-1}"

# Prefer project venv.
if [[ -f "$PWD/.venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source "$PWD/.venv/bin/activate"
fi

PY_BIN="python3"
if [[ -x "$PWD/.venv/bin/python" ]]; then
  PY_BIN="$PWD/.venv/bin/python"
fi

exec "$PY_BIN" -m notes_sync.watcher \
  --api-url "$NOTES_INGEST_URL" \
  --token "$INGEST_TOKEN" \
  --state-db "${STATE_DB:-$HOME/.notes-sync/state.db}" \
  --interval "${WATCH_INTERVAL:-10}" \
  "$@"
