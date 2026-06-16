"""
Insight Agent (Agent #4).

Phân tích kết quả truy vấn (Pandas DataFrame) để rút ra nhận định:
  - Thống kê cơ bản (tổng, trung bình, min/max) trên cột số.
  - Giá trị nổi bật (cao nhất/thấp nhất) theo chỉ số chính.
  - Tăng trưởng/so sánh kỳ trước nếu có cột thời gian/thứ tự.
Phần thống kê được tính DETERMINISTIC bằng pandas; sau đó LLM diễn giải thành câu
văn tiếng Việt. Nếu LLM lỗi, vẫn có nhận định dựa trên quy tắc (fallback).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.agents.columns import find_time_column
from app.llm import LLMError, get_llm
from app.llm.base import LLMProviderInterface
from app.prompts import INSIGHT_SYSTEM, build_insight_prompt
from app.utils import get_logger

logger = get_logger(__name__)


@dataclass
class InsightResult:
    summary: str
    stats: dict[str, Any] = field(default_factory=dict)
    highlights: list[str] = field(default_factory=list)
    llm_used: bool = False


class InsightAgent:
    def __init__(self, llm: LLMProviderInterface | None = None, use_llm: bool = True) -> None:
        self._llm = llm
        self.use_llm = use_llm

    @property
    def llm(self) -> LLMProviderInterface:
        return self._llm or get_llm()

    def analyze(self, question: str, df) -> InsightResult:
        import pandas as pd  # lazy

        if df is None or len(df) == 0:
            return InsightResult(summary="Không có dữ liệu phù hợp với câu hỏi.", stats={})

        stats = self._compute_stats(df, pd)
        highlights = self._build_highlights(df, stats, pd)
        rule_based = " ".join(highlights) or "Đã truy vấn được dữ liệu."

        summary = rule_based
        llm_used = False
        if self.use_llm:
            try:
                data_summary = self._format_for_llm(df, stats, highlights)
                resp = self.llm.generate(
                    build_insight_prompt(question, data_summary),
                    system=INSIGHT_SYSTEM,
                    max_tokens=300,
                )
                if resp.text.strip():
                    summary = resp.text.strip()
                    llm_used = True
            except LLMError as exc:
                logger.warning("Insight LLM lỗi, dùng fallback theo quy tắc: %s", exc)

        return InsightResult(
            summary=summary, stats=stats, highlights=highlights, llm_used=llm_used
        )

    # ---------- Thống kê ----------
    def _compute_stats(self, df, pd) -> dict[str, Any]:
        numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        stats: dict[str, Any] = {
            "row_count": int(len(df)),
            "columns": list(df.columns),
            "numeric_columns": numeric_cols,
            "measures": {},
        }
        for c in numeric_cols:
            col = df[c]
            stats["measures"][c] = {
                "sum": float(col.sum()),
                "mean": float(col.mean()),
                "min": float(col.min()),
                "max": float(col.max()),
            }
        # cột thời gian (nếu có)
        time_col = find_time_column(df)
        stats["time_column"] = time_col

        # Tăng trưởng đầu kỳ -> cuối kỳ trên chỉ số chính (loại trừ chính cột thời gian)
        measures = [c for c in numeric_cols if c != time_col]
        if time_col and measures:
            measure = measures[0]
            ordered = df.sort_values(by=time_col)
            first = float(ordered[measure].iloc[0])
            last = float(ordered[measure].iloc[-1])
            growth = ((last - first) / first * 100) if first else None
            stats["growth"] = {
                "measure": measure,
                "first": first,
                "last": last,
                "pct_change": round(growth, 2) if growth is not None else None,
            }
        return stats

    def _build_highlights(self, df, stats, pd) -> list[str]:
        out: list[str] = []
        out.append(f"Kết quả gồm {stats['row_count']} dòng.")

        measures = [c for c in stats["numeric_columns"] if c != stats.get("time_column")]
        label_col = next(
            (c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c])), None
        )
        if measures and label_col is not None and len(df) > 1:
            measure = measures[0]
            idx_max = df[measure].idxmax()
            idx_min = df[measure].idxmin()
            out.append(
                f"'{df.loc[idx_max, label_col]}' cao nhất theo {measure} "
                f"({_fmt(df.loc[idx_max, measure])}); "
                f"'{df.loc[idx_min, label_col]}' thấp nhất ({_fmt(df.loc[idx_min, measure])})."
            )
        if "growth" in stats and stats["growth"].get("pct_change") is not None:
            g = stats["growth"]
            chieu = "tăng" if g["pct_change"] >= 0 else "giảm"
            out.append(
                f"{g['measure']} {chieu} {abs(g['pct_change'])}% từ đầu kỳ đến cuối kỳ."
            )
        return out

    def _format_for_llm(self, df, stats, highlights) -> str:
        lines = [f"- Số dòng: {stats['row_count']}", f"- Cột: {', '.join(stats['columns'])}"]
        for c, m in stats["measures"].items():
            lines.append(
                f"- {c}: tổng={_fmt(m['sum'])}, TB={_fmt(m['mean'])}, "
                f"min={_fmt(m['min'])}, max={_fmt(m['max'])}"
            )
        if highlights:
            lines.append("- Điểm nổi bật: " + " ".join(highlights))
        lines.append("- Vài dòng đầu:\n" + df.head(5).to_string(index=False))
        return "\n".join(lines)


def _fmt(v: float) -> str:
    """Định dạng số gọn (phân tách hàng nghìn)."""
    try:
        return f"{v:,.0f}" if abs(v) >= 1000 else f"{v:,.2f}"
    except (ValueError, TypeError):
        return str(v)
