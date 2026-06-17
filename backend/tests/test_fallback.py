"""Kiểm thử chuỗi fallback provider."""
import pytest

from app.llm.base import LLMError, LLMRateLimitError, LLMResponse
from app.llm.fallback_provider import FallbackProvider


class StubProvider:
    """Provider giả: trả kết quả hoặc ném lỗi định sẵn."""

    def __init__(self, name, *, raises=None, text=None):
        self.name = name
        self.model = f"{name}-model"
        self._raises = raises
        self._text = text

    def generate(self, prompt, *, system=None, temperature=None, max_tokens=None, stop=None):
        if self._raises:
            raise self._raises
        return LLMResponse(text=self._text, model=self.model, provider=self.name)

    def health_check(self):
        return {"healthy": self._raises is None}


def test_rate_limit_is_llm_error():
    assert issubclass(LLMRateLimitError, LLMError)


def test_uses_primary_when_ok():
    fb = FallbackProvider([StubProvider("groq", text="OK1"), StubProvider("ollama", text="OK2")])
    assert fb.generate("q").text == "OK1"


def test_falls_back_on_rate_limit():
    fb = FallbackProvider([
        StubProvider("groq", raises=LLMRateLimitError("429")),
        StubProvider("openrouter", raises=LLMRateLimitError("429")),
        StubProvider("ollama", text="LOCAL"),
    ])
    resp = fb.generate("q")
    assert resp.text == "LOCAL"
    assert resp.provider == "ollama"


def test_falls_back_on_generic_error():
    fb = FallbackProvider([
        StubProvider("groq", raises=LLMError("timeout")),
        StubProvider("ollama", text="LOCAL"),
    ])
    assert fb.generate("q").text == "LOCAL"


def test_raises_when_all_fail():
    fb = FallbackProvider([
        StubProvider("a", raises=LLMRateLimitError("429")),
        StubProvider("b", raises=LLMError("down")),
    ])
    with pytest.raises(LLMError):
        fb.generate("q")


def test_health_check_aggregates():
    fb = FallbackProvider([
        StubProvider("groq", raises=LLMRateLimitError("429")),
        StubProvider("ollama", text="X"),
    ])
    hc = fb.health_check()
    assert hc["healthy"] is True  # ollama còn sống
    assert "providers" in hc


def test_chain_config_parsing():
    from app.core.config import Settings

    s = Settings(llm_chain='[{"provider":"ollama","model":"qwen2.5:1.5b"}]')
    assert len(s.llm_chain_list) == 1
    assert s.llm_chain_list[0]["provider"] == "ollama"

    s2 = Settings(llm_chain="")
    assert s2.llm_chain_list == []

    s3 = Settings(llm_chain="khong-phai-json")
    assert s3.llm_chain_list == []
