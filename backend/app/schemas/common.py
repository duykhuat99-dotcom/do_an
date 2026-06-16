"""Pydantic schema dùng chung cho nhiều endpoint."""
from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class HealthResponse(BaseModel):
    """Phản hồi cho endpoint /health."""

    status: str = Field(..., examples=["ok"])
    app_name: str
    app_env: str
    version: str


class ComponentStatus(BaseModel):
    """Trạng thái một thành phần hạ tầng (MySQL, VectorDB, LLM...)."""

    name: str
    healthy: bool
    detail: str | None = None


class APIResponse(BaseModel, Generic[T]):
    """Bao response chuẩn: {success, message, data}."""

    success: bool = True
    message: str = "OK"
    data: T | None = None


class ErrorResponse(BaseModel):
    """Định dạng lỗi trả về thống nhất cho toàn API."""

    success: bool = False
    error: str
    detail: Any | None = None
