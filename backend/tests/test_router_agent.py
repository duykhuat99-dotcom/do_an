"""Kiểm thử Router Agent với LLM giả (không gọi mô hình thật)."""
from app.agents.router_agent import RouterAgent
from app.llm.base import LLMResponse


class FakeLLM:
    """LLM giả trả về text cố định để test phân loại."""

    def __init__(self, text: str) -> None:
        self.text = text
        self.model = "fake"

    def generate(self, prompt, *, system=None, temperature=None, max_tokens=None, stop=None):
        return LLMResponse(text=self.text, model="fake", provider="fake")

    def health_check(self):
        return {"healthy": True}


def test_classify_general():
    agent = RouterAgent(llm=FakeLLM('{"type": "general"}'))
    assert agent.classify("Hôm nay là ngày nào?") == "general"


def test_classify_data():
    agent = RouterAgent(llm=FakeLLM('{"type": "data"}'))
    assert agent.classify("Doanh thu theo chi nhánh?") == "data"


def test_classify_unparseable_defaults_data():
    # LLM trả rác -> mặc định 'data' (an toàn, vẫn qua guardrail)
    agent = RouterAgent(llm=FakeLLM("không rõ"))
    assert agent.classify("abc") == "data"


def test_classify_disabled():
    agent = RouterAgent(llm=FakeLLM('{"type": "general"}'), enabled=False)
    assert agent.classify("Hôm nay là ngày nào?") == "data"


def test_answer_general_returns_text():
    agent = RouterAgent(llm=FakeLLM("Hôm nay là Thứ Hai."))
    assert "Thứ Hai" in agent.answer_general("Hôm nay thứ mấy?")
