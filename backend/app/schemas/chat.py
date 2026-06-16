"""Schema cho hội thoại chính (/chat) và lịch sử (/history)."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.schemas.query import ChartInfo, InsightInfo, ValidationInfo


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, examples=["Doanh thu theo chi nhánh năm 2024?"])
    session_id: str | None = Field(default=None, description="Bỏ trống để tạo phiên mới")
    top_k: int | None = Field(default=None, ge=1, le=50)
    max_rows: int = Field(default=1000, ge=1, le=10000)
    with_chart: bool = Field(default=True)


class ChatResponse(BaseModel):
    session_id: str
    question: str
    answer: str
    mode: str = "data"  # "data" (truy vấn DataMart) | "general" (câu hỏi thường)
    sql: str = ""
    validation: ValidationInfo
    tables: list[str] = Field(default_factory=list)
    columns: list[str] | None = None
    rows: list[dict[str, Any]] | None = None
    row_count: int | None = None
    insight: InsightInfo | None = None
    chart: ChartInfo | None = None
    execution_time_ms: float | None = None
    total_time_ms: float = 0.0
    success: bool = False
    error: str | None = None


class HistoryRequest(BaseModel):
    session_id: str = Field(..., min_length=1)
    limit: int = Field(default=20, ge=1, le=200)


class HistoryItem(BaseModel):
    id: int
    role: str
    question: str | None = None
    answer: str | None = None
    generated_sql: str | None = None
    chart: dict[str, Any] | None = None
    insight: dict[str, Any] | None = None
    created_at: str | None = None


class HistoryResponse(BaseModel):
    session_id: str
    count: int
    history: list[HistoryItem] = Field(default_factory=list)


class SuggestRequest(BaseModel):
    question: str = Field(..., min_length=1)
    answer: str | None = None


class SuggestResponse(BaseModel):
    suggestions: list[str] = Field(default_factory=list)


class SessionItem(BaseModel):
    session_id: str
    title: str
    last_at: str | None = None
    message_count: int


class SessionListResponse(BaseModel):
    count: int
    sessions: list[SessionItem] = Field(default_factory=list)


class FeedbackRequest(BaseModel):
    rating: str = Field(..., pattern="^(up|down)$")
    question: str | None = None
    answer: str | None = None
    session_id: str | None = None


class TopQuestion(BaseModel):
    question: str | None = None
    count: int


class DayStat(BaseModel):
    date: str
    total: int
    success: int


class StatsResponse(BaseModel):
    total_queries: int
    success_count: int
    success_rate: float
    avg_execution_ms: float
    feedback_up: int
    feedback_down: int
    top_questions: list[TopQuestion] = Field(default_factory=list)
    by_day: list[DayStat] = Field(default_factory=list)


class ComponentHealth(BaseModel):
    healthy: bool
    detail: str | None = None
    info: dict[str, Any] = Field(default_factory=dict)


class SystemStatusResponse(BaseModel):
    mysql: ComponentHealth
    vector_db: ComponentHealth
    llm: ComponentHealth
