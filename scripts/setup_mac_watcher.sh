#!/usr/bin/env bash
set -euo pipefail

if [[ "$(uname)" != "Darwin" ]]; then
  echo "This installer is for macOS only"
  exit 1
fi

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
API_URL="${NOTES_INGEST_URL:-}"
TOKEN="${INGEST_TOKEN:-}"
INTERVAL="${WATCH_INTERVAL:-10}"
STATE_DB="${STATE_DB:-$HOME/.notes-sync/state.db}"

usage() {
  cat <<EOF
Usage:
  $(basename "$0") --api-url <http://host:8787> --token <INGEST_TOKEN> [--interval 10] [--state-db <path>]

Examples:
  $(basename "$0") --api-url http://<host>:8787 --token abc123
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --api-url)
      API_URL="${2:-}"
      shift 2
      ;;
    --token)
      TOKEN="${2:-}"
      shift 2
      ;;
    --interval)
      INTERVAL="${2:-}"
      shift 2
      ;;
    --state-db)
      STATE_DB="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1"
      usage
      exit 1
      ;;
  esac
done

if [[ -z "$API_URL" || -z "$TOKEN" ]]; then
  usage
  exit 1
fi

pick_python() {
  local candidates=()
  [[ -n "${PYTHON_BIN:-}" ]] && candidates+=("$PYTHON_BIN")
  candidates+=("python3" "/opt/homebrew/bin/python3" "/usr/local/bin/python3")

  local py
  for py in "${candidates[@]}"; do
    if ! command -v "$py" >/dev/null 2>&1; then
      continue
    fi
    if "$py" - <<'PY' >/dev/null 2>&1
import sys
raise SystemExit(0 if sys.version_info >= (3, 10) else 1)
PY
    then
      command -v "$py"
      return 0
    fi
  done
  return 1
}

PYTHON_PATH="$(pick_python || true)"
if [[ -z "$PYTHON_PATH" ]]; then
  echo "ERROR: Python >= 3.10 not found. Install Homebrew python first: brew install python"
  exit 1
fi

echo "Using Python: $PYTHON_PATH"
cd "$PROJECT_DIR"

"$PYTHON_PATH" -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e .

echo "Venv ready: $PROJECT_DIR/.venv"

echo "Installing launch agent..."
NOTES_SYNC_PROJECT_DIR="$PROJECT_DIR" \
NOTES_INGEST_URL="$API_URL" \
INGEST_TOKEN="$TOKEN" \
WATCH_INTERVAL="$INTERVAL" \
STATE_DB="$STATE_DB" \
./scripts/install_launchagent.sh

echo
echo "Done. Helpful commands:"
echo "  ./scripts/watcherctl.sh status"
echo "  ./scripts/watcherctl.sh logs"
