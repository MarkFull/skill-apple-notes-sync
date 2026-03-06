from pathlib import Path

from notes_sync.state_db import commit, connect_db, delete_state, init_db, load_state_map, upsert_state


def test_state_db_roundtrip(tmp_path: Path):
    db = tmp_path / "state.db"
    conn = connect_db(db)
    init_db(conn)

    upsert_state(conn, "n1", "2026-03-05T00:00:00Z", "h1", "2026-03-05T00:00:01Z")
    upsert_state(conn, "n2", "2026-03-05T00:00:00Z", "h2", "2026-03-05T00:00:01Z")
    commit(conn)

    state = load_state_map(conn)
    assert state["n1"] == ("2026-03-05T00:00:00Z", "h1")
    assert state["n2"] == ("2026-03-05T00:00:00Z", "h2")

    delete_state(conn, "n1")
    commit(conn)

    state2 = load_state_map(conn)
    assert "n1" not in state2
    assert "n2" in state2
