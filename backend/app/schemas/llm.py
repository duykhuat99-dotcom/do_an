"""Schema cho endpoint kiểm thử LLM."""
from __future__ import annotations

from pydantic import BaseModel, Field


class LLMTestRequest(BaseModel):
    prompt: str = Field(..., min_length=1, examples=["Chào bạn, giới thiệu ngắn gọn."])
    system: str | None = Field(default=None)
    max_tokens: int | None = Field(default=128, ge=1, le=4096)


class LLMTestResponse(BaseModel):
    provider: str
    model: str
    text: str
    latency_ms: float
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
