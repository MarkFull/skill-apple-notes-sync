from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class NoteMeta(BaseModel):
    tags: list[str] = Field(default_factory=list)
    language: str | None = None


class NoteRecord(BaseModel):
    source: str = "apple_notes"
    note_id: str
    title: str = ""
    content_text: str = ""
    content_html: str | None = None
    folder: str | None = None
    account: str | None = None
    created_at: datetime
    updated_at: datetime
    hash: str
    deleted: bool = False
    meta: NoteMeta = Field(default_factory=NoteMeta)


class IngestBatchRequest(BaseModel):
    batch_id: str
    sent_at: datetime
    notes: list[NoteRecord]


class IngestItemResult(BaseModel):
    note_id: str
    status: str
    error: str | None = None


class IngestBatchResponse(BaseModel):
    ok: bool = True
    batch_id: str
    accepted: int
    rejected: int
    items: list[IngestItemResult]


class SearchFilters(BaseModel):
    folder: list[str] | None = None
    from_date: datetime | None = None
    to_date: datetime | None = None


class SearchRequest(BaseModel):
    query: str
    top_k: int = 8
    filters: SearchFilters | None = None
    mode: str = "search"  # search|query


class SearchResult(BaseModel):
    score: float
    note_id: str | None = None
    title: str
    snippet: str
    folder: str | None = None
    updated_at: datetime | None = None
    file: str
    raw: dict[str, Any] | None = None


class SearchResponse(BaseModel):
    ok: bool = True
    results: list[SearchResult]
