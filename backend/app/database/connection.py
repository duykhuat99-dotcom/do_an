"""
Tầng kết nối MySQL bằng SQLAlchemy.

Cung cấp:
  - Engine chính (đọc/ghi) — dùng cho history, quản trị.
  - Engine chỉ-đọc (read-only) — dùng để thực thi SQL do LLM sinh (Phase 4).
  - Connection Pool có cấu hình, pre-ping (Health Check tự động).
  - Hàm kiểm tra kết nối có Retry (tenacity) + Logging.
  - Dependency `get_db()` cho FastAPI.

Engine được tạo lười (lazy singleton) để app vẫn khởi động được khi
MySQL chưa sẵn sàng — chỉ báo lỗi khi thực sự truy vấn.
"""
from __future__ import annotations

import time
from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import settings
from app.utils import get_logger

logger = get_logger(__name__)

_engine: Engine | None = None
_readonly_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def _build_engine(url: str, *, readonly: bool) -> Engine:
    """Tạo Engine với Connection Pool theo cấu hình."""
    label = "read-only" if readonly else "read-write"
    logger.info(
        "Khởi tạo SQLAlchemy engine (%s) -> %s:%s/%s",
        label,
        settings.mysql_host,
        settings.mysql_port,
        settings.mysql_database,
    )
    return create_engine(
        url,
        pool_size=settings.db_pool_size,
        max_overflow=settings.db_max_overflow,
        pool_timeout=settings.db_pool_timeout,
        pool_recycle=settings.db_pool_recycle,
        pool_pre_ping=True,  # tự kiểm tra connection còn sống trước khi dùng
        connect_args={"connect_timeout": settings.db_connect_timeout},
        future=True,
        echo=False,
    )


def get_engine() -> Engine:
    """Trả về engine chính (lazy singleton)."""
    global _engine
    if _engine is None:
        _engine = _build_engine(settings.database_url, readonly=False)
    return _engine


def get_readonly_engine() -> Engine:
    """Trả về engine chỉ-đọc (lazy singleton) — dùng để chạy SQL của LLM."""
    global _readonly_engine
    if _readonly_engine is None:
        _readonly_engine = _build_engine(settings.readonly_database_url, readonly=True)
    return _readonly_engine


def get_session_factory() -> sessionmaker[Session]:
    """Trả về sessionmaker gắn với engine chính (lazy singleton)."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            bind=get_engine(), autoflush=False, autocommit=False, expire_on_commit=False
        )
    return _SessionLocal


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency: cấp một Session và đảm bảo đóng sau request."""
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()


def _ping_once(engine: Engine) -> None:
    """Gửi `SELECT 1` một lần (không retry) — dùng cho health check fail-fast."""
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))


@retry(
    reraise=True,
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(SQLAlchemyError),
)
def wait_for_database() -> None:
    """Chờ DB sẵn sàng (có retry + backoff) — dùng lúc khởi động khi DB đang lên."""
    _ping_once(get_engine())


def check_database_connection() -> dict[str, object]:
    """
    Health Check kết nối DB (FAIL-FAST, một lần). Trả về dict mô tả trạng thái —
    KHÔNG ném lỗi để các endpoint trạng thái luôn phản hồi nhanh và gọn gàng.
    """
    start = time.perf_counter()
    try:
        _ping_once(get_engine())
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.info("Kết nối MySQL OK (%.2f ms)", elapsed_ms)
        return {
            "healthy": True,
            "database": settings.mysql_database,
            "host": f"{settings.mysql_host}:{settings.mysql_port}",
            "latency_ms": elapsed_ms,
            "detail": "Kết nối thành công",
        }
    except SQLAlchemyError as exc:
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        logger.error("Kết nối MySQL thất bại: %s", exc)
        return {
            "healthy": False,
            "database": settings.mysql_database,
            "host": f"{settings.mysql_host}:{settings.mysql_port}",
            "latency_ms": elapsed_ms,
            "detail": str(exc.__cause__ or exc),
        }


def init_schema() -> None:
    """Tạo các bảng còn thiếu (vd feedback) + nâng cấp cột — idempotent, best-effort."""
    try:
        import app.models  # noqa: F401  - đăng ký toàn bộ ORM model
        from app.database.base import Base

        Base.metadata.create_all(get_engine())
    except SQLAlchemyError as exc:
        logger.warning("Bỏ qua create_all (DB chưa sẵn sàng?): %s", exc)
    ensure_history_columns()


def ensure_history_columns() -> None:
    """
    Thêm cột chart_json/insight_json vào conversation_history nếu chưa có.

    Idempotent, best-effort (MySQL không hỗ trợ ADD COLUMN IF NOT EXISTS nên phải
    kiểm tra information_schema trước). Chạy lúc khởi động để tự nâng cấp DB cũ.
    """
    try:
        engine = get_engine()
        with engine.begin() as conn:
            existing = conn.execute(
                text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_schema=:db AND table_name='conversation_history'"
                ),
                {"db": settings.mysql_database},
            ).scalars().all()
            existing = {c.lower() for c in existing}
            if not existing:
                return  # bảng chưa tồn tại -> create_all sẽ tạo đủ cột
            for col in ("chart_json", "insight_json"):
                if col not in existing:
                    conn.execute(
                        text(f"ALTER TABLE conversation_history ADD COLUMN {col} LONGTEXT NULL")
                    )
                    logger.info("Migration: đã thêm cột %s vào conversation_history", col)
    except SQLAlchemyError as exc:
        logger.warning("Bỏ qua migration cột history (DB chưa sẵn sàng?): %s", exc)


def dispose_engines() -> None:
    """Đóng toàn bộ pool khi shutdown."""
    global _engine, _readonly_engine
    if _engine is not None:
        _engine.dispose()
        _engine = None
    if _readonly_engine is not None:
        _readonly_engine.dispose()
        _readonly_engine = None
    logger.info("Đã giải phóng connection pool")
