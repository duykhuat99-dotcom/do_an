"""Kiểm thử Validation Agent (guardrail) — tầng an toàn quan trọng nhất."""
import pytest

from app.agents.validation_agent import ValidationAgent

va = ValidationAgent(use_llm=False)

MALICIOUS = [
    "DROP TABLE fact_sales",
    "SELECT * FROM dim_product; DELETE FROM dim_product",
    "SELECT * FROM x WHERE 1=1 -- comment",
    "UPDATE dim_product SET unit_price=0",
    "INSERT INTO dim_product VALUES (1)",
    "TRUNCATE TABLE fact_sales",
    "ALTER TABLE fact_sales ADD col INT",
    "SELECT load_file('/etc/passwd')",
    "SELECT * FROM dim_product INTO OUTFILE '/tmp/x'",
    "SELECT * FROM information_schema.tables",
    "REPLACE INTO dim_product VALUES (1)",
    "GRANT ALL ON datamart.* TO 'x'@'%'",
]

SAFE = [
    "SELECT category, SUM(total_amount) FROM fact_sales f "
    "JOIN dim_product p ON f.product_id=p.product_id GROUP BY category",
    "WITH t AS (SELECT * FROM fact_sales) SELECT COUNT(*) FROM t",
    "SELECT * FROM dim_branch LIMIT 10",
    "SELECT b.region, SUM(f.total_amount) FROM fact_sales f "
    "JOIN dim_branch b ON f.branch_id=b.branch_id GROUP BY b.region",
]


@pytest.mark.parametrize("sql", MALICIOUS)
def test_block_malicious(sql):
    result = va.validate(sql)
    assert result.safe is False, f"Câu phá hoại bị LỌT: {sql}"


@pytest.mark.parametrize("sql", SAFE)
def test_allow_safe(sql):
    result = va.validate(sql)
    assert result.safe is True, f"Câu hợp lệ bị CHẶN nhầm: {sql} ({result.reason})"


def test_empty_sql_blocked():
    assert va.validate("").safe is False


def test_stacked_query_blocked():
    assert va.validate("SELECT 1; SELECT 2").safe is False
