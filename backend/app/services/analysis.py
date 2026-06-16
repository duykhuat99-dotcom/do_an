"""
Analysis Service — chạy Insight Agent + Visualization Agent trên một DataFrame.

Tách riêng để Orchestrator (Phase 6) và endpoint /chart tái sử dụng chung.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.agents import ChartAgent, ChartConfig, InsightAgent, InsightResult
from app.utils import get_logger

logger = get_logger(__name__)


@dataclass
class AnalysisResult:
    insight: InsightResult | None = None
    chart: ChartConfig | None = None


class AnalysisService:
    def __init__(
        self,
        insight_agent: InsightAgent | None = None,
        chart_agent: ChartAgent | None = None,
    ) -> None:
        self.insight_agent = insight_agent or InsightAgent()
        self.chart_agent = chart_agent or ChartAgent()

    def analyze(self, question: str, df, with_insight: bool = True) -> AnalysisResult:
        insight = self.insight_agent.analyze(question, df) if with_insight else None
        chart = self.chart_agent.build(question, df)
        return AnalysisResult(insight=insight, chart=chart)
