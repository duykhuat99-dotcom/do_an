"""Kiểm thử làm sạch SQL từ output thô của LLM."""
from app.agents.sql_agent import SQLAgent


def test_strip_markdown_fences():
    raw = "```sql\nSELECT * FROM dim_product LIMIT 5;\n```"
    assert SQLAgent.clean_sql(raw) == "SELECT * FROM dim_product LIMIT 5"


def test_strip_prefix_and_explanation():
    raw = "Câu lệnh: SELECT id FROM dim_branch"
    assert SQLAgent.clean_sql(raw) == "SELECT id FROM dim_branch"


def test_extract_select_from_text():
    raw = "Đây là truy vấn phù hợp:\nSELECT COUNT(*) FROM fact_sales"
    assert SQLAgent.clean_sql(raw) == "SELECT COUNT(*) FROM fact_sales"


def test_keep_with_cte():
    raw = "```\nWITH t AS (SELECT 1) SELECT * FROM t\n```"
    assert SQLAgent.clean_sql(raw).startswith("WITH t AS")
