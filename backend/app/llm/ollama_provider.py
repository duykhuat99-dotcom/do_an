"""
Provider chạy LLM mã nguồn mở qua Ollama (local).

Hỗ trợ: Mistral 7B Instruct, Llama 3 8B Instruct, Gemma 2B — cấu hình qua `.env`
(LLM_MODEL, LLM_BASE_URL). Dùng HTTP API /api/generate của Ollama.
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
from app.llm.base import LLMError, LLMProviderInterface, LLMResponse
from app.utils import get_logger

logger = get_logger(__name__)


class OllamaProvider(LLMProviderInterface):
    name = "ollama"

    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
        timeout: int | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(model or settings.llm_model)
        self.base_url = (base_url or settings.llm_base_url).rstrip("/")
        self.timeout = timeout or settings.llm_timeout

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type((httpx.TransportError, httpx.HTTPStatusError)),
    )
    def _post_generate(self, payload: dict) -> dict:
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(f"{self.base_url}/api/generate", json=payload)
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
        options: dict[str, Any] = {
            "temperature": settings.llm_temperature if temperature is None else temperature,
            "num_predict": max_tokens or settings.llm_max_tokens,
        }
        if stop:
            options["stop"] = stop

        payload: dict[str, Any] = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": options,
        }
        if system:
            payload["system"] = system

        start = time.perf_counter()
        try:
            data = self._post_generate(payload)
        except httpx.HTTPError as exc:
            logger.error("Ollama generate lỗi: %s", exc)
            raise LLMError(f"Gọi Ollama thất bại: {exc}") from exc

        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        text = (data.get("response") or "").strip()
        if not text:
            raise LLMError("Ollama trả về phản hồi rỗng")

        return LLMResponse(
            text=text,
            model=data.get("model", self.model),
            provider=self.name,
            latency_ms=latency_ms,
            prompt_tokens=data.get("prompt_eval_count"),
            completion_tokens=data.get("eval_count"),
            raw=data,
        )

    def health_check(self) -> dict[str, Any]:
        try:
            with httpx.Client(timeout=10) as client:
                resp = client.get(f"{self.base_url}/api/tags")
                resp.raise_for_status()
                models = [m["name"] for m in resp.json().get("models", [])]
            available = any(self.model.split(":")[0] in m for m in models)
            return {
                "healthy": True,
                "provider": self.name,
                "model": self.model,
                "base_url": self.base_url,
                "model_pulled": available,
                "available_models": models,
                "detail": "Kết nối Ollama OK"
                + ("" if available else f"; CHƯA pull model '{self.model}'"),
            }
        except httpx.HTTPError as exc:
            logger.warning("Ollama health_check thất bại: %s", exc)
            return {
                "healthy": False,
                "provider": self.name,
                "model": self.model,
                "base_url": self.base_url,
                "detail": str(exc),
            }
