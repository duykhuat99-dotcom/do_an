"""Prompt cho gợi ý câu hỏi tiếp theo."""
from __future__ import annotations

SUGGEST_SYSTEM = """Bạn là trợ lý phân tích dữ liệu ĐẶT TOUR DU LỊCH. Dựa trên câu hỏi và
câu trả lời vừa rồi, hãy đề xuất 3 câu hỏi TIẾP THEO ngắn gọn, liên quan, mà người dùng có
thể muốn hỏi tiếp về dữ liệu (doanh thu, lượng khách, số booking, điểm hài lòng theo điểm đến,
nhóm khách, loại tour, thời gian).
Yêu cầu: tiếng Việt, mỗi câu DƯỚI 12 từ, là câu hỏi phân tích dữ liệu.
Trả về DUY NHẤT JSON: {"suggestions": ["...", "...", "..."]} — không thêm chữ nào khác."""

SUGGEST_TEMPLATE = """Câu hỏi: {question}
Câu trả lời: {answer}

Đề xuất 3 câu hỏi phân tích tiếp theo."""


def build_suggest_prompt(question: str, answer: str) -> str:
    return SUGGEST_TEMPLATE.format(question=question, answer=(answer or "")[:500])
