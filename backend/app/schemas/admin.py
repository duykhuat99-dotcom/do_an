"""Schema cho các endpoint quản trị RAG."""
from __future__ import annotations

from pydantic import BaseModel, Field


class RebuildResponse(BaseModel):
    """Kết quả build/reload vector DB."""

    success: bool = True
    message: str
    documents_built: int
    documents_in_store: int
    reset: bool
    by_type: dict[str, int] = Field(default_factory=dict)


class RetrieveRequest(BaseModel):
    """Yêu cầu truy hồi metadata (phục vụ kiểm thử RAG)."""

    query: str = Field(..., min_length=1, examples=["doanh thu theo chi nhánh"])
    top_k: int | None = Field(default=None, ge=1, le=50)


class RetrieveItem(BaseModel):
    id: str
    document: str
    metadata: dict
    distance: float


class RetrieveResponse(BaseModel):
    query: str
    count: int
    results: list[RetrieveItem]
