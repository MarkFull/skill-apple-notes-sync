from __future__ import annotations

from dataclasses import dataclass

from .models import NoteRecord


@dataclass
class Delta:
    upserts: list[NoteRecord]
    deleted_note_ids: list[str]


def compute_delta(current_notes: list[NoteRecord], last_state: dict[str, tuple[str, str]]) -> Delta:
    """
    last_state: note_id -> (updated_at_iso, hash)
    """
    upserts: list[NoteRecord] = []
    current_ids = set()

    for note in current_notes:
        current_ids.add(note.note_id)
        prev = last_state.get(note.note_id)
        cur_updated = note.updated_at.isoformat()

        if prev is None:
            upserts.append(note)
            continue

        prev_updated, prev_hash = prev
        if prev_updated != cur_updated or prev_hash != note.hash:
            upserts.append(note)

    deleted_note_ids = sorted(set(last_state.keys()) - current_ids)
    return Delta(upserts=upserts, deleted_note_ids=deleted_note_ids)
