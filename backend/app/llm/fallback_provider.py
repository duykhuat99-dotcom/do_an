"""
FallbackProvider — chuỗi provider dự phòng.

Thử lần lượt từng provider theo thứ tự; nếu provider hiện tại hết hạn mức (429,
LLMRateLimitError) hoặc lỗi (LLMError) thì tự động chuyển sang provider kế tiếp.
Provider cuối cùng (vd Ollama local) đóng vai "lưới an toàn" luôn sẵn sàng.

Ví dụ chuỗi: Groq -> OpenRouter -> Gemini -> Ollama local.
"""
from __future__ import annotations

from typing import Any

from app.llm.base import LLMError, LLMProviderInterface, LLMRateLimitError, LLMResponse
from app.utils import get_logger

logger = get_logger(__name__)


class FallbackProvider(LLMProviderInterface):
    name = "fallback"

    def __init__(self, providers: list[LLMProviderInterface]) -> None:
        if not providers:
            raise ValueError("FallbackProvider cần ít nhất 1 provider")
        self.providers = providers
        # 'model' tổng hợp để hiển thị/log.
        self.model = " -> ".join(f"{p.name}:{p.model}" for p in providers)

    def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        stop: list[str] | None = None,
    ) -> LLMResponse:
        last_err: Exception | None = None
        for i, provider in enumerate(self.providers):
            try:
                resp = provider.generate(
                    prompt,
                    system=system,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stop=stop,
                )
                if i > 0:
                    logger.info("Fallback: dùng provider dự phòng #%d (%s)", i + 1, provider.name)
                return resp
            except LLMRateLimitError as exc:
                logger.warning(
                    "Provider #%d (%s) hết hạn mức -> chuyển dự phòng", i + 1, provider.name
                )
                last_err = exc
            except LLMError as exc:
                logger.warning(
                    "Provider #%d (%s) lỗi: %s -> chuyển dự phòng", i + 1, provider.name, exc
                )
                last_err = exc
        raise last_err or LLMError("Tất cả provider trong chuỗi đều thất bại")

    def health_check(self) -> dict[str, Any]:
        checks = [p.health_check() for p in self.providers]
        return {
            "healthy": any(c.get("healthy") for c in checks),
            "provider": self.name,
            "chain": self.model,
            "detail": "Chuỗi fallback: " + ", ".join(
                f"{p.name}({'OK' if c.get('healthy') else 'X'})"
                for p, c in zip(self.providers, checks)
            ),
            "providers": checks,
        }
