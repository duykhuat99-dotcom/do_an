"""
Router quản trị RAG.

  - POST /rebuild-vector-db : xóa & dựng lại toàn bộ vector store từ metadata.
  - POST /reload-metadata   : nạp lại metadata (upsert đè, không xóa collection).
  - POST /metadata-search   : truy hồi thử để kiểm tra chất lượng RAG.
  - GET  /vector-db-status  : số tài liệu hiện có trong vector store.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.rag import loader, retriever, vector_store
from app.schemas.admin import (
    RebuildResponse,
    RetrieveRequest,
    RetrieveResponse,
)
from app.utils import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["rag-admin"])


@router.post("/rebuild-vector-db", response_model=RebuildResponse, summary="Dựng lại vector DB")
async def rebuild_vector_db() -> RebuildResponse:
    """Xóa collection cũ và embedding lại toàn bộ metadata."""
    try:
        result = loader.rebuild_vector_db(reset=True)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("Lỗi khi rebuild vector DB")
        raise HTTPException(status_code=500, detail=f"Rebuild thất bại: {exc}") from exc
    return RebuildResponse(message="Đã dựng lại vector DB", **result)


@router.post("/reload-metadata", response_model=RebuildResponse, summary="Nạp lại metadata")
async def reload_metadata() -> RebuildResponse:
    """Đọc lại file metadata và upsert (không xóa collection)."""
    try:
        result = loader.rebuild_vector_db(reset=False)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("Lỗi khi reload metadata")
        raise HTTPException(status_code=500, detail=f"Reload thất bại: {exc}") from exc
    return RebuildResponse(message="Đã nạp lại metadata", **result)


@router.post("/metadata-search", response_model=RetrieveResponse, summary="Truy hồi thử RAG")
async def metadata_search(req: RetrieveRequest) -> RetrieveResponse:
    """Embedding câu hỏi và trả về Top-K metadata gần nhất (debug/kiểm thử)."""
    try:
        results = retriever.retrieve(req.query, top_k=req.top_k)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Lỗi khi truy hồi metadata")
        raise HTTPException(status_code=500, detail=f"Truy hồi thất bại: {exc}") from exc
    return RetrieveResponse(query=req.query, count=len(results), results=results)


@router.get("/vector-db-status", summary="Trạng thái vector DB")
async def vector_db_status() -> dict[str, object]:
    """Số tài liệu hiện có trong vector store."""
    return {"documents_in_store": vector_store.count()}
