from datetime import datetime, timezone

from fastapi.testclient import TestClient

from notes_sync.models import SearchResult


class FakeIndexer:
    def __init__(self, *_args, **_kwargs):
        from types import SimpleNamespace

        self.items = []
        self.cfg = SimpleNamespace(run_embed=False)

    def ensure_collection(self):
        return None

    def _run(self, *_args, **_kwargs):
        return ""

    def ingest(self, notes, **_kwargs):
        self.items.extend(notes)
        return [{"note_id": n.note_id, "status": "upserted"} for n in notes]

    def search(self, query, top_k, filters=None, mode="search"):
        _ = (query, top_k, filters, mode)
        return [
            SearchResult(
                score=0.9,
                note_id="n1",
                title="App ideas",
                snippet="notes sync with qmd",
                folder="Ideas",
                updated_at=datetime(2026, 3, 5, tzinfo=timezone.utc),
                file="qmd://apple_notes/n1.md",
            )
        ]


def test_api_ingest_and_search(monkeypatch):
    monkeypatch.setenv("INGEST_TOKEN", "ingest-token")
    monkeypatch.setenv("SEARCH_TOKEN", "search-token")

    import notes_sync.api as api_mod

    monkeypatch.setattr(api_mod, "QmdIndexer", FakeIndexer)
    app = api_mod.build_app()
    client = TestClient(app)

    health = client.get("/health")
    assert health.status_code == 200

    payload = {
        "batch_id": "b1",
        "sent_at": "2026-03-05T00:00:00Z",
        "notes": [
            {
                "source": "apple_notes",
                "note_id": "n1",
                "title": "App ideas",
                "content_text": "Build sync",
                "content_html": None,
                "folder": "Ideas",
                "account": "iCloud",
                "created_at": "2026-03-05T00:00:00Z",
                "updated_at": "2026-03-05T00:00:00Z",
                "hash": "abc",
                "deleted": False,
                "meta": {"tags": [], "language": None},
            }
        ],
    }

    r1 = client.post("/ingest/apple-notes/batch", json=payload)
    assert r1.status_code == 401

    r2 = client.post(
        "/ingest/apple-notes/batch",
        json=payload,
        headers={"Authorization": "Bearer ingest-token", "X-Defer-QMD-Update": "1"},
    )
    assert r2.status_code == 200
    assert r2.json()["accepted"] == 1

    r3 = client.post(
        "/search/apple-notes",
        json={"query": "sync", "top_k": 3, "mode": "search"},
        headers={"Authorization": "Bearer search-token"},
    )
    assert r3.status_code == 200
    assert r3.json()["results"][0]["note_id"] == "n1"

    r3b = client.post(
        "/tool/notes_search",
        json={"query": "sync", "top_k": 2, "mode": "search"},
        headers={"Authorization": "Bearer search-token"},
    )
    assert r3b.status_code == 200
    assert r3b.json()["results"][0]["note_id"] == "n1"

    r4 = client.post("/admin/qmd/update", headers={"Authorization": "Bearer ingest-token"})
    assert r4.status_code == 200
    assert r4.text == "ok"
