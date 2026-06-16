"""Kiểm thử Insight & Chart agents (chế độ không dùng LLM)."""
import pandas as pd

from app.agents import ChartAgent, InsightAgent

insight = InsightAgent(use_llm=False)
chart = ChartAgent(use_llm=False)

df_cat = pd.DataFrame(
    {"category": ["Điện thoại", "Laptop", "Phụ kiện"], "doanh_thu": [1200, 900, 300]}
)
df_time = pd.DataFrame({"thang": [1, 2, 3, 4], "doanh_thu": [100, 120, 150, 200]})


def test_insight_highlights_top_bottom():
    r = insight.analyze("Doanh thu theo danh mục?", df_cat)
    assert r.stats["row_count"] == 3
    assert any("Điện thoại" in h for h in r.highlights)


def test_insight_growth():
    r = insight.analyze("Doanh thu theo tháng?", df_time)
    g = r.stats.get("growth")
    assert g is not None
    assert g["pct_change"] == 100.0  # 100 -> 200


def test_insight_empty_df():
    r = insight.analyze("?", pd.DataFrame())
    assert "Không có dữ liệu" in r.summary


def test_chart_bar_for_category():
    c = chart.build("Doanh thu theo danh mục?", df_cat)
    assert c.chart_type == "bar"
    assert c.plotly["data"][0]["type"] == "bar"


def test_chart_line_for_time():
    c = chart.build("Doanh thu theo tháng?", df_time)
    assert c.chart_type == "line"


def test_chart_pie_for_keyword():
    c = chart.build("Cơ cấu doanh thu theo danh mục?", df_cat)
    assert c.chart_type == "pie"


def test_chart_none_without_measure():
    df = pd.DataFrame({"a": ["x", "y"], "b": ["m", "n"]})
    assert chart.build("?", df) is None
