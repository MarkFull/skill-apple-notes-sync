# Ingest & Retrieval API Contract

## Auth
- `Authorization: Bearer <INGEST_TOKEN>`
- TLS required (or private network/Tailscale only)

---

## 1) Batch Ingest

`POST /ingest/apple-notes/batch`

### Request
```json
{
  "batch_id": "uuid",
  "sent_at": "ISO8601",
  "notes": [
    {
      "source": "apple_notes",
      "note_id": "n_123",
      "title": "Sample note",
      "content_text": "...",
      "content_html": null,
      "folder": "Ideas",
      "account": "iCloud",
      "created_at": "2026-03-05T00:00:00Z",
      "updated_at": "2026-03-05T10:00:00Z",
      "hash": "sha256...",
      "deleted": false,
      "meta": {"tags": []}
    }
  ]
}
```

### Response
```json
{
  "ok": true,
  "batch_id": "uuid",
  "accepted": 10,
  "rejected": 0,
  "items": [
    {"note_id": "n_123", "status": "upserted"}
  ]
}
```

### Status values
- `upserted`
- `deleted`
- `unchanged`
- `rejected` (with error)

---

## 2) Search

Primary endpoint:
- `POST /search/apple-notes`

OpenClaw tool alias (same request/response/auth):
- `POST /tool/notes_search`

CLI helper for OpenClaw automation (no manual curl):
- `./scripts/notes_search.sh --query '<text>' --top-k 5 --pretty`

### Request
```json
{
  "query": "what did i write about qmd",
  "top_k": 8,
  "filters": {
    "folder": ["Ideas"],
    "from_date": "2026-01-01",
    "to_date": "2026-12-31"
  }
}
```

### Response
```json
{
  "ok": true,
  "results": [
    {
      "score": 0.84,
      "note_id": "n_123",
      "title": "Sample note",
      "snippet": "...",
      "folder": "Ideas",
      "updated_at": "2026-03-05T10:00:00Z"
    }
  ]
}
```

---

## 3) Health

`GET /health`

```json
{
  "ok": true,
  "index_ready": true,
  "qmd": "up"
}
```

---

## OpenClaw Tool Mapping

Tool name suggestion: `notes_search`

Input:
```json
{
  "query": "string",
  "topK": 8,
  "folder": "optional string",
  "fromDate": "optional YYYY-MM-DD",
  "toDate": "optional YYYY-MM-DD"
}
```

Output:
- normalized list of ranked note snippets (no raw full-note dump by default)
