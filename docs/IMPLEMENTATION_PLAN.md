# Implementation Plan

## Phase 0 — Setup & Validation (0.5 day)
- [x] Validate Apple Notes automation access (`osascript`)
- [x] Validate target host has `qmd`
- [ ] Create project scaffolding and docs
- [ ] Define ingest token + network policy

## Phase 1 — MVP Pipeline (1–2 days)

### 1. Mac Watcher (polling)
- [ ] Implement extractor command wrapper (JXA/AppleScript)
- [ ] Build normalizer to canonical schema
- [ ] Add hash-based change detection
- [ ] Store state in SQLite (`notes_state`, `sync_state`)

### 2. Ingestion API
- [ ] Implement `/ingest/apple-notes/batch`
- [ ] Add token auth + schema validation
- [ ] Return per-item status for idempotent retry

### 3. QMD Upsert
- [ ] Chunk + embed + upsert by `doc_id`
- [ ] Remove stale chunks on hash change
- [ ] Tombstone handling (`deleted=true`)

### 4. Retrieval
- [ ] Implement `/search/apple-notes`
- [ ] Add metadata filters
- [ ] Add OpenClaw `notes_search` tool mapping

### Exit Criteria (MVP)
- [ ] Full bootstrap of all notes succeeds
- [ ] Edit in Notes appears in search <= 15s
- [ ] No duplicate chunks after repeated updates

---

## Phase 2 — Reliability (1 day)
- [ ] Outbox queue + retry backoff
- [ ] Daily reconcile (full scan to heal drift)
- [ ] Structured logs + metrics (latency, failures)
- [ ] Dead-letter handling for poison payloads

## Phase 3 — Quality & UX (1 day)
- [ ] Ranking blend (semantic + recency)
- [ ] Better snippets + source metadata in tool output
- [ ] Folder allowlist/blocklist config
- [ ] Optional attachment placeholder support

---

## Test Plan

### Unit
- [ ] hash/normalization determinism
- [ ] checkpoint diff logic
- [ ] API schema validation

### Integration
- [ ] end-to-end ingest batch -> searchable results
- [ ] delete/tombstone propagation
- [ ] retry idempotency

### Manual acceptance
- [ ] Create note, edit note, delete note
- [ ] Query matches expected content in OpenClaw
- [ ] Verify latency target in normal load
