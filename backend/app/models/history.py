"""
Bảng lưu vết phục vụ History Agent (Phase 6) — KHÔNG thuộc DataMart nghiệp vụ.

  - conversation_history : từng lượt hội thoại (user/assistant) theo phiên.
  - query_log            : nhật ký SQL do LLM sinh + thời gian thực thi + kết quả.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base

# LONGTEXT trên MySQL (chứa Plotly JSON có thể lớn); TEXT trên SQLite (cho test).
_JSON_COL = LONGTEXT().with_variant(Text(), "sqlite")


class ConversationHistory(Base):
    __tablename__ = "conversation_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(64), index=True)
    role: Mapped[str] = mapped_column(String(16))  # user | assistant
    question: Mapped[str | None] = mapped_column(Text, nullable=True)
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated_sql: Mapped[str | None] = mapped_column(Text, nullable=True)
    # JSON đã tuần tự hóa của biểu đồ Plotly và insight (để khôi phục khi mở lại chat).
    chart_json: Mapped[str | None] = mapped_column(_JSON_COL, nullable=True)
    insight_json: Mapped[str | None] = mapped_column(_JSON_COL, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), index=True
    )


class ChatSession(Base):
    """Lưu tên tùy chỉnh (đặt lại) cho một cuộc trò chuyện."""

    __tablename__ = "chat_session"

    session_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    question: Mapped[str | None] = mapped_column(Text, nullable=True)
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    rating: Mapped[str] = mapped_column(String(10))  # 'up' | 'down'
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), index=True
    )


class QueryLog(Base):
    __tablename__ = "query_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(64), index=True)
    question: Mapped[str] = mapped_column(Text)
    generated_sql: Mapped[str | None] = mapped_column(Text, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, default=False)
    row_count: Mapped[int] = mapped_column(Integer, default=0)
    execution_time_ms: Mapped[float] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), index=True
    )
