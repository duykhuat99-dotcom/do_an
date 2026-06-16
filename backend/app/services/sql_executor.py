"""
Thực thi SQL an toàn trên DataMart và trả về kết quả dạng Pandas DataFrame.

Các lớp an toàn:
  - Dùng engine CHỈ-ĐỌC (tài khoản datamart_ro chỉ có quyền SELECT).
  - Đặt MAX_EXECUTION_TIME (timeout ở phía MySQL) để tránh truy vấn treo.
  - Tự chèn LIMIT nếu câu lệnh chưa có, tránh kéo về quá nhiều dòng.

LƯU Ý: chỉ gọi sau khi Validation Agent đã xác nhận an toàn.
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database import get_readonly_engine
from app.utils import get_logger

logger = get_logger(__name__)

DEFAULT_MAX_ROWS = 1000
DEFAULT_TIMEOUT_MS = 15000

_LIMIT_RE = re.compile(r"\blimit\b", re.IGNORECASE)


class SQLExecutionError(RuntimeError):
    """Lỗi khi thực thi SQL trên DataMart."""


@dataclass
class QueryResult:
    columns: list[str]
    rows: list[dict[str, Any]]
    row_count: int
    execution_time_ms: float
    truncated: bool = False
    dataframe: Any = field(default=None, repr=False)  # pandas.DataFrame


def _ensure_limit(sql: str, max_rows: int) -> str:
    """Chèn LIMIT nếu câu lệnh chưa có (an toàn số dòng trả về)."""
    if _LIMIT_RE.search(sql):
        return sql
    return f"{sql.rstrip().rstrip(';')} LIMIT {max_rows}"


def execute_sql(
    sql: str,
    max_rows: int = DEFAULT_MAX_ROWS,
    timeout_ms: int = DEFAULT_TIMEOUT_MS,
) -> QueryResult:
    """Chạy câu SELECT và trả về QueryResult (kèm DataFrame cho Insight/Chart)."""
    import pandas as pd  # lazy import: chỉ cần khi thực thi truy vấn

    safe_sql = _ensure_limit(sql, max_rows)
    engine = get_readonly_engine()

    start = time.perf_counter()
    try:
        with engine.connect() as conn:
            # Giới hạn thời gian thực thi ở phía MySQL (mili giây).
            try:
                conn.execute(text(f"SET SESSION MAX_EXECUTION_TIME={int(timeout_ms)}"))
            except SQLAlchemyError:
                # Một số phiên bản/biến thể không hỗ trợ -> bỏ qua, vẫn chạy.
                pass
            df = pd.read_sql(text(safe_sql), conn)
    except SQLAlchemyError as exc:
        elapsed = round((time.perf_counter() - start) * 1000, 2)
        logger.error("Thực thi SQL lỗi (%.0f ms): %s", elapsed, exc)
        raise SQLExecutionError(str(exc.__cause__ or exc)) from exc

    elapsed = round((time.perf_counter() - start) * 1000, 2)

    truncated = False
    if len(df) > max_rows:
        df = df.head(max_rows)
        truncated = True

    # Chuẩn hóa kiểu dữ liệu cho JSON (Decimal/Timestamp -> str/native).
    records = df.astype(object).where(df.notna(), None).to_dict(orient="records")
    records = _jsonify_records(records)

    logger.info("Thực thi SQL OK: %d dòng (%.0f ms)", len(df), elapsed)
    return QueryResult(
        columns=list(df.columns),
        rows=records,
        row_count=len(df),
        execution_time_ms=elapsed,
        truncated=truncated,
        dataframe=df,
    )


def _jsonify_records(records: list[dict]) -> list[dict]:
    """Ép các kiểu không-JSON (Decimal, datetime, ...) về dạng tuần tự hóa được."""
    from datetime import date, datetime
    from decimal import Decimal

    out = []
    for row in records:
        clean = {}
        for k, v in row.items():
            if isinstance(v, Decimal):
                clean[k] = float(v)
            elif isinstance(v, (datetime, date)):
                clean[k] = v.isoformat()
            else:
                clean[k] = v
        out.append(clean)
    return out
