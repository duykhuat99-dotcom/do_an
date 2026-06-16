"""
Validation Agent (Agent #3) — Guardrail.

Hai tầng phòng thủ trước khi cho phép thực thi SQL:
  1. REGEX (bắt buộc, quyết định): chặn tuyệt đối mọi thao tác ghi/phá hoại
     (DROP, DELETE, TRUNCATE, ALTER, UPDATE, INSERT, CREATE, ...), chặn nhiều câu
     lệnh nối nhau và comment khả nghi; chỉ chấp nhận câu bắt đầu bằng SELECT/WITH.
  2. LLM (best-effort, bổ sung): nhờ LLM soát lại ý đồ. LLM CHỈ có thể siết thêm
     (đánh dấu không an toàn), không thể nới lỏng kết quả của regex. Nếu LLM lỗi/
     không sẵn sàng thì bỏ qua, vẫn dựa trên regex.

Tầng phòng thủ thứ ba (ngoài agent này) là tài khoản MySQL chỉ-đọc khi thực thi.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from app.llm import LLMError, get_llm
from app.llm.base import LLMProviderInterface
from app.prompts import VALIDATION_SYSTEM, build_validation_prompt
from app.utils import get_logger

logger = get_logger(__name__)

# Từ khóa bị cấm tuyệt đối (so khớp theo ranh giới từ, không phân biệt hoa thường).
FORBIDDEN_KEYWORDS = [
    "DROP", "DELETE", "TRUNCATE", "ALTER", "UPDATE", "INSERT", "CREATE",
    "REPLACE", "MERGE", "GRANT", "REVOKE", "EXEC", "EXECUTE", "CALL",
    "ATTACH", "RENAME", "LOCK", "UNLOCK", "SHUTDOWN", "HANDLER",
]
_FORBIDDEN_RE = re.compile(
    r"\b(" + "|".join(FORBIDDEN_KEYWORDS) + r")\b", re.IGNORECASE
)
# Cụm nguy hiểm dù không đứng riêng thành từ.
_DANGEROUS_PHRASES = [
    r"into\s+outfile", r"into\s+dumpfile", r"load_file\s*\(",
    r"load\s+data", r"set\s+@", r"information_schema", r"sleep\s*\(",
    r"benchmark\s*\(",
]
_DANGEROUS_RE = re.compile("|".join(_DANGEROUS_PHRASES), re.IGNORECASE)
_COMMENT_RE = re.compile(r"(--|#|/\*)")
_STARTS_OK_RE = re.compile(r"^\s*(WITH|SELECT)\b", re.IGNORECASE)


@dataclass
class ValidationResult:
    safe: bool
    reason: str
    regex_passed: bool = False
    llm_checked: bool = False
    llm_safe: bool | None = None
    checks: dict = field(default_factory=dict)


class ValidationAgent:
    def __init__(self, llm: LLMProviderInterface | None = None, use_llm: bool = True) -> None:
        self._llm = llm
        self.use_llm = use_llm

    @property
    def llm(self) -> LLMProviderInterface:
        return self._llm or get_llm()

    # ---------- Tầng 1: Regex ----------
    def regex_check(self, sql: str) -> tuple[bool, str]:
        if not sql or not sql.strip():
            return False, "Câu SQL rỗng."

        if not _STARTS_OK_RE.match(sql):
            return False, "Chỉ cho phép câu lệnh bắt đầu bằng SELECT hoặc WITH."

        # Chặn nhiều câu lệnh nối nhau (stacked queries).
        if ";" in sql.strip().rstrip(";"):
            return False, "Phát hiện nhiều câu lệnh nối nhau (stacked queries)."

        if _COMMENT_RE.search(sql):
            return False, "Câu SQL chứa comment khả nghi (--, #, /*)."

        m = _FORBIDDEN_RE.search(sql)
        if m:
            return False, f"Phát hiện từ khóa bị cấm: {m.group(1).upper()}."

        m2 = _DANGEROUS_RE.search(sql)
        if m2:
            return False, f"Phát hiện cú pháp nguy hiểm: {m2.group(0)}."

        return True, "Vượt qua kiểm tra regex."

    # ---------- Tầng 2: LLM ----------
    def llm_check(self, sql: str) -> tuple[bool, str]:
        prompt = build_validation_prompt(sql)
        resp = self.llm.generate(prompt, system=VALIDATION_SYSTEM, max_tokens=200)
        data = _extract_json(resp.text)
        if data is None:
            # Không parse được -> thận trọng coi như không kết luận được (an toàn theo regex).
            logger.warning("LLM validation không trả JSON hợp lệ: %s", resp.text[:120])
            return True, "LLM không kết luận rõ (bỏ qua, dựa regex)."
        safe = bool(data.get("safe", False))
        return safe, str(data.get("reason", ""))

    # ---------- Tổng hợp ----------
    def validate(self, sql: str) -> ValidationResult:
        regex_ok, regex_reason = self.regex_check(sql)
        result = ValidationResult(
            safe=regex_ok,
            reason=regex_reason,
            regex_passed=regex_ok,
            checks={"regex": regex_reason},
        )
        if not regex_ok:
            logger.warning("Guardrail CHẶN (regex): %s | SQL=%s", regex_reason, sql[:120])
            return result  # regex đã chặn, không cần hỏi LLM

        if not self.use_llm:
            return result

        try:
            llm_safe, llm_reason = self.llm_check(sql)
            result.llm_checked = True
            result.llm_safe = llm_safe
            result.checks["llm"] = llm_reason
            if not llm_safe:
                result.safe = False
                result.reason = f"LLM đánh giá không an toàn: {llm_reason}"
                logger.warning("Guardrail CHẶN (LLM): %s", llm_reason)
        except LLMError as exc:
            # LLM không sẵn sàng -> vẫn dựa vào regex (đã pass).
            logger.warning("Bỏ qua LLM check (lỗi LLM): %s", exc)
            result.checks["llm"] = f"bỏ qua: {exc}"
        return result


def _extract_json(text: str) -> dict | None:
    """Trích object JSON đầu tiên trong chuỗi (LLM hay kèm chữ thừa)."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
