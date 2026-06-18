"""Prompt cho SQL Agent (Text-to-SQL) — dùng ở Phase 4, có few-shot & tự sửa lỗi."""
from __future__ import annotations

SQL_SYSTEM = """Bạn là chuyên gia phân tích dữ liệu, viết câu lệnh SQL cho MySQL 8 trên
DataMart đặt tour (Star Schema). Nguyên tắc bắt buộc:
- CHỈ sinh DUY NHẤT một câu lệnh SELECT. Tuyệt đối KHÔNG dùng \
INSERT/UPDATE/DELETE/DROP/ALTER/TRUNCATE.
- Chỉ dùng các bảng và cột có trong NGỮ CẢNH SCHEMA được cung cấp. Không bịa tên bảng/cột.
- GIỮ NGUYÊN chữ hoa-thường của tên bảng/cột (PascalCase): FactBooking, DimDate,
  DimDestination, DimCustomerSegment, DimTour, các cột như DestinationKey, Revenue,
  Pax, SatisfactionScore... TUYỆT ĐỐI KHÔNG đổi sang chữ thường hay thêm dấu gạch dưới
  (vd KHÔNG viết fact_booking, destination_id).
- Khi lọc/gom theo năm/quý/tháng phải JOIN sang DimDate qua DateKey rồi dùng
  DimDate.YearNumber / QuarterNumber / MonthNumber.
- "Doanh thu" = SUM(FactBooking.Revenue); "lượng khách" = SUM(FactBooking.Pax);
  "số booking" = COUNT(*); "điểm hài lòng" = AVG(FactBooking.SatisfactionScore).
- Truy vấn liệt kê chi tiết nên có LIMIT hợp lý.
- Chỉ trả về câu SQL thuần, KHÔNG giải thích, KHÔNG markdown, KHÔNG ```."""

# Ví dụ mẫu (few-shot) — dùng đúng tên bảng/cột PascalCase của schema tour.
FEW_SHOT = """Câu hỏi: Doanh thu theo điểm đến?
SQL: SELECT d.DestinationName, SUM(f.Revenue) AS doanh_thu FROM FactBooking f \
JOIN DimDestination d ON f.DestinationKey = d.DestinationKey \
GROUP BY d.DestinationName ORDER BY doanh_thu DESC

Câu hỏi: Số booking theo loại tour?
SQL: SELECT t.TourName, COUNT(*) AS so_booking FROM FactBooking f \
JOIN DimTour t ON f.TourKey = t.TourKey GROUP BY t.TourName ORDER BY so_booking DESC

Câu hỏi: Doanh thu theo từng tháng năm 2024?
SQL: SELECT dt.MonthNumber, SUM(f.Revenue) AS doanh_thu FROM FactBooking f \
JOIN DimDate dt ON f.DateKey = dt.DateKey WHERE dt.YearNumber = 2024 \
GROUP BY dt.MonthNumber ORDER BY dt.MonthNumber

Câu hỏi: Điểm hài lòng trung bình theo nhóm khách?
SQL: SELECT s.SegmentName, AVG(f.SatisfactionScore) AS diem_hai_long FROM FactBooking f \
JOIN DimCustomerSegment s ON f.SegmentKey = s.SegmentKey GROUP BY s.SegmentName \
ORDER BY diem_hai_long DESC"""

SQL_USER_TEMPLATE = """NGỮ CẢNH SCHEMA (từ RAG):
{schema_context}

VÍ DỤ MẪU:
{few_shot}
{history_block}
CÂU HỎI NGƯỜI DÙNG:
{question}

Hãy viết câu lệnh SELECT MySQL phù hợp."""


def build_sql_prompt(question: str, schema_context: str, history: str | None = None) -> str:
    history_block = ""
    if history:
        history_block = (
            "\nLỊCH SỬ HỘI THOẠI GẦN ĐÂY (dùng để hiểu câu hỏi nối tiếp, vd 'thế còn quý 2?'):\n"
            f"{history}\n"
        )
    return SQL_USER_TEMPLATE.format(
        schema_context=schema_context,
        few_shot=FEW_SHOT,
        history_block=history_block,
        question=question,
    )


# ----- Tự sửa lỗi SQL (self-correction) -----
SQL_FIX_SYSTEM = """Bạn là chuyên gia SQL MySQL. Câu lệnh SQL trước đó chạy bị LỖI.
Hãy SỬA LẠI dựa trên thông báo lỗi từ MySQL. Vẫn chỉ dùng bảng/cột có trong ngữ cảnh
schema, chỉ sinh câu SELECT. Chỉ trả về câu SQL đã sửa — KHÔNG giải thích, KHÔNG markdown."""

SQL_FIX_TEMPLATE = """NGỮ CẢNH SCHEMA:
{schema_context}

CÂU HỎI: {question}

CÂU SQL BỊ LỖI:
{bad_sql}

THÔNG BÁO LỖI TỪ MYSQL:
{error}

Hãy sửa lại câu lệnh SELECT cho đúng cú pháp/đúng tên bảng-cột."""


def build_fix_prompt(question: str, schema_context: str, bad_sql: str, error: str) -> str:
    return SQL_FIX_TEMPLATE.format(
        schema_context=schema_context, question=question, bad_sql=bad_sql, error=error
    )
