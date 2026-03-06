# Data Model

## Canonical Note Record

```json
{
  "source": "apple_notes",
  "note_id": "string",
  "title": "string",
  "content_text": "string",
  "content_html": "string|null",
  "folder": "string|null",
  "account": "string|null",
  "created_at": "ISO8601",
  "updated_at": "ISO8601",
  "hash": "sha256",
  "deleted": false,
  "meta": {
    "tags": ["string"],
    "language": "string|null"
  }
}
```

### Field Rules
- `note_id`: stable Apple Notes identifier (required)
- `hash`: sha256 of normalized content (`title + content_text + folder`)
- `deleted=true`: tombstone event (content may be empty)

---

## Producer Checkpoint DB (SQLite)

### `notes_state`
Tracks last indexed state.

```sql
CREATE TABLE notes_state (
  note_id TEXT PRIMARY KEY,
  updated_at TEXT NOT NULL,
  hash TEXT NOT NULL,
  last_seen_at TEXT NOT NULL
);
```

### `sync_state`
Stores sync cursor and metadata.

```sql
CREATE TABLE sync_state (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
```

### `outbox`
Reliable delivery queue.

```sql
CREATE TABLE outbox (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  payload_json TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  retry_count INTEGER NOT NULL DEFAULT 0,
  last_error TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

---

## QMD Document Shape (logical)

```json
{
  "doc_id": "apple_notes:<note_id>",
  "source": "apple_notes",
  "title": "...",
  "chunk": "...",
  "chunk_id": "...",
  "updated_at": "ISO8601",
  "folder": "...",
  "account": "...",
  "hash": "sha256"
}
```

`hash` must be indexed in metadata to detect stale chunks.
