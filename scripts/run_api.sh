#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

: "${INGEST_TOKEN:?INGEST_TOKEN is required}"
: "${SEARCH_TOKEN:?SEARCH_TOKEN is required}"

python3 -m notes_sync.server --host 0.0.0.0 --port "${PORT:-8787}"
