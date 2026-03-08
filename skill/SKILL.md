---
name: apple-notes-sync
description: Bootstrap and operate an Apple Notes incremental sync stack (gateway + ingest API + macOS watcher). Use when asked to set up, package, troubleshoot, share, or directly query Apple Notes in OpenClaw (`notes_search`) for users, including requests mentioning Codex, reusable setup skills, LaunchAgent watcher setup, or end-to-end validation.
---

# Apple Notes Sync

Set up one reusable workflow that works for both:
- tool-enabled automation (can run on host + paired Mac)
- Codex-style terminal guidance (user runs commands locally)

## Workflow

### 1) Gather minimum required inputs
Collect only what is required:
- Host API URL (example: `http://<host>:8787`)
- `INGEST_TOKEN` (and optional `SEARCH_TOKEN`)
- macOS project path where watcher scripts live
- Reachable path Mac → host (LAN/Tailscale/public)

If missing, proceed with defaults and mark TODO placeholders clearly.

### 2) Prepare host side (gateway + ingest API)
1. Ensure gateway is healthy (status/health check)
2. In project repo, run API with env vars:
   - `INGEST_TOKEN`
   - `SEARCH_TOKEN`
   - optional `NOTES_DATA_DIR`, `QMD_COLLECTION`
3. Verify:
   - `GET /health` returns `ok: true`

Use `references/commands.md` for copy-paste command blocks.

### 3) Install macOS watcher
Prefer one-command installer:
- `./scripts/setup_mac_watcher.sh --api-url <host> --token <INGEST_TOKEN> --interval 10`

Then validate LaunchAgent:
- `./scripts/watcherctl.sh status`
- `./scripts/watcherctl.sh logs`

If installer is unavailable, install manually with `install_launchagent.sh` + `run_watcher.sh`.

### 4) Validate end-to-end
Validate both paths:
1. Mac watcher process is running (LaunchAgent state + logs)
2. Host search endpoint returns note results using `SEARCH_TOKEN`

If first sync is slow, treat as expected for initial scan and validate incremental updates on later runs.

### 5) OpenClaw direct notes search (no manual curl)
For user requests like “search my notes / note_search / notes_search”, call:
- `./scripts/notes_search.sh --query '<text>' --top-k 5 --pretty`

Behavior of this helper:
- Tries `/tool/notes_search` first, then falls back to `/search/apple-notes`
- Uses `NOTES_SEARCH_TOKEN` / `SEARCH_TOKEN` automatically
- If env token is missing, attempts to read token from running `notes_sync.server` process env on host

### 6) Package for reuse
When user asks for distribution:
- Keep one skill containing host + Mac setup
- Include one-command installer + service controls + concise troubleshooting
- Keep real secrets out of files; always use placeholders

## Tool-execution vs terminal-guidance mode

- If tools can execute on host/Mac directly, perform actions and return status.
- If running in plain Codex without remote execution, provide exact command sequence and diagnose from outputs.

## Security and reliability rules

- Never publish real tokens in docs, commits, screenshots, or logs.
- Use per-user/per-host tokens; avoid one global shared token.
- Prefer idempotent scripts (safe to rerun).
- For failures, retry once with adjusted parameters before escalating.

## Quick troubleshooting checklist

1. `ModuleNotFoundError` on Mac watcher
   - Ensure venv exists and watcher starts via project venv
2. `401 unauthorized` from ingest API
   - Verify `INGEST_TOKEN` matches host env
3. Mac cannot reach host
   - Test URL from Mac (`curl /health`)
4. Watcher "running" but no updates
   - Check watcher logs, then verify search endpoint for changed notes

For exact command snippets and validation calls, read `references/commands.md`.
