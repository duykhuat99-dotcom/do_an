"""
History Agent (Agent #6).

Quản lý ghi/đọc lịch sử hội thoại và nhật ký truy vấn vào database để duy trì
context phiên làm việc (theo session_id).

  - conversation_history: lưu từng lượt user/assistant (kèm SQL đã sinh).
  - query_log: nhật ký SQL + thời gian thực thi + kết quả/lỗi.

Mọi thao tác DB đều "best-effort": nếu DB lỗi thì ghi log cảnh báo và KHÔNG làm
hỏng luồng trả lời cho người dùng.
"""
from __future__ import annotations

import json
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.exc import SQLAlchemyError

from app.database import get_session_factory
from app.models import ChatSession, ConversationHistory, Feedback, QueryLog
from app.utils import get_logger

logger = get_logger(__name__)


def _safe_json(raw: str | None):
    """Parse JSON đã lưu; trả None nếu rỗng/hỏng."""
    if not raw:
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None


class HistoryAgent:
    def save_turn(
        self,
        session_id: str,
        question: str,
        answer: str | None,
        generated_sql: str | None = None,
        chart_json: str | None = None,
        insight_json: str | None = None,
    ) -> bool:
        """Lưu một lượt hội thoại: bản ghi user (câu hỏi) + assistant (trả lời)."""
        try:
            factory = get_session_factory()
            with factory() as session:
                session.add(
                    ConversationHistory(session_id=session_id, role="user", question=question)
                )
                session.add(
                    ConversationHistory(
                        session_id=session_id,
                        role="assistant",
                        answer=answer,
                        generated_sql=generated_sql,
                        chart_json=chart_json,
                        insight_json=insight_json,
                    )
                )
                session.commit()
            return True
        except SQLAlchemyError as exc:
            logger.warning("Không lưu được lịch sử hội thoại: %s", exc)
            return False

    def log_query(
        self,
        session_id: str,
        question: str,
        generated_sql: str | None,
        success: bool,
        row_count: int = 0,
        execution_time_ms: float = 0.0,
        error: str | None = None,
    ) -> bool:
        """Ghi nhật ký một lần sinh/thực thi SQL."""
        try:
            factory = get_session_factory()
            with factory() as session:
                session.add(
                    QueryLog(
                        session_id=session_id,
                        question=question,
                        generated_sql=generated_sql,
                        success=success,
                        row_count=row_count,
                        execution_time_ms=int(execution_time_ms),
                        error=error,
                    )
                )
                session.commit()
            return True
        except SQLAlchemyError as exc:
            logger.warning("Không ghi được query_log: %s", exc)
            return False

    def save_feedback(
        self, rating: str, question: str | None, answer: str | None, session_id: str | None = None
    ) -> bool:
        """Lưu đánh giá 👍/👎 của người dùng cho một câu trả lời."""
        if rating not in ("up", "down"):
            return False
        try:
            factory = get_session_factory()
            with factory() as session:
                session.add(
                    Feedback(
                        session_id=session_id, question=question, answer=answer, rating=rating
                    )
                )
                session.commit()
            return True
        except SQLAlchemyError as exc:
            logger.warning("Không lưu được feedback: %s", exc)
            return False

    def get_stats(self) -> dict[str, Any]:
        """Tổng hợp thống kê từ query_log + feedback (cho trang quản trị)."""
        empty = {
            "total_queries": 0,
            "success_count": 0,
            "success_rate": 0.0,
            "avg_execution_ms": 0.0,
            "feedback_up": 0,
            "feedback_down": 0,
            "top_questions": [],
            "by_day": [],
        }
        try:
            factory = get_session_factory()
            with factory() as session:
                total = session.scalar(select(func.count()).select_from(QueryLog)) or 0
                success = (
                    session.scalar(
                        select(func.count()).select_from(QueryLog).where(QueryLog.success.is_(True))
                    )
                    or 0
                )
                avg_ms = session.scalar(select(func.avg(QueryLog.execution_time_ms))) or 0
                top = session.execute(
                    select(QueryLog.question, func.count().label("c"))
                    .group_by(QueryLog.question)
                    .order_by(func.count().desc())
                    .limit(10)
                ).all()
                by_day = session.execute(
                    select(
                        func.date(QueryLog.created_at).label("d"),
                        func.count().label("c"),
                        func.sum(QueryLog.success).label("ok"),
                    )
                    .group_by(func.date(QueryLog.created_at))
                    .order_by(func.date(QueryLog.created_at))
                    .limit(30)
                ).all()
                fb_up = (
                    session.scalar(
                        select(func.count()).select_from(Feedback).where(Feedback.rating == "up")
                    )
                    or 0
                )
                fb_down = (
                    session.scalar(
                        select(func.count()).select_from(Feedback).where(Feedback.rating == "down")
                    )
                    or 0
                )
            return {
                "total_queries": int(total),
                "success_count": int(success),
                "success_rate": round(success / total * 100, 1) if total else 0.0,
                "avg_execution_ms": round(float(avg_ms), 1),
                "feedback_up": int(fb_up),
                "feedback_down": int(fb_down),
                "top_questions": [{"question": q, "count": int(c)} for q, c in top],
                "by_day": [
                    {"date": str(d), "total": int(c), "success": int(ok or 0)}
                    for d, c, ok in by_day
                ],
            }
        except SQLAlchemyError as exc:
            logger.warning("Không lấy được thống kê: %s", exc)
            return empty

    def list_sessions(self, limit: int = 50) -> list[dict[str, Any]]:
        """Liệt kê các cuộc trò chuyện (mỗi session_id một mục), mới nhất trước.

        Mỗi mục gồm: tiêu đề (câu hỏi đầu tiên), thời điểm hoạt động gần nhất,
        số tin nhắn.
        """
        try:
            factory = get_session_factory()
            with factory() as session:
                agg = session.execute(
                    select(
                        ConversationHistory.session_id,
                        func.max(ConversationHistory.created_at).label("last_at"),
                        func.count().label("msg_count"),
                    )
                    .group_by(ConversationHistory.session_id)
                    .order_by(func.max(ConversationHistory.created_at).desc())
                    .limit(limit)
                ).all()

                session_ids = [r.session_id for r in agg]
                titles: dict[str, str] = {}
                custom: dict[str, str] = {}
                if session_ids:
                    trows = session.execute(
                        select(
                            ConversationHistory.session_id,
                            ConversationHistory.question,
                        )
                        .where(
                            ConversationHistory.role == "user",
                            ConversationHistory.session_id.in_(session_ids),
                        )
                        .order_by(ConversationHistory.id)
                    ).all()
                    for sid, question in trows:
                        if sid not in titles and question:
                            titles[sid] = question
                    # Tên tùy chỉnh (đặt lại) — ưu tiên hơn câu hỏi đầu.
                    crows = session.execute(
                        select(ChatSession.session_id, ChatSession.title).where(
                            ChatSession.session_id.in_(session_ids)
                        )
                    ).all()
                    custom = {sid: t for sid, t in crows}

            return [
                {
                    "session_id": r.session_id,
                    "title": custom.get(r.session_id)
                    or titles.get(r.session_id)
                    or "Cuộc trò chuyện",
                    "last_at": r.last_at.isoformat() if r.last_at else None,
                    "message_count": int(r.msg_count),
                }
                for r in agg
            ]
        except SQLAlchemyError as exc:
            logger.warning("Không liệt kê được danh sách phiên: %s", exc)
            return []

    def rename_session(self, session_id: str, title: str) -> bool:
        """Đặt lại tên hiển thị cho một cuộc trò chuyện."""
        title = (title or "").strip()[:255]
        if not title:
            return False
        try:
            factory = get_session_factory()
            with factory() as session:
                obj = session.get(ChatSession, session_id)
                if obj:
                    obj.title = title
                else:
                    session.add(ChatSession(session_id=session_id, title=title))
                session.commit()
            return True
        except SQLAlchemyError as exc:
            logger.warning("Không đổi tên được phiên: %s", exc)
            return False

    def delete_session(self, session_id: str) -> bool:
        """Xóa toàn bộ lịch sử + nhật ký + tên của một cuộc trò chuyện."""
        try:
            factory = get_session_factory()
            with factory() as session:
                session.execute(
                    delete(ConversationHistory).where(
                        ConversationHistory.session_id == session_id
                    )
                )
                session.execute(delete(QueryLog).where(QueryLog.session_id == session_id))
                session.execute(delete(ChatSession).where(ChatSession.session_id == session_id))
                session.commit()
            return True
        except SQLAlchemyError as exc:
            logger.warning("Không xóa được phiên: %s", exc)
            return False

    def get_history(self, session_id: str, limit: int = 20) -> list[dict[str, Any]]:
        """Đọc lịch sử hội thoại của một phiên (mới nhất trước)."""
        try:
            factory = get_session_factory()
            with factory() as session:
                stmt = (
                    select(ConversationHistory)
                    .where(ConversationHistory.session_id == session_id)
                    .order_by(ConversationHistory.created_at.desc(), ConversationHistory.id.desc())
                    .limit(limit)
                )
                rows = session.scalars(stmt).all()
            return [
                {
                    "id": r.id,
                    "role": r.role,
                    "question": r.question,
                    "answer": r.answer,
                    "generated_sql": r.generated_sql,
                    "chart": _safe_json(r.chart_json),
                    "insight": _safe_json(r.insight_json),
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                }
                for r in rows
            ]
        except SQLAlchemyError as exc:
            logger.warning("Không đọc được lịch sử hội thoại: %s", exc)
            return []
