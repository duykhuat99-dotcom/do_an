"""Schema cho pipeline Text-to-SQL (Phase 4)."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class GenerateSQLRequest(BaseModel):
    question: str = Field(..., min_length=1, examples=["Doanh thu theo chi nhánh năm 2024?"])
    top_k: int | None = Field(default=None, ge=1, le=50)
    execute: bool = Field(default=False, description="Có thực thi SQL và trả dữ liệu không")
    max_rows: int = Field(default=1000, ge=1, le=10000)


class ValidationInfo(BaseModel):
    safe: bool
    reason: str
    regex_passed: bool
    llm_checked: bool
    llm_safe: bool | None = None
    checks: dict[str, str] = Field(default_factory=dict)


class InsightInfo(BaseModel):
    summary: str
    highlights: list[str] = Field(default_factory=list)
    stats: dict[str, Any] = Field(default_factory=dict)
    llm_used: bool = False


class ChartInfo(BaseModel):
    chart_type: str
    plotly: dict[str, Any]
    x: str | None = None
    y: str | None = None
    title: str = ""
    reason: str = ""


class ChartRequest(BaseModel):
    question: str = Field(..., min_length=1, examples=["Doanh thu theo danh mục sản phẩm?"])
    top_k: int | None = Field(default=None, ge=1, le=50)
    max_rows: int = Field(default=1000, ge=1, le=10000)
    with_insight: bool = Field(default=True)


class ChartResponse(BaseModel):
    question: str
    sql: str
    columns: list[str] | None = None
    rows: list[dict[str, Any]] | None = None
    row_count: int | None = None
    chart: ChartInfo | None = None
    insight: InsightInfo | None = None
    error: str | None = None


class GenerateSQLResponse(BaseModel):
    question: str
    sql: str
    validation: ValidationInfo
    tables: list[str] = Field(default_factory=list)
    schema_context: str | None = None
    latency_ms: float = 0.0

    # Chỉ có khi execute=True và SQL an toàn
    executed: bool = False
    columns: list[str] | None = None
    rows: list[dict[str, Any]] | None = None
    row_count: int | None = None
    execution_time_ms: float | None = None
    truncated: bool | None = None
    error: str | None = None
