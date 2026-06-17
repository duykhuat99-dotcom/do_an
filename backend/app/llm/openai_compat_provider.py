"""
Provider cho các endpoint tương thích OpenAI (vLLM, llama.cpp server, LM Studio,
hoặc OpenAI API). Cho phép chạy cùng các model mã nguồn mở qua chuẩn /v1/chat/completions.

Cấu hình qua `.env`: LLM_BASE_URL (vd http://localhost:8001/v1), LLM_API_KEY, LLM_MODEL.
"""
from __future__ import annotations

import time
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import settings
from app.llm.base import LLMError, LLMProviderInterface, LLMRateLimitError, LLMResponse
from app.utils import get_logger

logger = get_logger(__name__)


class OpenAICompatProvider(LLMProviderInterface):
    name = "openai_compat"

    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
        timeout: int | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(model or settings.llm_model)
        self.base_url = (base_url or settings.llm_base_url).rstrip("/")
        self.api_key = api_key or settings.llm_api_key or "not-needed"
        self.timeout = timeout or settings.llm_timeout

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type(httpx.TransportError),  # KHÔNG retry 429 -> fail-fast để fallback
    )
    def _post_chat(self, payload: dict) -> dict:
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=self._headers(),
            )
            resp.raise_for_status()
            return resp.json()

    def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        stop: list[str] | None = None,
    ) -> LLMResponse:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": settings.llm_temperature if temperature is None else temperature,
            "max_tokens": max_tokens or settings.llm_max_tokens,
            "stream": False,
        }
        if stop:
            payload["stop"] = stop

        start = time.perf_counter()
        try:
            data = self._post_chat(payload)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 429:
                logger.warning("Provider hết hạn mức (429): %s", self.base_url)
                raise LLMRateLimitError(f"Hết hạn mức (429) tại {self.base_url}") from exc
            logger.error("OpenAI-compat lỗi HTTP %s", exc.response.status_code)
            raise LLMError(f"Gọi LLM thất bại (HTTP {exc.response.status_code})") from exc
        except httpx.HTTPError as exc:
            logger.error("OpenAI-compat generate lỗi: %s", exc)
            raise LLMError(f"Gọi LLM thất bại: {exc}") from exc

        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        try:
            text = data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError) as exc:
            raise LLMError(f"Phản hồi LLM không hợp lệ: {data}") from exc

        usage = data.get("usage", {})
        return LLMResponse(
            text=text,
            model=data.get("model", self.model),
            provider=self.name,
            latency_ms=latency_ms,
            prompt_tokens=usage.get("prompt_tokens"),
            completion_tokens=usage.get("completion_tokens"),
            raw=data,
        )

    def health_check(self) -> dict[str, Any]:
        try:
            with httpx.Client(timeout=10) as client:
                resp = client.get(f"{self.base_url}/models", headers=self._headers())
                resp.raise_for_status()
            return {
                "healthy": True,
                "provider": self.name,
                "model": self.model,
                "base_url": self.base_url,
                "detail": "Kết nối LLM OK",
            }
        except httpx.HTTPError as exc:
            logger.warning("OpenAI-compat health_check thất bại: %s", exc)
            return {
                "healthy": False,
                "provider": self.name,
                "model": self.model,
                "base_url": self.base_url,
                "detail": str(exc),
            }
