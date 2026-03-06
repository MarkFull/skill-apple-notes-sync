# Design Graph

## System Architecture (Mermaid)

```mermaid
flowchart LR
  subgraph MAC["Mac (Producer)"]
    A[Apple Notes]
    B["Notes Watcher<br/>(osascript/JXA, 10s poll)"]
    C[("Checkpoint DB<br/>SQLite")]
    D[(Outbox Queue)]

    A --> B
    B <--> C
    B --> D
  end

  subgraph HOST["OpenClaw Host (Linux)"]
    E["Ingestion API<br/>/ingest/apple-notes/batch"]
    F[QMD Upsert Adapter]
    G[("QMD Index<br/>chunks + embeddings + metadata")]
    H["Retrieval API<br/>/search/apple-notes"]
    I["OpenClaw Tool<br/>notes_search"]
  end

  D -->|HTTPS + Bearer Token| E
  E --> F --> G
  H --> G
  I --> H

  J[User Query in OpenClaw] --> I
  I --> K[Grounded Answer]
```

## Compatibility Version (for older Mermaid parsers)

```mermaid
flowchart LR
  subgraph MAC
    A[Apple Notes]
    B[Notes Watcher]
    C[Checkpoint DB]
    D[Outbox Queue]
    A --> B
    B --> C
    C --> B
    B --> D
  end

  subgraph HOST
    E[Ingestion API]
    F[QMD Upsert Adapter]
    G[QMD Index]
    H[Retrieval API]
    I[OpenClaw Tool notes_search]
    E --> F
    F --> G
    H --> G
    I --> H
  end

  D --> E
  J[User Query in OpenClaw] --> I
  I --> K[Grounded Answer]
```

## Sync + Query Sequence (Mermaid)

```mermaid
sequenceDiagram
  participant N as Apple Notes
  participant W as Mac Watcher
  participant S as Checkpoint SQLite
  participant API as Ingestion API
  participant Q as QMD
  participant OC as OpenClaw

  loop every 10s
    W->>N: Read notes (id/title/content/updated_at)
    W->>S: Compare hash + updated_at
    S-->>W: changed/new/deleted set
    W->>API: POST /ingest/apple-notes/batch
    API->>Q: upsert/delete chunks by doc_id
    Q-->>API: status
    API-->>W: per-item result
    W->>S: update checkpoint
  end

  OC->>API: POST /search/apple-notes (query, filters)
  API->>Q: semantic retrieval + metadata filter
  Q-->>API: top-k snippets
  API-->>OC: ranked results
```

## Data Entities

```mermaid
erDiagram
  NOTE_RECORD {
    string source
    string note_id
    string title
    string content_text
    string folder
    string account
    string created_at
    string updated_at
    string hash
    boolean deleted
  }

  NOTES_STATE {
    string note_id PK
    string updated_at
    string hash
    string last_seen_at
  }

  OUTBOX {
    int id PK
    string payload_json
    string status
    int retry_count
    string last_error
    string created_at
    string updated_at
  }

  NOTE_RECORD ||--|| NOTES_STATE : tracks
  NOTE_RECORD ||--o{ OUTBOX : emits_delta
```

## Rendered SVG Assets

- `docs/graphs/architecture.svg`
- `docs/graphs/sequence.svg`
- `docs/graphs/entities.svg`
