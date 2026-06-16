"""Helper nhận diện vai trò cột (dùng chung cho Insight & Chart agents)."""
from __future__ import annotations

import re

# Token gợi ý cột thời gian/kỳ — gồm cả tiếng Việt có dấu và không dấu.
# Dùng so khớp theo TOKEN (tách theo _ - . / khoảng trắng) để tránh false positive
# kiểu 'name' bị nhận nhầm là 'nam'.
_TIME_TOKENS = {
    "date", "time", "day", "month", "quarter", "year", "period", "week",
    "ngay", "thang", "quy", "nam", "tuan", "ky",
    "ngày", "tháng", "quý", "năm", "tuần", "kỳ",
}


def _tokens(name: str) -> list[str]:
    return [t for t in re.split(r"[\s_\-./]+", str(name).lower()) if t]


def is_time_column(name: str, series=None) -> bool:
    """True nếu cột mang ý nghĩa thời gian (theo kiểu dữ liệu hoặc theo tên)."""
    if series is not None:
        try:
            import pandas as pd

            if pd.api.types.is_datetime64_any_dtype(series):
                return True
        except Exception:  # noqa: BLE001
            pass
    return any(tok in _TIME_TOKENS for tok in _tokens(name))


def find_time_column(df) -> str | None:
    """Trả về tên cột thời gian đầu tiên trong DataFrame (nếu có)."""
    for c in df.columns:
        if is_time_column(c, df[c]):
            return c
    return None
