"""
Router cho pipeline Text-to-SQL.

  - POST /generate-sql : sinh SQL từ câu hỏi (kèm guardrail); tùy chọn thực thi.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.llm import LLMError
from app.schemas.query import (
    ChartInfo,
    ChartRequest,
    ChartResponse,
    GenerateSQLRequest,
    GenerateSQLResponse,
    InsightInfo,
    ValidationInfo,
)
from app.services.analysis import AnalysisService
from app.services.text_to_sql import TextToSQLService
from app.utils import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["query"])

_service = TextToSQLService()
_analysis = AnalysisService()


def _format_history(turns) -> str | None:
    """Định dạng các lượt hỏi trước thành ngữ cảnh multi-turn cho SQL Agent."""
    if not turns:
        return None
    from app.core.config import settings

    lines: list[str] = []
    for t in turns[-settings.history_context_turns:]:
        if t.question:
            lines.append(f"Người dùng: {t.question}")
        if t.sql:
            lines.append(f"SQL đã dùng: {t.sql}")
    return "\n".join(lines) if lines else None


@router.post("/generate-sql", response_model=GenerateSQLResponse, summary="Sinh SQL từ câu hỏi")
async def generate_sql(req: GenerateSQLRequest) -> GenerateSQLResponse:
    try:
        outcome = _service.run(
            req.question, top_k=req.top_k, execute=req.execute, max_rows=req.max_rows
        )
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=f"LLM lỗi: {exc}") from exc

    resp = GenerateSQLResponse(
        question=outcome.question,
        sql=outcome.sql,
        validation=ValidationInfo(**TextToSQLService.to_validation_dict(outcome.validation)),
        tables=outcome.tables,
        schema_context=outcome.schema_context,
        latency_ms=outcome.latency_ms,
        executed=outcome.executed,
        error=outcome.error,
    )
    if outcome.result is not None:
        resp.columns = outcome.result.columns
        resp.rows = outcome.result.rows
        resp.row_count = outcome.result.row_count
        resp.execution_time_ms = outcome.result.execution_time_ms
        resp.truncated = outcome.result.truncated
    return resp


@router.post("/chart", response_model=ChartResponse, summary="Sinh biểu đồ + insight cho câu hỏi")
async def chart(req: ChartRequest) -> ChartResponse:
    """Chạy pipeline (sinh SQL + thực thi) rồi tạo Plotly config và AI Insight."""
    try:
        outcome = _service.run(
            req.question,
            top_k=req.top_k,
            execute=True,
            max_rows=req.max_rows,
            history=_format_history(req.history),
        )
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=f"LLM lỗi: {exc}") from exc

    resp = ChartResponse(question=req.question, sql=outcome.sql, error=outcome.error)
    if outcome.result is None:
        return resp  # bị guardrail chặn hoặc lỗi thực thi -> trả kèm error

    resp.columns = outcome.result.columns
    resp.rows = outcome.result.rows
    resp.row_count = outcome.result.row_count

    analysis = _analysis.analyze(
        req.question, outcome.result.dataframe, with_insight=req.with_insight
    )
    if analysis.chart is not None:
        c = analysis.chart
        resp.chart = ChartInfo(
            chart_type=c.chart_type, plotly=c.plotly, x=c.x, y=c.y,
            title=c.title, reason=c.reason,
        )
    if analysis.insight is not None:
        i = analysis.insight
        resp.insight = InsightInfo(
            summary=i.summary, highlights=i.highlights, stats=i.stats, llm_used=i.llm_used,
        )
    return resp
