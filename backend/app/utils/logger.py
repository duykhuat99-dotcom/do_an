"""
Cấu hình logging tập trung: ghi ra console + file xoay vòng (rotating file).

Dùng:
    from app.utils import get_logger
    logger = get_logger(__name__)
    logger.info("Xin chào")
"""
from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.core.config import BASE_DIR, settings

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
_configured = False


def setup_logging() -> None:
    """Khởi tạo root logger (gọi 1 lần khi app start). Idempotent."""
    global _configured
    if _configured:
        return

    log_dir = (BASE_DIR / settings.log_dir).resolve()
    log_dir.mkdir(parents=True, exist_ok=True)

    level = getattr(logging, settings.log_level, logging.INFO)
    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    # Console Windows mặc định là cp1252 -> ép UTF-8 để log tiếng Việt không crash.
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (ValueError, OSError):
                pass

    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()

    # Console
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    root.addHandler(console)

    # File xoay vòng: 10MB/file, giữ 5 file gần nhất
    file_handler = RotatingFileHandler(
        log_dir / "app.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    # Giảm nhiễu từ thư viện bên thứ ba
    for noisy in ("uvicorn.access", "httpx", "chromadb", "sentence_transformers"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Lấy logger theo tên module; tự khởi tạo cấu hình nếu chưa có."""
    if not _configured:
        setup_logging()
    return logging.getLogger(name)
