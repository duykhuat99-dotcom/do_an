"""
Dimension Tables — Star Schema "Vietnam Tour Bookings".

  - DimDate            : chiều thời gian (theo booking_date)
  - DimDestination     : điểm đến (tỉnh, vùng, loại địa điểm)
  - DimCustomerSegment : nhóm khách hàng (nhóm tuổi, loại khách)
  - DimTour            : loại tour (danh mục, số ngày, phương tiện)

Tên bảng & cột giữ đúng PascalCase theo sơ đồ Star Schema.
"""
from __future__ import annotations

from datetime import date

from sqlalchemy import Boolean, Date, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class DimDate(Base):
    __tablename__ = "DimDate"

    DateKey: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    FullDate: Mapped[date] = mapped_column(Date)
    DayOfMonth: Mapped[int] = mapped_column(Integer)
    DayName: Mapped[str] = mapped_column(String(20))
    WeekOfYear: Mapped[int] = mapped_column(Integer)
    MonthNumber: Mapped[int] = mapped_column(Integer, index=True)
    MonthName: Mapped[str] = mapped_column(String(20))
    QuarterNumber: Mapped[int] = mapped_column(Integer, index=True)
    YearNumber: Mapped[int] = mapped_column(Integer, index=True)
    IsWeekend: Mapped[bool] = mapped_column(Boolean)


class DimDestination(Base):
    __tablename__ = "DimDestination"

    DestinationKey: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    DestinationName: Mapped[str] = mapped_column(String(100), index=True)
    Province: Mapped[str] = mapped_column(String(100))
    Region: Mapped[str] = mapped_column(String(50), index=True)
    DestinationType: Mapped[str] = mapped_column(String(50))


class DimCustomerSegment(Base):
    __tablename__ = "DimCustomerSegment"

    SegmentKey: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    SegmentName: Mapped[str] = mapped_column(String(50), index=True)
    AgeGroup: Mapped[str] = mapped_column(String(50))
    CustomerType: Mapped[str] = mapped_column(String(50))


class DimTour(Base):
    __tablename__ = "DimTour"

    TourKey: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    TourName: Mapped[str] = mapped_column(String(200))
    TourCategory: Mapped[str] = mapped_column(String(50), index=True)
    DurationDays: Mapped[int] = mapped_column(Integer)
    TransportationType: Mapped[str] = mapped_column(String(50))
