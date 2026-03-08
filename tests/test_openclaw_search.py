import pytest

from notes_sync import openclaw_search as ns


class _Resp:
    def __init__(self, status_code: int, body=None, text: str = ""):
        self.status_code = status_code
        self._body = body if body is not None else {}
        self.text = text

    def json(self):
        return self._body


def test_resolve_token_priority(monkeypatch):
    monkeypatch.setenv("NOTES_SEARCH_TOKEN", "from-notes")
    monkeypatch.setenv("SEARCH_TOKEN", "from-search")

    assert ns.resolve_token("explicit") == "explicit"
    assert ns.resolve_token(None) == "from-notes"

    monkeypatch.delenv("NOTES_SEARCH_TOKEN", raising=False)
    assert ns.resolve_token(None) == "from-search"


def test_notes_search_fallback_from_tool_alias(monkeypatch):
    calls = []

    def fake_post(url, headers=None, json=None, timeout=None):
        calls.append(url)
        if url.endswith("/tool/notes_search"):
            return _Resp(404, text="not found")
        return _Resp(200, body={"ok": True, "results": [{"title": "t"}]})

    monkeypatch.setattr(ns.requests, "post", fake_post)

    out = ns.notes_search(
        base_url="http://127.0.0.1:8787",
        query="test",
        top_k=3,
        mode="search",
        token="tok",
        folders=None,
        from_date=None,
        to_date=None,
        timeout=5,
    )

    assert out["ok"] is True
    assert calls[0].endswith("/tool/notes_search")
    assert calls[1].endswith("/search/apple-notes")


def test_notes_search_unauthorized(monkeypatch):
    def fake_post(url, headers=None, json=None, timeout=None):
        _ = (url, headers, json, timeout)
        return _Resp(401, text="unauthorized")

    monkeypatch.setattr(ns.requests, "post", fake_post)

    with pytest.raises(RuntimeError, match="Unauthorized"):
        ns.notes_search(
            base_url="http://127.0.0.1:8787",
            query="test",
            top_k=3,
            mode="search",
            token=None,
            folders=None,
            from_date=None,
            to_date=None,
            timeout=5,
        )
