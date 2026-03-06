# Install for Other OpenClaw Users (Copy-Paste Guide)

This guide installs the **macOS watcher** (Apple Notes → ingest API) for a user running their own OpenClaw host.

## 0) Prerequisites

- macOS machine with Apple Notes data
- OpenClaw host already running the ingest API (`scripts/run_api.sh`)
- Reachable API URL from Mac (LAN/Tailscale/public)
- Ingest token from host env: `INGEST_TOKEN`

---

## 1) On host: run API

```bash
cd apple-notes-qmd-openclaw
export INGEST_TOKEN='replace-me'
export SEARCH_TOKEN='replace-me-search'
./scripts/run_api.sh
```

Default API endpoint: `http://<host>:8787`

---

## 2) On Mac: clone project

```bash
git clone <your-repo-url>
cd apple-notes-qmd-openclaw
```

---

## 3) One-command install (recommended)

```bash
./scripts/setup_mac_watcher.sh \
  --api-url 'http://<host>:8787' \
  --token '<INGEST_TOKEN>' \
  --interval 10
```

What this does:
- selects Python >= 3.10
- creates `.venv`
- installs project deps
- installs and starts LaunchAgent `com.openclaw.apple-notes-sync`

---

## 4) Service operations

```bash
./scripts/watcherctl.sh status
./scripts/watcherctl.sh logs
./scripts/watcherctl.sh restart
./scripts/watcherctl.sh uninstall
```

---

## 5) Verify indexing from host

```bash
curl -sS -X POST 'http://127.0.0.1:8787/search/apple-notes' \
  -H 'Authorization: Bearer <SEARCH_TOKEN>' \
  -H 'Content-Type: application/json' \
  -d '{"query":"meeting notes","top_k":3}'
```

---

## FAQ

### Q1. Why is first sync slow?
Apple Notes has no official webhook API; first scan may be heavy. Subsequent runs are incremental.

### Q2. macOS asks for automation permission
Allow automation access for Apple Events (Notes). Then restart watcher:

```bash
./scripts/watcherctl.sh restart
```

### Q3. "Module not found" / wrong Python
Run installer again (it recreates env with Python >= 3.10):

```bash
./scripts/setup_mac_watcher.sh --api-url 'http://<host>:8787' --token '<INGEST_TOKEN>'
```

### Q4. Which token should I share?
Only share each user’s own ingest token for their own host. Do not reuse one global token across users.
