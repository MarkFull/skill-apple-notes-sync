# Architecture

## Components

### 1) Mac Notes Watcher (producer)
Runs continuously on macOS via LaunchAgent.

Responsibilities:
- Poll Apple Notes via `osascript`/JXA every 10s (configurable)
- Normalize note payloads
- Detect changes via `updated_at` + content hash
- Send delta batches to ingestion API
- Retry failed sends with backoff

### 2) Ingestion API (bridge)
Runs on OpenClaw host (Linux).

Responsibilities:
- AuthN/AuthZ for producer requests
- Validate schema and reject malformed payloads
- Upsert/delete in index pipeline queue
- Return per-item status for idempotent retries

### 3) QMD Indexer
Runs on OpenClaw host.

Responsibilities:
- Chunk note text
- Generate embeddings (QMD backend model)
- Upsert by stable `doc_id`
- Remove stale chunks when note hash changes

### 4) OpenClaw Retrieval Tool
Exposed as tool (MCP/custom endpoint): `notes_search`.

Responsibilities:
- semantic search with filters (folder/date/source)
- top-k ranking and concise snippets
- structured response for assistant grounding

---

## Data Flow

1. Watch loop triggers (every 10s)
2. Read note metadata + content from Apple Notes
3. Compare with local checkpoint DB
4. Build `changed_notes` + `deleted_notes`
5. POST batch to Ingestion API
6. Ingestion API writes/updates QMD index
7. OpenClaw query calls `notes_search`
8. Results feed answer generation

---

## Runtime Targets

- Poll interval: 10s default (adaptive 10–30s)
- End-to-end index latency target: <= 15s
- Retrieval p95 latency target: <= 500ms (small-to-medium corpora)

---

## Failure Strategy

- Producer-side outbox queue for at-least-once delivery
- API idempotency by (`source`, `note_id`, `hash`)
- Dead-letter record after max retry count
- Full reconciliation run once daily to correct drift
