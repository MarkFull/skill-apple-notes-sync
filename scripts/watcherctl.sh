#!/usr/bin/env bash
set -euo pipefail

LABEL="com.openclaw.apple-notes-sync"
PLIST_PATH="$HOME/Library/LaunchAgents/${LABEL}.plist"
LOG_OUT="$HOME/Library/Logs/apple-notes-sync.log"
LOG_ERR="$HOME/Library/Logs/apple-notes-sync.err.log"
DOMAIN="gui/$(id -u)"
TARGET="${DOMAIN}/${LABEL}"

cmd="${1:-status}"

case "$cmd" in
  status)
    launchctl print "$TARGET" | egrep 'state =|runs =|pid =|last exit code' || true
    ;;
  start)
    launchctl bootstrap "$DOMAIN" "$PLIST_PATH" >/dev/null 2>&1 || true
    launchctl kickstart -k "$TARGET"
    ;;
  stop)
    launchctl bootout "$DOMAIN" "$PLIST_PATH" >/dev/null 2>&1 || launchctl bootout "$TARGET" >/dev/null 2>&1 || true
    ;;
  restart)
    "$0" stop || true
    "$0" start
    ;;
  logs)
    tail -n 120 "$LOG_OUT" "$LOG_ERR" 2>/dev/null || true
    ;;
  install)
    ./scripts/install_launchagent.sh
    ;;
  uninstall)
    "$0" stop || true
    rm -f "$PLIST_PATH"
    echo "Removed $PLIST_PATH"
    ;;
  *)
    echo "Usage: $(basename "$0") {status|start|stop|restart|logs|install|uninstall}"
    exit 1
    ;;
esac
