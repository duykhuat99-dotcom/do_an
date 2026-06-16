"""
Router Agent — phân loại ý định câu hỏi và trả lời câu hỏi thường.

  - classify(question) -> "data" | "general"
        "data"    : cần truy vấn DataMart (đi tiếp pipeline Text-to-SQL).
        "general" : câu hỏi thường/trò chuyện (trả lời trực tiếp bằng LLM).
  - answer_general(question) -> câu trả lời tự nhiên (chèn ngày hiện tại).

Nếu LLM lỗi khi phân loại -> mặc định coi là "data" (an toàn: vẫn qua guardrail).
"""
from __future__ import annotations

from datetime import datetime

from app.agents.validation_agent import _extract_json
from app.llm import LLMError, get_llm
from app.llm.base import LLMProviderInterface
from app.prompts import GENERAL_SYSTEM, ROUTER_SYSTEM, build_router_prompt
from app.utils import get_logger

logger = get_logger(__name__)


class RouterAgent:
    def __init__(self, llm: LLMProviderInterface | None = None, enabled: bool = True) -> None:
        self._llm = llm
        self.enabled = enabled

    @property
    def llm(self) -> LLMProviderInterface:
        return self._llm or get_llm()

    def classify(self, question: str) -> str:
        """Phân loại 'data' | 'general'."""
        if not self.enabled:
            return "data"
        try:
            resp = self.llm.generate(
                build_router_prompt(question), system=ROUTER_SYSTEM, max_tokens=20
            )
            data = _extract_json(resp.text)
            if data and data.get("type") in ("data", "general"):
                logger.info("Router: '%s' -> %s", question[:50], data["type"])
                return data["type"]
            # Không parse được -> đoán theo nội dung thô.
            if "general" in resp.text.lower():
                return "general"
        except LLMError as exc:
            logger.warning("Router lỗi LLM, mặc định 'data': %s", exc)
        return "data"

    def answer_general(self, question: str) -> str:
        """Trả lời câu hỏi thường bằng LLM (chèn ngày hiện tại vào system prompt)."""
        today = datetime.now().strftime("%A, %d/%m/%Y")
        system = GENERAL_SYSTEM.format(today=today)
        try:
            resp = self.llm.generate(question, system=system, max_tokens=400)
            return resp.text.strip() or "Xin lỗi, mình chưa trả lời được câu này."
        except LLMError as exc:
            logger.warning("answer_general lỗi LLM: %s", exc)
            return f"Xin lỗi, hiện chưa trả lời được do lỗi mô hình: {exc}"
