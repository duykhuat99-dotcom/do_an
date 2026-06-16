"""
AI Orchestrator — điều phối trọn vẹn 6 agent cho một lượt hội thoại:

    câu hỏi (+ session_id)
      -> Metadata Agent   (RAG schema context)
      -> SQL Agent        (sinh SELECT)
      -> Validation Agent (guardrail)
      -> SQL Executor     (read-only) -> DataFrame
      -> Insight Agent    (phân tích)
      -> Visualization Agent (Plotly JSON)
      -> History Agent    (lưu hội thoại + nhật ký truy vấn)
      -> trả về câu trả lời tổng hợp

Tái sử dụng TextToSQLService (Phase 4) cho 4 bước đầu và AnalysisService (Phase 5)
cho insight/chart, rồi bổ sung tổng hợp câu trả lời + lưu lịch sử.
"""
from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from app.agents import ChartConfig, HistoryAgent, InsightResult, RouterAgent
from app.core.config import settings
from app.services.analysis import AnalysisService
from app.services.text_to_sql import TextToSQLService
from app.utils import get_logger

logger = get_logger(__name__)

# Validation mặc định cho câu trả lời thường (không sinh SQL).
_GENERAL_VALIDATION = {
    "safe": True,
    "reason": "Câu hỏi thường — không truy vấn dữ liệu.",
    "regex_passed": True,
    "llm_checked": False,
    "llm_safe": None,
    "checks": {},
}


@dataclass
class ChatResult:
    session_id: str
    question: str
    answer: str
    mode: str = "data"  # "data" | "general"
    sql: str = ""
    validation: dict[str, Any] = field(default_factory=dict)
    tables: list[str] = field(default_factory=list)
    columns: list[str] | None = None
    rows: list[dict[str, Any]] | None = None
    row_count: int | None = None
    insight: InsightResult | None = None
    chart: ChartConfig | None = None
    execution_time_ms: float | None = None
    total_time_ms: float = 0.0
    success: bool = False
    error: str | None = None


class Orchestrator:
    def __init__(
        self,
        text_to_sql: TextToSQLService | None = None,
        analysis: AnalysisService | None = None,
        history: HistoryAgent | None = None,
        router: RouterAgent | None = None,
    ) -> None:
        self.text_to_sql = text_to_sql or TextToSQLService()
        self.analysis = analysis or AnalysisService()
        self.history = history or HistoryAgent()
        self.router = router or RouterAgent()

    def process_chat(
        self,
        question: str,
        session_id: str | None = None,
        *,
        top_k: int | None = None,
        max_rows: int = 1000,
        with_chart: bool = True,
    ) -> ChatResult:
        session_id = session_id or uuid.uuid4().hex
        start = time.perf_counter()

        # B0: phân loại ý định — câu hỏi thường thì trả lời trực tiếp, không sinh SQL.
        if self.router.classify(question) == "general":
            answer = self.router.answer_general(question)
            result = ChatResult(
                session_id=session_id,
                question=question,
                answer=answer,
                mode="general",
                validation=dict(_GENERAL_VALIDATION),
                success=True,
            )
            self._persist(result, success=True, exec_ms=0.0)
            result.total_time_ms = _ms(start)
            logger.info("Orchestrator (general) phiên=%s (%.0f ms)", session_id, result.total_time_ms)
            return result

        # B1-4: metadata -> sql -> validation -> execute (kèm ngữ cảnh hội thoại)
        history_ctx = self._recent_history_context(session_id)
        outcome = self.text_to_sql.run(
            question, top_k=top_k, execute=True, max_rows=max_rows, history=history_ctx
        )
        result = ChatResult(
            session_id=session_id,
            question=question,
            answer="",
            sql=outcome.sql,
            validation=TextToSQLService.to_validation_dict(outcome.validation),
            tables=outcome.tables,
        )

        # Trường hợp bị guardrail chặn hoặc lỗi thực thi
        if outcome.result is None:
            result.error = outcome.error or "Không thể thực thi truy vấn."
            result.answer = self._error_answer(outcome)
            self._persist(result, success=False, exec_ms=0.0)
            result.total_time_ms = _ms(start)
            return result

        qr = outcome.result
        result.columns = qr.columns
        result.rows = qr.rows
        result.row_count = qr.row_count
        result.execution_time_ms = qr.execution_time_ms

        # B5-6: insight + chart
        analysis = self.analysis.analyze(question, qr.dataframe, with_insight=True)
        result.insight = analysis.insight
        result.chart = analysis.chart if with_chart else None
        result.answer = (
            analysis.insight.summary if analysis.insight else "Đã truy vấn xong dữ liệu."
        )
        result.success = True

        # B7: lưu lịch sử
        self._persist(result, success=True, exec_ms=qr.execution_time_ms)
        result.total_time_ms = _ms(start)
        logger.info(
            "Orchestrator hoàn tất phiên=%s (%.0f ms, %d dòng)",
            session_id, result.total_time_ms, qr.row_count,
        )
        return result

    def _recent_history_context(self, session_id: str) -> str:
        """Lấy vài lượt hội thoại gần nhất, định dạng cho ngữ cảnh multi-turn.

        Tại thời điểm này câu hỏi hiện tại CHƯA được lưu, nên chỉ trả về các lượt trước.
        """
        turns = settings.history_context_turns
        if turns <= 0:
            return ""
        rows = self.history.get_history(session_id, limit=turns * 2)
        if not rows:
            return ""
        lines: list[str] = []
        for r in reversed(rows):  # mới nhất ở cuối -> đảo về thứ tự thời gian
            if r.get("role") == "user" and r.get("question"):
                lines.append(f"Người dùng: {r['question']}")
            elif r.get("role") == "assistant" and r.get("generated_sql"):
                lines.append(f"SQL đã dùng: {r['generated_sql']}")
        return "\n".join(lines[-(turns * 2):])

    def get_history(self, session_id: str, limit: int = 20) -> list[dict[str, Any]]:
        return self.history.get_history(session_id, limit=limit)

    def list_sessions(self, limit: int = 50) -> list[dict[str, Any]]:
        return self.history.list_sessions(limit=limit)

    def get_stats(self) -> dict[str, Any]:
        return self.history.get_stats()

    def save_feedback(
        self, rating: str, question: str | None, answer: str | None, session_id: str | None = None
    ) -> bool:
        return self.history.save_feedback(rating, question, answer, session_id)

    # ---------- Nội bộ ----------
    def _persist(self, result: ChatResult, success: bool, exec_ms: float) -> None:
        self.history.save_turn(
            result.session_id,
            result.question,
            result.answer,
            result.sql or None,
            chart_json=_serialize_chart(result.chart),
            insight_json=_serialize_insight(result.insight),
        )
        self.history.log_query(
            result.session_id,
            result.question,
            result.sql or None,
            success=success,
            row_count=result.row_count or 0,
            execution_time_ms=exec_ms,
            error=result.error,
        )

    @staticmethod
    def _error_answer(outcome) -> str:
        if not outcome.validation.safe:
            return (
                "Xin lỗi, yêu cầu này không thể thực hiện vì lý do an toàn dữ liệu: "
                f"{outcome.validation.reason}"
            )
        return f"Xin lỗi, đã xảy ra lỗi khi truy vấn dữ liệu: {outcome.error}"


def _ms(start: float) -> float:
    return round((time.perf_counter() - start) * 1000, 2)


def _serialize_chart(chart: ChartConfig | None) -> str | None:
    if chart is None:
        return None
    return json.dumps(
        {
            "chart_type": chart.chart_type,
            "plotly": chart.plotly,
            "x": chart.x,
            "y": chart.y,
            "title": chart.title,
            "reason": chart.reason,
        },
        ensure_ascii=False,
        default=str,
    )


def _serialize_insight(insight: InsightResult | None) -> str | None:
    if insight is None:
        return None
    return json.dumps(
        {
            "summary": insight.summary,
            "highlights": insight.highlights,
            "stats": insight.stats,
            "llm_used": insight.llm_used,
        },
        ensure_ascii=False,
        default=str,
    )
