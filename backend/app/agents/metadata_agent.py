"""
Metadata Agent (Agent #1).

Nhận câu hỏi người dùng, truy hồi ngữ cảnh schema/KPI/business rules liên quan từ
ChromaDB (qua RAG retriever) để cung cấp cho SQL Agent. Đồng thời trích danh sách
bảng liên quan — dùng cho lớp kiểm tra "chỉ dùng bảng hợp lệ".
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.rag import retriever
from app.utils import get_logger

logger = get_logger(__name__)


@dataclass
class SchemaContext:
    question: str
    context: str
    results: list[dict] = field(default_factory=list)
    tables: list[str] = field(default_factory=list)


class MetadataAgent:
    def __init__(self, top_k: int | None = None) -> None:
        self.top_k = top_k

    def retrieve(self, question: str, top_k: int | None = None) -> SchemaContext:
        results = retriever.retrieve(question, top_k=top_k or self.top_k)
        context = retriever.format_context(results)
        tables = self._extract_tables(results)
        logger.info("MetadataAgent: %d kết quả, bảng liên quan=%s", len(results), tables)
        return SchemaContext(
            question=question, context=context, results=results, tables=tables
        )

    @staticmethod
    def _extract_tables(results: list[dict]) -> list[str]:
        """Lấy danh sách bảng xuất hiện trong metadata truy hồi được."""
        tables: list[str] = []
        for r in results:
            meta = r.get("metadata", {})
            t = meta.get("table")
            if t and t not in tables:
                tables.append(t)
            # KPI/business_rule lưu danh sách bảng dạng chuỗi "a, b"
            raw = meta.get("tables")
            if isinstance(raw, str):
                for name in raw.split(","):
                    name = name.strip()
                    if name and name not in tables:
                        tables.append(name)
        return tables
