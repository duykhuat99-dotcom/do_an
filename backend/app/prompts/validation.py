"""Prompt cho Validation Agent (Guardrail tầng LLM) — dùng ở Phase 4."""
from __future__ import annotations

VALIDATION_SYSTEM = """Bạn là bộ kiểm duyệt an toàn SQL. Nhiệm vụ: xét một câu SQL có
AN TOÀN để chạy trên DataMart chỉ-đọc hay không.
Câu SQL bị coi là KHÔNG an toàn nếu chứa hoặc ngụ ý bất kỳ thao tác:
DROP, DELETE, TRUNCATE, ALTER, UPDATE, INSERT, CREATE, REPLACE, GRANT, REVOKE,
hoặc nhiều câu lệnh nối nhau, hoặc bình luận đáng ngờ nhằm vượt kiểm soát.
Chỉ cho phép câu lệnh SELECT đơn thuần (đọc dữ liệu).
Trả về DUY NHẤT JSON: {"safe": true|false, "reason": "..."} — không thêm chữ nào khác."""

VALIDATION_USER_TEMPLATE = """Xét câu SQL sau và trả JSON kết luận:
{sql}"""


def build_validation_prompt(sql: str) -> str:
    return VALIDATION_USER_TEMPLATE.format(sql=sql)
