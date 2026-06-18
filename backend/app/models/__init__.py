"""Gom toàn bộ ORM model để `Base.metadata` biết mọi bảng khi create_all."""
from app.models.dimensions import (
    DimCustomerSegment,
    DimDate,
    DimDestination,
    DimTour,
)
from app.models.facts import FactBooking
from app.models.history import ChatSession, ConversationHistory, Feedback, QueryLog

__all__ = [
    "DimDate",
    "DimDestination",
    "DimCustomerSegment",
    "DimTour",
    "FactBooking",
    "ConversationHistory",
    "QueryLog",
    "Feedback",
    "ChatSession",
]
