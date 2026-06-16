"""
Text-to-SQL Service — ghép các agent của Phase 4 thành một luồng:

    câu hỏi
      -> Metadata Agent  (RAG: lấy schema context)
      -> SQL Agent       (sinh SELECT)
      -> Validation Agent(guardrail regex + LLM)
      -> [tùy chọn] SQL Executor (read-only) -> DataFrame

Orchestrator đầy đủ (kèm Insight/Chart/History) sẽ build trên service này ở Phase 6.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.agents import MetadataAgent, SQLAgent, ValidationAgent
from app.agents.validation_agent import ValidationResult
from app.core.config import settings
from app.services.sql_executor import QueryResult, SQLExecutionError, execute_sql
from app.utils import get_logger

logger = get_logger(__name__)


@dataclass
class TextToSQLOutcome:
    question: str
    sql: str
    validation: ValidationResult
    tables: list[str] = field(default_factory=list)
    schema_context: str = ""
    latency_ms: float = 0.0
    executed: bool = False
    result: QueryResult | None = None
    error: str | None = None
    attempts: int = 1       # số lần sinh SQL (1 = không phải sửa)
    corrected: bool = False  # có dùng self-correction không


class TextToSQLService:
    def __init__(
        self,
        metadata_agent: MetadataAgent | None = None,
        sql_agent: SQLAgent | None = None,
        validation_agent: ValidationAgent | None = None,
    ) -> None:
        self.metadata_agent = metadata_agent or MetadataAgent()
        self.sql_agent = sql_agent or SQLAgent()
        self.validation_agent = validation_agent or ValidationAgent()

    def run(
        self,
        question: str,
        *,
        top_k: int | None = None,
        execute: bool = False,
        max_rows: int = 1000,
        history: str | None = None,
    ) -> TextToSQLOutcome:
        # 1) Metadata Agent — RAG
        ctx = self.metadata_agent.retrieve(question, top_k=top_k)

        # 2) SQL Agent — sinh SQL (kèm lịch sử hội thoại cho câu hỏi nối tiếp)
        generated = self.sql_agent.generate(question, ctx.context, history=history)

        # 3) Validation Agent — guardrail
        validation = self.validation_agent.validate(generated.sql)

        outcome = TextToSQLOutcome(
            question=question,
            sql=generated.sql,
            validation=validation,
            tables=ctx.tables,
            schema_context=ctx.context,
            latency_ms=generated.latency_ms,
        )

        if not execute:
            return outcome
        if not validation.safe:
            outcome.error = f"SQL bị chặn bởi guardrail: {validation.reason}"
            return outcome

        # 4) Thực thi (read-only) — có self-correction khi lỗi
        self._execute_with_retry(outcome, ctx.context, max_rows)
        return outcome

    def _execute_with_retry(
        self, outcome: TextToSQLOutcome, schema_context: str, max_rows: int
    ) -> None:
        """Thực thi SQL; nếu lỗi thì nhờ LLM sửa rồi thử lại (tối đa sql_max_retries)."""
        sql = outcome.sql
        max_retries = settings.sql_max_retries
        attempt = 0
        while True:
            try:
                outcome.result = execute_sql(sql, max_rows=max_rows)
                outcome.executed = True
                outcome.sql = sql
                return
            except SQLExecutionError as exc:
                if attempt >= max_retries:
                    outcome.error = f"Lỗi thực thi SQL: {exc}"
                    outcome.sql = sql
                    logger.warning(
                        "Thực thi thất bại sau %d lần thử: %s", attempt + 1, exc
                    )
                    return
                attempt += 1
                logger.info("Self-correction lần %d cho câu hỏi: %s", attempt, outcome.question[:60])
                fixed = self.sql_agent.fix(outcome.question, schema_context, sql, str(exc))
                # Câu SQL sửa lại vẫn phải qua guardrail.
                v = self.validation_agent.validate(fixed.sql)
                if not v.safe:
                    outcome.error = f"SQL sửa lại bị guardrail chặn: {v.reason}"
                    outcome.validation = v
                    return
                sql = fixed.sql
                outcome.validation = v
                outcome.corrected = True
                outcome.attempts = attempt + 1

    @staticmethod
    def to_validation_dict(v: ValidationResult) -> dict[str, Any]:
        return {
            "safe": v.safe,
            "reason": v.reason,
            "regex_passed": v.regex_passed,
            "llm_checked": v.llm_checked,
            "llm_safe": v.llm_safe,
            "checks": v.checks,
        }
