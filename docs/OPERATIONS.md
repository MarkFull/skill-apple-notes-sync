# Operations Runbook

## Health Checks

### Producer (Mac watcher)
- process alive
- last poll timestamp < 30s
- outbox pending not growing unbounded

### Ingestion API
- `/health` returns `ok=true`
- auth rejection behavior verified
- ingest p95 latency within target

### QMD
- index writable
- search endpoint responsive
- metadata filters functioning

## Daily Checks
- changed note count trend
- failed ingests / retry count
- average index latency
- retrieval p95 latency

## Reconciliation Job
Run once daily:
1. full note scan on producer
2. compare `note_id/hash` against index metadata
3. fix drift by upsert/delete

## Recovery Playbooks

### A) Producer offline
- restart LaunchAgent
- replay outbox

### B) Ingestion auth failures
- verify token sync
- rotate token if compromised

### C) QMD index corruption/drift
- clear affected source namespace
- full bootstrap reindex

## Suggested SLOs
- Ingest success rate: >= 99.5%
- End-to-end sync latency: <= 15s p95
- Search latency: <= 500ms p95
