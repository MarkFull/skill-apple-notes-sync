#!/usr/bin/env bash
set -euo pipefail

if [[ "$(uname)" != "Darwin" ]]; then
  echo "This script is for macOS only"
  exit 1
fi

: "${NOTES_SYNC_PROJECT_DIR:?Set NOTES_SYNC_PROJECT_DIR to this project path on Mac}"
: "${NOTES_INGEST_URL:?Set NOTES_INGEST_URL}"
: "${INGEST_TOKEN:?Set INGEST_TOKEN}"

WATCH_INTERVAL="${WATCH_INTERVAL:-10}"
STATE_DB="${STATE_DB:-$HOME/.notes-sync/state.db}"
LABEL="com.openclaw.apple-notes-sync"
PLIST_DIR="$HOME/Library/LaunchAgents"
PLIST_PATH="$PLIST_DIR/${LABEL}.plist"
LOG_OUT="$HOME/Library/Logs/apple-notes-sync.log"
LOG_ERR="$HOME/Library/Logs/apple-notes-sync.err.log"

mkdir -p "$PLIST_DIR" "$(dirname "$LOG_OUT")"

_escape_squotes() {
  printf "%s" "$1" | sed "s/'/'\\''/g"
}

PROJECT_ESC="$(_escape_squotes "$NOTES_SYNC_PROJECT_DIR")"
URL_ESC="$(_escape_squotes "$NOTES_INGEST_URL")"
TOKEN_ESC="$(_escape_squotes "$INGEST_TOKEN")"
STATE_DB_ESC="$(_escape_squotes "$STATE_DB")"
INTERVAL_ESC="$(_escape_squotes "$WATCH_INTERVAL")"

CMD="cd '${PROJECT_ESC}' && NOTES_INGEST_URL='${URL_ESC}' INGEST_TOKEN='${TOKEN_ESC}' STATE_DB='${STATE_DB_ESC}' WATCH_INTERVAL='${INTERVAL_ESC}' PYTHONUNBUFFERED=1 ./scripts/run_watcher.sh"

cat >"$PLIST_PATH" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>${LABEL}</string>

  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>-lc</string>
    <string>${CMD}</string>
  </array>

  <key>RunAtLoad</key>
  <true/>

  <key>KeepAlive</key>
  <true/>

  <key>StandardOutPath</key>
  <string>${LOG_OUT}</string>

  <key>StandardErrorPath</key>
  <string>${LOG_ERR}</string>
</dict>
</plist>
EOF

# Reload agent
launchctl bootout "gui/$(id -u)" "$PLIST_PATH" >/dev/null 2>&1 || true
launchctl bootstrap "gui/$(id -u)" "$PLIST_PATH"
launchctl kickstart -k "gui/$(id -u)/${LABEL}" >/dev/null 2>&1 || true

echo "Installed and started: $PLIST_PATH"
echo "Status: launchctl print gui/$(id -u)/${LABEL}"
echo "Logs: $LOG_OUT"
