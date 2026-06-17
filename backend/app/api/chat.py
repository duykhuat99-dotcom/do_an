"""
Router hội thoại chính & lịch sử.

  - POST /chat    : một lượt hỏi-đáp đầy đủ (điều phối 6 agent qua Orchestrator).
  - POST /history : lấy lịch sử hội thoại theo session_id.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.agents.validation_agent import _extract_json
from app.llm import LLMError, get_llm
from app.prompts import SUGGEST_SYSTEM, build_suggest_prompt
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    FeedbackRequest,
    HistoryRequest,
    HistoryResponse,
    RenameSessionRequest,
    SessionListResponse,
    StatsResponse,
    SuggestRequest,
    SuggestResponse,
)
from app.schemas.query import ChartInfo, InsightInfo, ValidationInfo
from app.services.orchestrator import ChatResult, Orchestrator
from app.utils import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["chat"])

_orchestrator = Orchestrator()


def _to_response(r: ChatResult) -> ChatResponse:
    resp = ChatResponse(
        session_id=r.session_id,
        question=r.question,
        answer=r.answer,
        mode=r.mode,
        sql=r.sql,
        validation=ValidationInfo(**r.validation),
        tables=r.tables,
        columns=r.columns,
        rows=r.rows,
        row_count=r.row_count,
        execution_time_ms=r.execution_time_ms,
        total_time_ms=r.total_time_ms,
        success=r.success,
        error=r.error,
    )
    if r.insight is not None:
        resp.insight = InsightInfo(
            summary=r.insight.summary,
            highlights=r.insight.highlights,
            stats=r.insight.stats,
            llm_used=r.insight.llm_used,
        )
    if r.chart is not None:
        resp.chart = ChartInfo(
            chart_type=r.chart.chart_type,
            plotly=r.chart.plotly,
            x=r.chart.x,
            y=r.chart.y,
            title=r.chart.title,
            reason=r.chart.reason,
        )
    return resp


@router.post("/chat", response_model=ChatResponse, summary="Hội thoại chính (full pipeline)")
async def chat(req: ChatRequest) -> ChatResponse:
    try:
        result = _orchestrator.process_chat(
            req.question,
            session_id=req.session_id,
            top_k=req.top_k,
            max_rows=req.max_rows,
            with_chart=req.with_chart,
        )
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=f"LLM lỗi: {exc}") from exc
    return _to_response(result)


@router.post("/history", response_model=HistoryResponse, summary="Lấy lịch sử hội thoại")
async def history(req: HistoryRequest) -> HistoryResponse:
    items = _orchestrator.get_history(req.session_id, limit=req.limit)
    return HistoryResponse(session_id=req.session_id, count=len(items), history=items)


@router.get("/sessions", response_model=SessionListResponse, summary="Liệt kê các cuộc trò chuyện")
async def sessions(limit: int = 50) -> SessionListResponse:
    items = _orchestrator.list_sessions(limit=limit)
    return SessionListResponse(count=len(items), sessions=items)


@router.patch("/sessions/{session_id}", summary="Đổi tên cuộc trò chuyện")
async def rename_session(session_id: str, req: RenameSessionRequest) -> dict[str, bool]:
    return {"success": _orchestrator.rename_session(session_id, req.title)}


@router.delete("/sessions/{session_id}", summary="Xóa cuộc trò chuyện")
async def delete_session(session_id: str) -> dict[str, bool]:
    return {"success": _orchestrator.delete_session(session_id)}


@router.get("/stats", response_model=StatsResponse, summary="Thống kê truy vấn (admin)")
async def stats() -> StatsResponse:
    """Tổng hợp số liệu từ query_log + feedback cho trang quản trị."""
    return StatsResponse(**_orchestrator.get_stats())


@router.post("/feedback", summary="Đánh giá câu trả lời (👍/👎)")
async def feedback(req: FeedbackRequest) -> dict[str, bool]:
    ok = _orchestrator.save_feedback(req.rating, req.question, req.answer, req.session_id)
    return {"success": ok}


@router.post("/suggest-questions", response_model=SuggestResponse, summary="Gợi ý câu hỏi tiếp theo")
async def suggest_questions(req: SuggestRequest) -> SuggestResponse:
    """Sinh 3 câu hỏi gợi ý tiếp theo (1 lần gọi LLM). Lỗi -> trả danh sách rỗng."""
    try:
        resp = get_llm().generate(
            build_suggest_prompt(req.question, req.answer or ""),
            system=SUGGEST_SYSTEM,
            max_tokens=150,
        )
        data = _extract_json(resp.text)
        items = data.get("suggestions") if isinstance(data, dict) else None
        suggestions = [str(s).strip() for s in items][:3] if isinstance(items, list) else []
    except LLMError as exc:
        logger.warning("Gợi ý câu hỏi lỗi LLM: %s", exc)
        suggestions = []
    return SuggestResponse(suggestions=suggestions)
