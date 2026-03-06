# Security & Privacy

## Data Classification
Apple Notes may contain highly sensitive personal/work data.
Treat all indexed data as confidential.

## Required Controls

### Transport
- TLS required or private network (Tailscale)
- Reject plaintext external traffic

### Authentication
- Bearer token for ingest API
- Rotate token periodically
- IP/network allowlist where possible

### Data Minimization
- Index only required fields (`title`, `content_text`, minimal metadata)
- Avoid storing raw HTML unless needed
- Optional folder denylist (e.g., Private/Finance)

### Redaction
- Pre-index redaction rules for common secrets:
  - API keys (`sk-`, `ghp_`, etc.)
  - access tokens
  - password patterns

### Access Control
- Expose retrieval tool only to trusted sessions/channels
- Disable broad group access for retrieval tools if channel is untrusted

### Retention & Deletion
- Honor delete tombstones from Notes
- Support forced reindex and purge by `note_id` or folder

## Threats & Mitigations

1. **Token leakage**
   - Mitigation: env var + secret file perms + rotation
2. **Prompt-level data exfiltration**
   - Mitigation: tool access policy + minimal snippets in tool response
3. **Replay/duplicate ingest**
   - Mitigation: idempotency key (`note_id` + `hash`)
4. **Index poisoning**
   - Mitigation: strict schema + source validation + size limits

## Operational Safeguards
- Log only metadata, avoid logging full note bodies
- Add ingestion payload size cap
- Alert on unusual write volume spikes
