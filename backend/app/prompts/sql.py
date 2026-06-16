"""Prompt cho SQL Agent (Text-to-SQL) — dùng ở Phase 4, có few-shot & tự sửa lỗi."""
from __future__ import annotations

SQL_SYSTEM = """Bạn là chuyên gia phân tích dữ liệu, viết câu lệnh SQL cho MySQL 8.
Nguyên tắc bắt buộc:
- CHỈ sinh DUY NHẤT một câu lệnh SELECT. Tuyệt đối KHÔNG dùng \
INSERT/UPDATE/DELETE/DROP/ALTER/TRUNCATE.
- Chỉ dùng các bảng và cột có trong NGỮ CẢNH SCHEMA được cung cấp. Không bịa tên bảng/cột.
- Khi lọc theo năm/quý/tháng phải JOIN sang dim_time qua time_id.
- "Doanh thu" = SUM(fact_sales.total_amount). Tuân thủ các quy tắc nghiệp vụ trong ngữ cảnh.
- Truy vấn liệt kê chi tiết nên có LIMIT hợp lý.
- Chỉ trả về câu SQL thuần, KHÔNG giải thích, KHÔNG markdown, KHÔNG ```."""

# Ví dụ mẫu (few-shot) giúp LLM bám đúng phong cách JOIN/GROUP BY trên schema này.
FEW_SHOT = """Câu hỏi: Doanh thu theo chi nhánh năm 2024?
SQL: SELECT b.branch_name, SUM(f.total_amount) AS doanh_thu FROM fact_sales f \
JOIN dim_branch b ON f.branch_id=b.branch_id JOIN dim_time t ON f.time_id=t.time_id \
WHERE t.year=2024 GROUP BY b.branch_name ORDER BY doanh_thu DESC

Câu hỏi: Top 5 sản phẩm bán chạy nhất?
SQL: SELECT p.product_name, SUM(f.quantity) AS so_luong FROM fact_sales f \
JOIN dim_product p ON f.product_id=p.product_id GROUP BY p.product_name \
ORDER BY so_luong DESC LIMIT 5

Câu hỏi: Liệt kê nhiệm vụ đang quá hạn?
SQL: SELECT TenNhiemVu, DonViChuTri, SoNgayQuaHan FROM qlnv_chitiet \
WHERE SoNgayQuaHan > 0 ORDER BY SoNgayQuaHan DESC LIMIT 100"""

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
