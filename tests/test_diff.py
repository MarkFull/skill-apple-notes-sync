from datetime import datetime, timezone

from notes_sync.diff import compute_delta
from notes_sync.models import NoteRecord
from notes_sync.utils import compute_note_hash


def mk_note(note_id: str, title: str, content: str, updated: str) -> NoteRecord:
    updated_dt = datetime.fromisoformat(updated.replace("Z", "+00:00"))
    return NoteRecord(
        source="apple_notes",
        note_id=note_id,
        title=title,
        content_text=content,
        content_html=None,
        folder="Ideas",
        account="iCloud",
        created_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
        updated_at=updated_dt,
        hash=compute_note_hash(title, content, "Ideas"),
        deleted=False,
    )


def test_compute_delta_new_changed_deleted():
    n1_old = mk_note("n1", "A", "old", "2026-03-05T00:00:00Z")
    n1_new = mk_note("n1", "A", "new", "2026-03-05T01:00:00Z")
    n2 = mk_note("n2", "B", "x", "2026-03-05T01:00:00Z")

    state = {
        "n1": (n1_old.updated_at.isoformat(), n1_old.hash),
        "n3": ("2026-03-05T01:00:00+00:00", "abc"),
    }

    d = compute_delta([n1_new, n2], state)

    assert sorted([x.note_id for x in d.upserts]) == ["n1", "n2"]
    assert d.deleted_note_ids == ["n3"]
