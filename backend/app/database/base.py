"""Declarative Base dùng chung cho mọi ORM model."""
from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Lớp cơ sở cho toàn bộ model (fact, dim, history)."""

    pass
