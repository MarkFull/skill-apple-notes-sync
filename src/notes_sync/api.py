from __future__ import annotations

import os
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, Response

from .models import (
    IngestBatchRequest,
    IngestBatchResponse,
    IngestItemResult,
    SearchRequest,
    SearchResponse,
)
from .qmd_index import QmdConfig, QmdIndexer


def _bearer_token(value: str | None) -> str | None:
    if not value:
        return None
    if not value.lower().startswith("bearer "):
        return None
    return value.split(" ", 1)[1].strip()


def build_app() -> FastAPI:
    ingest_token = os.getenv("INGEST_TOKEN", "")
    search_token = os.getenv("SEARCH_TOKEN", ingest_token)
    qmd_bin = os.getenv("QMD_BIN", "qmd")
    collection = os.getenv("QMD_COLLECTION", "apple_notes")
    data_dir = Path(os.getenv("NOTES_DATA_DIR", "./data/notes"))
    run_embed = os.getenv("QMD_RUN_EMBED", "false").lower() in {"1", "true", "yes"}

    app = FastAPI(title="Apple Notes QMD Bridge", version="0.1.0")
    indexer = QmdIndexer(QmdConfig(qmd_bin=qmd_bin, collection=collection, data_dir=data_dir, run_embed=run_embed))

    def require_ingest_token(authorization: str | None = Header(default=None)) -> None:
        if not ingest_token:
            return
        token = _bearer_token(authorization)
        if token != ingest_token:
            raise HTTPException(status_code=401, detail="unauthorized")

    def require_search_token(authorization: str | None = Header(default=None)) -> None:
        if not search_token:
            return
        token = _bearer_token(authorization)
        if token != search_token:
            raise HTTPException(status_code=401, detail="unauthorized")

    @app.get("/health")
    def health() -> dict:
        return {"ok": True, "index_ready": True, "qmd_collection": collection}

    @app.post("/ingest/apple-notes/batch", response_model=IngestBatchResponse)
    def ingest_batch(
        req: IngestBatchRequest,
        _: None = Depends(require_ingest_token),
        x_defer_qmd_update: str | None = Header(default=None),
    ) -> IngestBatchResponse:
        defer_update = (x_defer_qmd_update or "").strip().lower() in {"1", "true", "yes"}
        try:
            items = indexer.ingest(req.notes, defer_update=defer_update)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"ingest failed: {e}") from e

        result_items: list[IngestItemResult] = []
        rejected = 0
        for item in items:
            status = item.get("status", "rejected")
            if status == "rejected":
                rejected += 1
            result_items.append(IngestItemResult(note_id=item.get("note_id", ""), status=status, error=item.get("error")))

        return IngestBatchResponse(
            ok=True,
            batch_id=req.batch_id,
            accepted=len(result_items) - rejected,
            rejected=rejected,
            items=result_items,
        )

    def _run_search(req: SearchRequest) -> SearchResponse:
        try:
            rows = indexer.search(req.query, req.top_k, filters=req.filters, mode=req.mode)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"search failed: {e}") from e
        return SearchResponse(ok=True, results=rows)

    @app.post("/search/apple-notes", response_model=SearchResponse)
    def search_notes(req: SearchRequest, _: None = Depends(require_search_token)) -> SearchResponse:
        return _run_search(req)

    @app.post("/tool/notes_search", response_model=SearchResponse)
    def tool_notes_search(req: SearchRequest, _: None = Depends(require_search_token)) -> SearchResponse:
        # OpenClaw-facing alias route that keeps the user mental model as "notes_search".
        return _run_search(req)

    @app.post("/admin/qmd/update")
    def qmd_update(_: None = Depends(require_ingest_token)) -> Response:
        # Force an index refresh after deferred batch ingests.
        try:
            indexer.ensure_collection()
            indexer._run("update")
            if indexer.cfg.run_embed:
                indexer._run("embed")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"qmd update failed: {e}") from e
        return Response(content="ok", media_type="text/plain")

    return app


app = build_app()
