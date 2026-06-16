"""Prompt cho Visualization Agent — dùng ở Phase 5."""
from __future__ import annotations

CHART_SYSTEM = """Bạn là chuyên gia trực quan hóa dữ liệu. Dựa trên câu hỏi và cấu trúc
bảng kết quả, chọn loại biểu đồ phù hợp nhất trong: bar, line, pie, area, scatter.
Quy tắc gợi ý: chuỗi thời gian -> line/area; so sánh hạng mục -> bar; tỷ trọng -> pie;
quan hệ hai biến số -> scatter.
Trả về DUY NHẤT JSON: {"chart_type": "...", "x": "<tên cột>", "y": "<tên cột>",
"title": "..."} — không thêm chữ nào khác."""

CHART_USER_TEMPLATE = """CÂU HỎI:
{question}

CÁC CỘT KẾT QUẢ: {columns}
VÀI DÒNG MẪU:
{sample_rows}

Hãy chọn cấu hình biểu đồ phù hợp (JSON)."""


def build_chart_prompt(question: str, columns: list[str], sample_rows: str) -> str:
    return CHART_USER_TEMPLATE.format(
        question=question, columns=", ".join(columns), sample_rows=sample_rows
    )
