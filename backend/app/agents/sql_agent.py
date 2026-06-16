"""
SQL Agent (Agent #2).

Nhận câu hỏi + ngữ cảnh schema (từ Metadata Agent), gọi LLM sinh câu lệnh MySQL.
Làm sạch output (gỡ markdown, tiền tố, lấy đúng câu SELECT) trước khi trả về.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from app.llm import get_llm
from app.llm.base import LLMProviderInterface
from app.prompts import SQL_FIX_SYSTEM, SQL_SYSTEM, build_fix_prompt, build_sql_prompt
from app.utils import get_logger

logger = get_logger(__name__)

# Tìm câu lệnh bắt đầu bằng SELECT hoặc WITH (CTE) cho tới hết.
_SQL_PATTERN = re.compile(r"(?is)\b(WITH|SELECT)\b.*")
_FENCE_PATTERN = re.compile(r"```(?:sql)?", re.IGNORECASE)


@dataclass
class GeneratedSQL:
    question: str
    sql: str
    latency_ms: float = 0.0
    model: str = ""


class SQLAgent:
    def __init__(self, llm: LLMProviderInterface | None = None) -> None:
        self._llm = llm

    @property
    def llm(self) -> LLMProviderInterface:
        return self._llm or get_llm()

    def generate(
        self, question: str, schema_context: str, history: str | None = None
    ) -> GeneratedSQL:
        prompt = build_sql_prompt(question, schema_context, history=history)
        resp = self.llm.generate(prompt, system=SQL_SYSTEM, stop=[";"])
        sql = self.clean_sql(resp.text)
        logger.info("SQLAgent sinh SQL (%.0f ms): %s", resp.latency_ms, sql[:120])
        return GeneratedSQL(
            question=question, sql=sql, latency_ms=resp.latency_ms, model=resp.model
        )

    def fix(
        self, question: str, schema_context: str, bad_sql: str, error: str
    ) -> GeneratedSQL:
        """Sửa lại câu SQL bị lỗi dựa trên thông báo lỗi từ MySQL (self-correction)."""
        prompt = build_fix_prompt(question, schema_context, bad_sql, error)
        resp = self.llm.generate(prompt, system=SQL_FIX_SYSTEM, stop=[";"])
        sql = self.clean_sql(resp.text)
        logger.info("SQLAgent SỬA SQL (%.0f ms): %s", resp.latency_ms, sql[:120])
        return GeneratedSQL(
            question=question, sql=sql, latency_ms=resp.latency_ms, model=resp.model
        )

    @staticmethod
    def clean_sql(text: str) -> str:
        """Gỡ markdown/tiền tố và trích đúng câu lệnh SELECT/WITH."""
        cleaned = _FENCE_PATTERN.sub("", text).strip()
        # Bỏ tiền tố kiểu "SQL:", "Câu lệnh:" nếu có.
        cleaned = re.sub(r"(?i)^\s*(sql|câu lệnh|query)\s*:\s*", "", cleaned).strip()
        match = _SQL_PATTERN.search(cleaned)
        if match:
            cleaned = match.group(0)
        # Chuẩn hóa khoảng trắng cuối + bỏ dấu ; thừa.
        return cleaned.strip().rstrip(";").strip()
