# Apple Notes → QMD → OpenClaw (Near-Real-Time)

## Goal
Build a near-real-time indexing pipeline from Apple Notes into QMD, then expose retrieval to OpenClaw.

- No manual export workflow
- Incremental sync (changed notes only)
- Practical real-time UX (target: 5–15s indexing latency)

## Environment Checklist
- macOS can read Apple Notes via `osascript`
- host machine has `qmd` available in PATH
- host API endpoint is reachable from macOS (LAN/Tailscale/public)
- `INGEST_TOKEN` / `SEARCH_TOKEN` are configured before startup

## Architecture (high level)
1. **Mac Watcher** reads Apple Notes changes continuously
2. **Ingestion API** receives normalized note batches
3. **QMD Indexer** upserts markdown mirror into a QMD collection
4. **OpenClaw Tool** (`notes_search`) queries QMD and returns ranked snippets

See `docs/ARCHITECTURE.md` for details.

---

## Project Docs Index
- `docs/ARCHITECTURE.md` — components, data flow, runtime model
- `docs/DESIGN_GRAPH.md` — Mermaid architecture/sequence/entity graphs
- `docs/graphs/*.svg` — rendered SVG diagrams
- `docs/DATA_MODEL.md` — canonical schema + checkpoint schema
- `docs/INGEST_API.md` — ingestion/retrieval API contract
- `docs/IMPLEMENTATION_PLAN.md` — phased plan and milestones
- `docs/SECURITY_PRIVACY.md` — threat model + controls
- `docs/OPERATIONS.md` — runbook, health checks, troubleshooting
- `docs/INSTALL_FOR_OPENCLAW_USERS.md` — copy-paste installer guide for other OpenClaw users

---

## Code Layout

```text
src/notes_sync/
  api.py            # FastAPI ingest/search bridge
  server.py         # uvicorn launcher
  qmd_index.py      # qmd collection/index/search adapter
  watcher.py        # macOS poller + delta sync loop
  apple_notes.py    # osascript/JXA extractor
  state_db.py       # watcher checkpoint sqlite
  diff.py           # changed/deleted detection
  models.py         # shared request/response schemas
  utils.py          # hash + filename helpers
```

---

## Quick Start

### 1) Install dependencies

```bash
cd <project-dir>
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

### 2) Run API on OpenClaw host (Linux)

```bash
export INGEST_TOKEN='change-me'
export SEARCH_TOKEN='change-me-search'
export NOTES_DATA_DIR='./data/notes'
export QMD_COLLECTION='apple_notes'

./scripts/run_api.sh
```

API defaults to `http://0.0.0.0:8787`.

### 3) Run watcher on Mac (one-shot test)

```bash
cd <project-dir>
source .venv/bin/activate
python3 -m notes_sync.watcher \
  --api-url 'http://<linux-host>:8787' \
  --token 'change-me' \
  --once
```

### 4) Run watcher continuously on Mac (recommended)

```bash
cd <project-dir>
./scripts/setup_mac_watcher.sh \
  --api-url 'http://<linux-host>:8787' \
  --token 'change-me' \
  --interval 10
```

The installer will:
- pick Python >= 3.10
- create/update `.venv`
- install project dependencies
- install + start LaunchAgent

### 5) Manage watcher service

```bash
./scripts/watcherctl.sh status
./scripts/watcherctl.sh logs
./scripts/watcherctl.sh restart
./scripts/watcherctl.sh uninstall
```

---

## Search API Example

```bash
curl -sS -X POST 'http://127.0.0.1:8787/search/apple-notes' \
  -H 'Authorization: Bearer <SEARCH_TOKEN>' \
  -H 'Content-Type: application/json' \
  -d '{"query":"qmd indexing plan","top_k":5,"mode":"search"}'
```

### OpenClaw-friendly alias (`notes_search` mental model)

```bash
curl -sS -X POST 'http://127.0.0.1:8787/tool/notes_search' \
  -H 'Authorization: Bearer change-me-search' \
  -H 'Content-Type: application/json' \
  -d '{"query":"这周会议纪要","top_k":5,"mode":"search"}'
```

### OpenClaw direct call helper (no manual curl)

```bash
./scripts/notes_search.sh --query '这周会议纪要' --top-k 5 --pretty
```

Helper behavior:
- auto-detects token from `NOTES_SEARCH_TOKEN` / `SEARCH_TOKEN`
- if env token is missing, tries reading token from running `notes_sync.server` process env
- tries `/tool/notes_search` first, then falls back to `/search/apple-notes`

> `mode="search"` is default and fast. `mode="query"` may trigger heavier model downloads in QMD.

---

## Tests

```bash
pytest -q
```

---


## Included skill

This repository also includes the reusable agent skill package:

- source: `skill/SKILL.md` + `skill/references/commands.md`
- packaged: `skill/dist/apple-notes-sync.skill`

## Notes
- Apple Notes has no official webhook API; this project uses near-realtime polling (default 10s).
- This implementation mirrors notes into local markdown files on host side, then indexes with QMD.
- Delete events are handled via tombstones and mirrored file deletion.

## Sharing with other OpenClaw users

Yes — this repo is designed to be reusable by other OpenClaw users in a self-hosted setup:

- each user runs their own Mac watcher locally
- watcher pushes to their own OpenClaw host ingest API
- tokens are per-user (`INGEST_TOKEN`, `SEARCH_TOKEN`)

For production sharing, provide this repo + the one-command mac installer:

```bash
./scripts/setup_mac_watcher.sh --api-url 'http://<host>:8787' --token '<INGEST_TOKEN>'
```

## Next Step (Optional)
Expose this helper behind an MCP/custom tool so `notes_search` appears as a first-class callable tool in your OpenClaw runtime.
