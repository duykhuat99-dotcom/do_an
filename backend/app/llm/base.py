"""
Interface trừu tượng cho mọi LLM Provider.

Mọi agent chỉ phụ thuộc vào `LLMProviderInterface`, không biết provider cụ thể.
Nhờ đó đổi model/nhà cung cấp chỉ bằng cách chỉnh `.env` (xem llm/factory.py).
"""
from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any


class LLMError(RuntimeError):
    """Lỗi khi gọi LLM (kết nối, timeout, phản hồi không hợp lệ...)."""


class LLMRateLimitError(LLMError):
    """Lỗi hết hạn mức / quá tải (HTTP 429). Dùng để kích hoạt fallback sang provider khác."""


@dataclass
class LLMResponse:
    """Kết quả sinh văn bản chuẩn hóa từ mọi provider."""

    text: str
    model: str
    provider: str
    latency_ms: float = 0.0
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    raw: dict[str, Any] = field(default_factory=dict)


class LLMProviderInterface(abc.ABC):
    """Hợp đồng chung cho các nhà cung cấp LLM."""

    #: Tên provider (vd 'ollama', 'openai_compat')
    name: str = "base"

    def __init__(self, model: str, **kwargs: Any) -> None:
        self.model = model

    @abc.abstractmethod
    def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        stop: list[str] | None = None,
    ) -> LLMResponse:
        """Sinh văn bản từ một prompt (kèm system prompt tùy chọn)."""
        raise NotImplementedError

    @abc.abstractmethod
    def health_check(self) -> dict[str, Any]:
        """Kiểm tra kết nối tới LLM. Trả về dict mô tả trạng thái (không ném lỗi)."""
        raise NotImplementedError
