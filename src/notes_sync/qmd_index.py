from __future__ import annotations

import json
import sqlite3
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .models import NoteRecord, SearchFilters, SearchResult
from .utils import note_storage_filename


@dataclass
class QmdConfig:
    qmd_bin: str = "qmd"
    collection: str = "apple_notes"
    data_dir: Path = Path("./data/notes")
    mask: str = "*.md"
    run_embed: bool = False


class QmdIndexer:
    def __init__(self, cfg: QmdConfig):
        self.cfg = cfg
        self.cfg.data_dir.mkdir(parents=True, exist_ok=True)
        self.meta_db = self.cfg.data_dir.parent / "notes_meta.sqlite"
        self._init_meta_db()

    def _run(self, *args: str) -> str:
        cmd = [self.cfg.qmd_bin, *args]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError(f"qmd command failed: {' '.join(cmd)}\n{proc.stderr.strip()}")
        return proc.stdout

    def _init_meta_db(self) -> None:
        conn = sqlite3.connect(self.meta_db)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS note_meta (
              note_id TEXT PRIMARY KEY,
              file_name TEXT NOT NULL,
              title TEXT,
              folder TEXT,
              updated_at TEXT,
              hash TEXT,
              deleted INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        conn.commit()
        conn.close()

    def _upsert_meta(self, note: NoteRecord, file_name: str) -> None:
        conn = sqlite3.connect(self.meta_db)
        conn.execute(
            """
            INSERT INTO note_meta(note_id, file_name, title, folder, updated_at, hash, deleted)
            VALUES (?, ?, ?, ?, ?, ?, 0)
            ON CONFLICT(note_id)
            DO UPDATE SET
              file_name=excluded.file_name,
              title=excluded.title,
              folder=excluded.folder,
              updated_at=excluded.updated_at,
              hash=excluded.hash,
              deleted=0
            """,
            (
                note.note_id,
                file_name,
                note.title,
                note.folder,
                note.updated_at.isoformat(),
                note.hash,
            ),
        )
        conn.commit()
        conn.close()

    def _mark_deleted_meta(self, note_id: str) -> None:
        conn = sqlite3.connect(self.meta_db)
        conn.execute("UPDATE note_meta SET deleted=1 WHERE note_id=?", (note_id,))
        conn.commit()
        conn.close()

    def _meta_for_file(self, file_ref: str) -> dict | None:
        """Lookup metadata for a QMD result.

        QMD returns a normalized filename inside the `qmd://...` URI that may not
        match the original on-disk filename exactly (case/underscore/hyphen
        differences). We therefore:

        1) Try exact match on `file_name`.
        2) Fallback to matching by the stable sha1 digest suffix we add in
           `note_storage_filename()` (last `-<10hex>.md`).
        """

        file_name = file_ref.split("/")[-1] if "/" in file_ref else file_ref

        conn = sqlite3.connect(self.meta_db)
        row = conn.execute(
            "SELECT note_id, title, folder, updated_at, deleted FROM note_meta WHERE file_name=?",
            (file_name,),
        ).fetchone()

        if not row:
            # Fallback: match by digest suffix.
            import re

            m = re.match(r".*-([0-9a-f]{10})\.md$", file_name)
            if m:
                digest = m.group(1)
                row = conn.execute(
                    "SELECT note_id, title, folder, updated_at, deleted FROM note_meta WHERE file_name LIKE ? LIMIT 1",
                    (f"%-{digest}.md",),
                ).fetchone()

        conn.close()

        if not row:
            return None

        return {
            "note_id": row[0],
            "title": row[1],
            "folder": row[2],
            "updated_at": row[3],
            "deleted": bool(row[4]),
        }

    def ensure_collection(self) -> None:
        out = self._run("collection", "list")
        marker = f"{self.cfg.collection} (qmd://"
        if marker in out:
            return
        self._run(
            "collection",
            "add",
            str(self.cfg.data_dir),
            "--name",
            self.cfg.collection,
            "--mask",
            self.cfg.mask,
        )

    def _render_markdown(self, note: NoteRecord) -> str:
        frontmatter = {
            "source": note.source,
            "note_id": note.note_id,
            "title": note.title,
            "folder": note.folder,
            "account": note.account,
            "created_at": note.created_at.isoformat(),
            "updated_at": note.updated_at.isoformat(),
            "hash": note.hash,
        }
        return (
            "---\n"
            + "\n".join(f"{k}: {json.dumps(v)}" for k, v in frontmatter.items())
            + "\n---\n\n"
            + f"# {note.title or 'Untitled'}\n\n"
            + (note.content_text or "")
            + "\n"
        )

    def ingest(self, notes: list[NoteRecord], *, defer_update: bool = False) -> list[dict]:
        self.ensure_collection()
        results: list[dict] = []
        changed = False

        for note in notes:
            file_name = note_storage_filename(note.note_id)
            file_path = self.cfg.data_dir / file_name

            if note.deleted:
                if file_path.exists():
                    file_path.unlink()
                    changed = True
                self._mark_deleted_meta(note.note_id)
                results.append({"note_id": note.note_id, "status": "deleted"})
                continue

            content = self._render_markdown(note)
            old = file_path.read_text() if file_path.exists() else None
            if old != content:
                file_path.write_text(content)
                changed = True
                status = "upserted"
            else:
                status = "unchanged"

            self._upsert_meta(note, file_name)
            results.append({"note_id": note.note_id, "status": status})

        if changed and not defer_update:
            self._run("update")
            if self.cfg.run_embed:
                self._run("embed")

        return results

    def search(self, query: str, top_k: int, filters: SearchFilters | None = None, mode: str = "search") -> list[SearchResult]:
        cmd_mode = "query" if mode == "query" else "search"
        out = self._run(cmd_mode, query, "-c", self.cfg.collection, "--json", "-n", str(top_k))
        rows = json.loads(out)

        results: list[SearchResult] = []
        for row in rows:
            file_ref = row.get("file", "")
            meta = self._meta_for_file(file_ref) if file_ref else None

            if meta and meta.get("deleted"):
                continue

            folder = meta.get("folder") if meta else None
            updated_at = None
            if meta and meta.get("updated_at"):
                try:
                    updated_at = datetime.fromisoformat(meta["updated_at"].replace("Z", "+00:00"))
                except Exception:
                    updated_at = None

            if filters:
                if filters.folder and folder not in set(filters.folder):
                    continue
                if filters.from_date and updated_at and updated_at < filters.from_date:
                    continue
                if filters.to_date and updated_at and updated_at > filters.to_date:
                    continue

            results.append(
                SearchResult(
                    score=float(row.get("score") or 0.0),
                    note_id=meta.get("note_id") if meta else None,
                    title=(meta.get("title") if meta and meta.get("title") else row.get("title") or ""),
                    snippet=row.get("snippet") or "",
                    folder=folder,
                    updated_at=updated_at,
                    file=file_ref,
                    raw=row,
                )
            )

        return results
