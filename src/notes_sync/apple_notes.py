from __future__ import annotations

import html
import json
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone

from .models import NoteRecord
from .utils import compute_note_hash


JXA_NOTES_META = r'''
ObjC.import('Foundation');

function toIso(d) {
  try {
    const dt = new Date(d);
    if (isNaN(dt.getTime())) return null;
    return dt.toISOString();
  } catch (e) {
    return null;
  }
}

function run() {
  const Notes = Application('Notes');
  Notes.includeStandardAdditions = true;

  const out = [];

  function pushMeta(note, accountName, folderName) {
    try {
      out.push({
        note_id: String(note.id()),
        title: String(note.name() || ''),
        account: accountName || null,
        folder: folderName || null,
        created_at: toIso(note.creationDate()),
        updated_at: toIso(note.modificationDate()),
      });
    } catch (e) {}
  }

  try {
    const accounts = Notes.accounts();
    for (let i = 0; i < accounts.length; i++) {
      const acc = accounts[i];
      const accountName = String(acc.name());

      const folders = acc.folders();
      for (let f = 0; f < folders.length; f++) {
        const folder = folders[f];
        const folderName = String(folder.name());
        const notes = folder.notes();
        for (let n = 0; n < notes.length; n++) {
          pushMeta(notes[n], accountName, folderName);
        }
      }
    }
  } catch (e) {
    const notes = Notes.notes();
    for (let i = 0; i < notes.length; i++) {
      pushMeta(notes[i], null, null);
    }
  }

  return JSON.stringify(out);
}
'''


TAG_RE = re.compile(r"<[^>]+>")


def html_to_text(s: str) -> str:
    if not s:
        return ""
    t = html.unescape(TAG_RE.sub(" ", s))
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _to_dt(raw: str | None) -> datetime:
    if not raw:
        return datetime.now(timezone.utc)
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except Exception:
        return datetime.now(timezone.utc)


def _osascript_jxa(script: str) -> list[dict]:
    cmd = ["osascript", "-l", "JavaScript", "-e", script]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    payload = proc.stdout.strip() or "[]"
    return json.loads(payload)


@dataclass(frozen=True)
class NoteMetaRow:
    note_id: str
    title: str
    folder: str | None
    account: str | None
    created_at: datetime
    updated_at: datetime


def fetch_notes_meta() -> list[NoteMetaRow]:
    rows = _osascript_jxa(JXA_NOTES_META)

    out: list[NoteMetaRow] = []
    for row in rows:
        note_id = str(row.get("note_id") or "")
        if not note_id:
            continue
        out.append(
            NoteMetaRow(
                note_id=note_id,
                title=str(row.get("title") or ""),
                folder=row.get("folder"),
                account=row.get("account"),
                created_at=_to_dt(row.get("created_at")),
                updated_at=_to_dt(row.get("updated_at")),
            )
        )

    return out


def _build_jxa_full(target_ids: set[str] | None) -> str:
    # Only call note.body() for target ids (huge perf win).
    ids_expr = "null" if target_ids is None else json.dumps(sorted(target_ids))

    return f'''
ObjC.import('Foundation');

function toIso(d) {{
  try {{
    const dt = new Date(d);
    if (isNaN(dt.getTime())) return null;
    return dt.toISOString();
  }} catch (e) {{
    return null;
  }}
}}

function run() {{
  const Notes = Application('Notes');
  Notes.includeStandardAdditions = true;

  const targetIds = {ids_expr};
  const targetSet = targetIds ? new Set(targetIds) : null;

  const out = [];

  function pushNote(note, accountName, folderName) {{
    try {{
      const nid = String(note.id());
      if (targetSet && !targetSet.has(nid)) return;

      out.push({{
        note_id: nid,
        title: String(note.name() || ''),
        content_html: String(note.body() || ''),
        account: accountName || null,
        folder: folderName || null,
        created_at: toIso(note.creationDate()),
        updated_at: toIso(note.modificationDate()),
      }});
    }} catch (e) {{}}
  }}

  try {{
    const accounts = Notes.accounts();
    for (let i = 0; i < accounts.length; i++) {{
      const acc = accounts[i];
      const accountName = String(acc.name());

      const folders = acc.folders();
      for (let f = 0; f < folders.length; f++) {{
        const folder = folders[f];
        const folderName = String(folder.name());
        const notes = folder.notes();
        for (let n = 0; n < notes.length; n++) {{
          pushNote(notes[n], accountName, folderName);
        }}
      }}
    }}
  }} catch (e) {{
    const notes = Notes.notes();
    for (let i = 0; i < notes.length; i++) {{
      pushNote(notes[i], null, null);
    }}
  }}

  return JSON.stringify(out);
}}
'''


def fetch_notes_full(target_ids: set[str] | None = None) -> list[NoteRecord]:
    rows = _osascript_jxa(_build_jxa_full(target_ids))

    out: list[NoteRecord] = []
    for row in rows:
        note_id = str(row.get("note_id") or "")
        if not note_id:
            continue

        title = str(row.get("title") or "")
        content_html = row.get("content_html")
        content_text = html_to_text(str(content_html or ""))
        folder = row.get("folder")
        note_hash = compute_note_hash(title, content_text, folder)

        out.append(
            NoteRecord(
                source="apple_notes",
                note_id=note_id,
                title=title,
                content_text=content_text,
                content_html=content_html,
                folder=folder,
                account=row.get("account"),
                created_at=_to_dt(row.get("created_at")),
                updated_at=_to_dt(row.get("updated_at")),
                hash=note_hash,
                deleted=False,
            )
        )

    return out


def fetch_notes() -> list[NoteRecord]:
    # Back-compat helper.
    return fetch_notes_full(target_ids=None)
