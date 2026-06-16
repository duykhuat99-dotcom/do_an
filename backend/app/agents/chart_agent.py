"""
Visualization Agent (Agent #5).

Xác định loại biểu đồ phù hợp (bar, line, pie, area, scatter) cho kết quả truy vấn,
rồi đóng gói thành cấu hình Plotly JSON ({data, layout}) để Frontend render trực tiếp
bằng react-plotly.js.

Cơ chế: LLM gợi ý loại biểu đồ + trục (best-effort) -> kiểm tra hợp lệ; nếu LLM lỗi
hoặc gợi ý không dùng được thì rơi về heuristic dựa trên hình dạng dữ liệu.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.agents.columns import find_time_column
from app.agents.validation_agent import _extract_json
from app.llm import LLMError, get_llm
from app.llm.base import LLMProviderInterface
from app.prompts import CHART_SYSTEM, build_chart_prompt
from app.utils import get_logger

logger = get_logger(__name__)

ALLOWED_CHARTS = {"bar", "line", "pie", "area", "scatter"}
_PIE_HINTS = ("tỷ trọng", "cơ cấu", "tỷ lệ", "phân bố", "chiếm", "proportion")


@dataclass
class ChartConfig:
    chart_type: str
    plotly: dict[str, Any] = field(default_factory=dict)
    x: str | None = None
    y: str | None = None
    title: str = ""
    reason: str = ""


class ChartAgent:
    def __init__(self, llm: LLMProviderInterface | None = None, use_llm: bool = True) -> None:
        self._llm = llm
        self.use_llm = use_llm

    @property
    def llm(self) -> LLMProviderInterface:
        return self._llm or get_llm()

    def build(self, question: str, df) -> ChartConfig | None:
        import pandas as pd  # lazy

        if df is None or len(df) == 0 or len(df.columns) == 0:
            return None

        numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        non_numeric = [c for c in df.columns if c not in numeric_cols]
        if not numeric_cols:
            return None  # không có chỉ số để vẽ

        choice = None
        if self.use_llm:
            choice = self._ask_llm(question, df)

        if not choice:
            choice = self._heuristic(question, df, numeric_cols, non_numeric)

        return self._to_plotly(df, choice)

    # ---------- LLM gợi ý ----------
    def _ask_llm(self, question: str, df) -> dict | None:
        try:
            sample = df.head(5).to_string(index=False)
            resp = self.llm.generate(
                build_chart_prompt(question, list(df.columns), sample),
                system=CHART_SYSTEM,
                max_tokens=200,
            )
            data = _extract_json(resp.text)
        except LLMError as exc:
            logger.warning("Chart LLM lỗi, dùng heuristic: %s", exc)
            return None

        if not data:
            return None
        ctype = str(data.get("chart_type", "")).lower().strip()
        x, y = data.get("x"), data.get("y")
        if ctype not in ALLOWED_CHARTS or x not in df.columns or y not in df.columns:
            logger.info("Gợi ý chart của LLM không hợp lệ (%s), dùng heuristic", data)
            return None
        return {
            "chart_type": ctype,
            "x": x,
            "y": y,
            "title": data.get("title") or f"{y} theo {x}",
            "reason": "Theo gợi ý LLM",
        }

    # ---------- Heuristic ----------
    def _heuristic(self, question: str, df, numeric_cols, non_numeric) -> dict:
        q = question.lower()
        time_col = find_time_column(df)
        # Chỉ số (measure) là cột số KHÔNG phải cột thời gian.
        measures = [c for c in numeric_cols if c != time_col]

        if time_col and measures:
            # Chuỗi thời gian -> line, trục x là cột thời gian.
            x, y, ctype = time_col, measures[0], "line"
        elif any(h in q for h in _PIE_HINTS) and non_numeric and len(df) <= 8:
            x, y, ctype = non_numeric[0], measures[0] if measures else numeric_cols[0], "pie"
        elif non_numeric and measures:
            # So sánh hạng mục -> bar.
            x, y, ctype = non_numeric[0], measures[0], "bar"
        elif len(measures) >= 2:
            # Hai biến số -> scatter.
            x, y, ctype = measures[0], measures[1], "scatter"
        else:
            x = non_numeric[0] if non_numeric else df.columns[0]
            y = measures[0] if measures else numeric_cols[0]
            ctype = "bar"

        return {
            "chart_type": ctype,
            "x": x,
            "y": y,
            "title": f"{y} theo {x}",
            "reason": "Heuristic theo hình dạng dữ liệu",
        }

    # ---------- Dựng Plotly JSON ----------
    def _to_plotly(self, df, choice: dict) -> ChartConfig:
        ctype, x, y = choice["chart_type"], choice["x"], choice["y"]
        xvals = df[x].tolist()
        yvals = df[y].tolist()

        if ctype == "pie":
            trace = {"type": "pie", "labels": [str(v) for v in xvals], "values": yvals}
        elif ctype == "line":
            trace = {"type": "scatter", "mode": "lines+markers", "x": xvals, "y": yvals, "name": y}
        elif ctype == "area":
            trace = {"type": "scatter", "mode": "lines", "fill": "tozeroy", "x": xvals, "y": yvals, "name": y}
        elif ctype == "scatter":
            trace = {"type": "scatter", "mode": "markers", "x": xvals, "y": yvals, "name": y}
        else:  # bar
            trace = {"type": "bar", "x": xvals, "y": yvals, "name": y}

        layout: dict[str, Any] = {"title": choice["title"], "autosize": True}
        if ctype != "pie":
            layout["xaxis"] = {"title": x}
            layout["yaxis"] = {"title": y}

        return ChartConfig(
            chart_type=ctype,
            plotly={"data": [trace], "layout": layout},
            x=x,
            y=y,
            title=choice["title"],
            reason=choice.get("reason", ""),
        )
