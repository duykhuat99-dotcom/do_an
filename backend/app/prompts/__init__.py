"""Quản lý prompt cho các agent (mỗi agent một module)."""
from app.prompts.chart import CHART_SYSTEM, build_chart_prompt
from app.prompts.insight import INSIGHT_SYSTEM, build_insight_prompt
from app.prompts.router import GENERAL_SYSTEM, ROUTER_SYSTEM, build_router_prompt
from app.prompts.suggest import SUGGEST_SYSTEM, build_suggest_prompt
from app.prompts.sql import (
    SQL_FIX_SYSTEM,
    SQL_SYSTEM,
    build_fix_prompt,
    build_sql_prompt,
)
from app.prompts.validation import VALIDATION_SYSTEM, build_validation_prompt

__all__ = [
    "SQL_SYSTEM",
    "build_sql_prompt",
    "SQL_FIX_SYSTEM",
    "build_fix_prompt",
    "VALIDATION_SYSTEM",
    "build_validation_prompt",
    "INSIGHT_SYSTEM",
    "build_insight_prompt",
    "CHART_SYSTEM",
    "build_chart_prompt",
    "ROUTER_SYSTEM",
    "build_router_prompt",
    "GENERAL_SYSTEM",
    "SUGGEST_SYSTEM",
    "build_suggest_prompt",
]
