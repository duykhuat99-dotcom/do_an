"""
Fact Table — FactBooking (Star Schema "Vietnam Tour Bookings").

Mỗi dòng là một lượt đặt tour (booking), trỏ về 4 chiều: thời gian, điểm đến,
nhóm khách hàng, loại tour. Các measure: Revenue, Pax, BookingCount, SatisfactionScore.
"""
from __future__ import annotations

from sqlalchemy import BigInteger, ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class FactBooking(Base):
    __tablename__ = "FactBooking"

    BookingID: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    DateKey: Mapped[int] = mapped_column(ForeignKey("DimDate.DateKey"), index=True)
    DestinationKey: Mapped[int] = mapped_column(
        ForeignKey("DimDestination.DestinationKey"), index=True
    )
    SegmentKey: Mapped[int] = mapped_column(
        ForeignKey("DimCustomerSegment.SegmentKey"), index=True
    )
    TourKey: Mapped[int] = mapped_column(ForeignKey("DimTour.TourKey"), index=True)

    Revenue: Mapped[float] = mapped_column(Numeric(18, 2), default=0)        # Doanh thu (VNĐ)
    Pax: Mapped[int] = mapped_column(Integer, default=0)                     # Số lượng khách
    BookingCount: Mapped[int] = mapped_column(Integer, default=1)           # Số booking
    SatisfactionScore: Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True)
