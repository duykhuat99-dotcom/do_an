"""
Retriever: embedding câu hỏi -> Similarity Search trên ChromaDB -> Schema Context.

Là lớp truy hồi nền tảng. Metadata Agent (Phase 4) sẽ gọi vào đây để lấy ngữ cảnh
schema/KPI/business rules liên quan trước khi sinh SQL.
"""
from __future__ import annotations

from app.core.config import settings
from app.rag import embedder, vector_store
from app.utils import get_logger

logger = get_logger(__name__)


def retrieve(query: str, top_k: int | None = None, where: dict | None = None) -> list[dict]:
    """Truy hồi Top-K tài liệu metadata gần nhất với câu hỏi."""
    k = top_k or settings.retrieval_top_k
    q_vec = embedder.embed_query(query)
    results = vector_store.query(q_vec, top_k=k, where=where)
    logger.info("Retrieve '%s' -> %d kết quả (top_k=%d)", query[:60], len(results), k)
    return results


def format_context(results: list[dict]) -> str:
    """Gộp kết quả truy hồi thành một đoạn ngữ cảnh đọc được cho LLM."""
    if not results:
        return "(Không tìm thấy ngữ cảnh schema phù hợp.)"
    lines = []
    for r in results:
        rtype = r["metadata"].get("type", "?")
        lines.append(f"[{rtype}] {r['document']}")
    return "\n".join(lines)


def retrieve_context(query: str, top_k: int | None = None) -> dict:
    """Tiện ích: trả về cả kết quả thô và ngữ cảnh đã định dạng."""
    results = retrieve(query, top_k=top_k)
    return {"results": results, "context": format_context(results)}
