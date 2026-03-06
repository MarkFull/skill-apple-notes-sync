from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone


SAFE_RE = re.compile(r"[^a-zA-Z0-9._-]+")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def normalize_text(s: str) -> str:
    return "\n".join(line.rstrip() for line in (s or "").replace("\r\n", "\n").split("\n")).strip()


def compute_note_hash(title: str, content_text: str, folder: str | None) -> str:
    payload = "\n---\n".join([
        normalize_text(title),
        normalize_text(content_text),
        normalize_text(folder or ""),
    ])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def safe_filename(note_id: str) -> str:
    cleaned = SAFE_RE.sub("_", note_id).strip("._")
    return cleaned or "unknown_note"


def note_storage_filename(note_id: str) -> str:
    digest = hashlib.sha1(note_id.encode("utf-8")).hexdigest()[:10]
    return f"{safe_filename(note_id)}-{digest}.md"
