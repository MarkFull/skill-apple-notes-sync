from __future__ import annotations

import sqlite3
from pathlib import Path


def connect_db(path: str | Path) -> sqlite3.Connection:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p))
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS notes_state (
          note_id TEXT PRIMARY KEY,
          updated_at TEXT NOT NULL,
          hash TEXT NOT NULL,
          last_seen_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS sync_state (
          key TEXT PRIMARY KEY,
          value TEXT NOT NULL
        );
        """
    )
    conn.commit()


def load_state_map(conn: sqlite3.Connection) -> dict[str, tuple[str, str]]:
    rows = conn.execute("SELECT note_id, updated_at, hash FROM notes_state").fetchall()
    return {r[0]: (r[1], r[2]) for r in rows}


def upsert_state(conn: sqlite3.Connection, note_id: str, updated_at: str, hash_value: str, seen_at: str) -> None:
    conn.execute(
        """
        INSERT INTO notes_state(note_id, updated_at, hash, last_seen_at)
        VALUES(?, ?, ?, ?)
        ON CONFLICT(note_id)
        DO UPDATE SET updated_at=excluded.updated_at, hash=excluded.hash, last_seen_at=excluded.last_seen_at
        """,
        (note_id, updated_at, hash_value, seen_at),
    )


def delete_state(conn: sqlite3.Connection, note_id: str) -> None:
    conn.execute("DELETE FROM notes_state WHERE note_id=?", (note_id,))


def commit(conn: sqlite3.Connection) -> None:
    conn.commit()
