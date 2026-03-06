# Commands (host + macOS)

## Host: gateway + API

Run your gateway status/start commands for your environment, then run the ingest API:

```bash
cd <project-dir>
export INGEST_TOKEN='replace-me'
export SEARCH_TOKEN='replace-me-search'
export NOTES_DATA_DIR='./data/notes'
export QMD_COLLECTION='apple_notes'
./scripts/run_api.sh
```

Health check:

```bash
curl -sS 'http://127.0.0.1:8787/health'
```

## macOS: watcher install

Recommended one-command setup:

```bash
cd <project-dir>
./scripts/setup_mac_watcher.sh \
  --api-url 'http://<host>:8787' \
  --token '<INGEST_TOKEN>' \
  --interval 10
```

Service control:

```bash
./scripts/watcherctl.sh status
./scripts/watcherctl.sh logs
./scripts/watcherctl.sh restart
./scripts/watcherctl.sh uninstall
```

## End-to-end query check (host)

```bash
curl -sS -X POST 'http://127.0.0.1:8787/search/apple-notes' \
  -H 'Authorization: Bearer <SEARCH_TOKEN>' \
  -H 'Content-Type: application/json' \
  -d '{"query":"meeting notes","top_k":3}'
```

## Common fixes

### 401 unauthorized
- Re-check `INGEST_TOKEN` on host and installer command token on Mac.

### Python/version issues on Mac
- Re-run installer; it re-creates `.venv` with Python >= 3.10 if available.

### Mac cannot reach host URL
- Verify network path (LAN/Tailscale/public) and test:

```bash
curl -sS 'http://<host>:8787/health'
```
