"""Kiểm thử Nhóm 1: few-shot, multi-turn, self-correction (dùng LLM giả)."""
from app.agents.sql_agent import SQLAgent
from app.llm.base import LLMResponse
from app.prompts.sql import build_fix_prompt, build_sql_prompt


class FakeLLM:
    def __init__(self, text):
        self.text = text
        self.model = "fake"
        self.last_prompt = None
        self.last_system = None

    def generate(self, prompt, *, system=None, temperature=None, max_tokens=None, stop=None):
        self.last_prompt = prompt
        self.last_system = system
        return LLMResponse(text=self.text, model="fake", provider="fake")

    def health_check(self):
        return {"healthy": True}


def test_prompt_has_fewshot():
    p = build_sql_prompt("Doanh thu?", "[table] FactBooking")
    assert "VÍ DỤ MẪU" in p
    assert "FactBooking" in p


def test_prompt_includes_history_when_given():
    p = build_sql_prompt("Thế còn quý 2?", "[table] fact_sales", history="Người dùng: Doanh thu quý 1?")
    assert "LỊCH SỬ HỘI THOẠI" in p
    assert "quý 1" in p


def test_prompt_no_history_block_when_empty():
    p = build_sql_prompt("Doanh thu?", "ctx", history=None)
    assert "LỊCH SỬ HỘI THOẠI" not in p


def test_fix_prompt_contains_error():
    p = build_fix_prompt("Doanh thu?", "ctx", "SELECT * FROM sai_bang", "Table 'sai_bang' doesn't exist")
    assert "sai_bang" in p
    assert "doesn't exist" in p


def test_sql_agent_generate_with_history():
    llm = FakeLLM("SELECT 1")
    agent = SQLAgent(llm=llm)
    agent.generate("Thế còn quý 2?", "ctx", history="Người dùng: Doanh thu quý 1?")
    assert "LỊCH SỬ HỘI THOẠI" in llm.last_prompt


def test_sql_agent_fix_returns_clean_sql():
    llm = FakeLLM("```sql\nSELECT * FROM fact_sales LIMIT 5\n```")
    agent = SQLAgent(llm=llm)
    out = agent.fix("Doanh thu?", "ctx", "SELECT * FROM sai", "error")
    assert out.sql == "SELECT * FROM fact_sales LIMIT 5"
