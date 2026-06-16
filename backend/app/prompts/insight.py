"""Prompt cho Insight Agent — dùng ở Phase 5."""
from __future__ import annotations

INSIGHT_SYSTEM = """Bạn là chuyên gia phân tích kinh doanh. Dựa trên câu hỏi và bảng
kết quả truy vấn, đưa ra nhận định ngắn gọn, có số liệu, bằng tiếng Việt.
Tập trung: xu hướng, tăng/giảm, so sánh, giá trị nổi bật (cao nhất/thấp nhất), KPI.
Viết 2-4 câu súc tích, KHÔNG bịa số không có trong dữ liệu."""

INSIGHT_USER_TEMPLATE = """CÂU HỎI:
{question}

KẾT QUẢ (tóm tắt thống kê + vài dòng đầu):
{data_summary}

Hãy đưa ra phân tích insight ngắn gọn."""


def build_insight_prompt(question: str, data_summary: str) -> str:
    return INSIGHT_USER_TEMPLATE.format(question=question, data_summary=data_summary)
