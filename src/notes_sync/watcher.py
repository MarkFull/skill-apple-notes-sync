from __future__ import annotations

import argparse
import os
import time
import uuid
from datetime import timezone

import requests

from .apple_notes import fetch_notes_full, fetch_notes_meta
from .models import IngestBatchRequest, NoteRecord
from .state_db import commit, connect_db, delete_state, init_db, load_state_map, upsert_state
from .utils import compute_note_hash, utc_now


def build_tombstone(note_id: str) -> NoteRecord:
    now = utc_now()
    return NoteRecord(
        source="apple_notes",
        note_id=note_id,
        title="",
        content_text="",
        content_html=None,
        folder=None,
        account=None,
        created_at=now,
        updated_at=now,
        hash=compute_note_hash("", "", None),
        deleted=True,
    )


def post_batch(api_url: str, token: str, notes: list[NoteRecord], timeout: int = 30) -> dict:
    req = IngestBatchRequest(batch_id=str(uuid.uuid4()), sent_at=utc_now(), notes=notes)
    resp = requests.post(
        f"{api_url.rstrip('/')}/ingest/apple-notes/batch",
        headers={"Authorization": f"Bearer {token}"},
        json=req.model_dump(mode="json"),
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.json()


def run_once(api_url: str, token: str, conn, dry_run: bool = False) -> tuple[int, int]:
    """One incremental sync iteration.

    Perf model:
    - Always fetch **metadata** for all notes (fast).
    - Only fetch full bodies for notes whose updated_at changed (slow path).

    First run will still be heavy (all notes look new), but subsequent runs should be small.
    """

    # note_id -> (updated_at_iso, hash)
    last_state = load_state_map(conn)

    meta_rows = fetch_notes_meta()
    current_ids = {m.note_id for m in meta_rows}

    changed_ids: list[str] = []
    for m in meta_rows:
        prev = last_state.get(m.note_id)
        cur_updated = m.updated_at.astimezone(timezone.utc).isoformat()
        if prev is None:
            changed_ids.append(m.note_id)
            continue
        prev_updated, _prev_hash = prev
        if prev_updated != cur_updated:
            changed_ids.append(m.note_id)

    deleted_note_ids = sorted(set(last_state.keys()) - current_ids)

    max_upserts = int(os.getenv("MAX_UPSERTS_PER_RUN", "50"))
    batch_ids = changed_ids[: max(0, max_upserts)]

    upserts: list[NoteRecord] = []
    if batch_ids:
        # Only call note.body() for these IDs.
        wanted = set(batch_ids)
        upserts = fetch_notes_full(target_ids=wanted)

        # Preserve progress even if JXA couldn't fetch some ids.
        got_ids = {n.note_id for n in upserts}
        missing = sorted(wanted - got_ids)
        if missing:
            print(f"warn: missing {len(missing)} notes in full fetch")

    tombstones = [build_tombstone(nid) for nid in deleted_note_ids]
    outbound = upserts + tombstones

    if not outbound:
        return 0, 0

    if not dry_run:
        post_batch(api_url, token, outbound)

    seen_at = utc_now().isoformat()
    for n in upserts:
        upsert_state(conn, n.note_id, n.updated_at.astimezone(timezone.utc).isoformat(), n.hash, seen_at)
    for deleted_id in deleted_note_ids:
        delete_state(conn, deleted_id)
    commit(conn)

    return len(upserts), len(deleted_note_ids)


def main() -> None:
    p = argparse.ArgumentParser(description="Apple Notes near-realtime watcher")
    p.add_argument("--api-url", required=True, help="Ingestion API base URL")
    p.add_argument("--token", required=True, help="Ingestion bearer token")
    p.add_argument("--state-db", default="~/.notes-sync/state.db")
    p.add_argument("--interval", type=int, default=10)
    p.add_argument("--once", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    conn = connect_db(args.state_db)
    init_db(conn)

    if args.once:
        upserts, deleted = run_once(args.api_url, args.token, conn, dry_run=args.dry_run)
        print(f"done: upserts={upserts} deleted={deleted}")
        return

    print(f"watching Apple Notes every {args.interval}s")
    while True:
        try:
            upserts, deleted = run_once(args.api_url, args.token, conn, dry_run=args.dry_run)
            if upserts or deleted:
                print(f"sync: upserts={upserts} deleted={deleted}")
        except Exception as e:
            print(f"sync error: {e}")
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
