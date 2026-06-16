"""
Dimension Tables của Star Schema.

  - dim_product  : sản phẩm
  - dim_customer : khách hàng
  - dim_time     : thời gian (date dimension)
  - dim_branch   : chi nhánh
"""
from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class DimProduct(Base):
    __tablename__ = "dim_product"

    product_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    product_name: Mapped[str] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(String(100), index=True)
    brand: Mapped[str] = mapped_column(String(100))
    unit_cost: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    unit_price: Mapped[float] = mapped_column(Numeric(12, 2), default=0)


class DimCustomer(Base):
    __tablename__ = "dim_customer"

    customer_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    customer_name: Mapped[str] = mapped_column(String(255))
    gender: Mapped[str] = mapped_column(String(10))
    age_group: Mapped[str] = mapped_column(String(20))
    city: Mapped[str] = mapped_column(String(100), index=True)
    segment: Mapped[str] = mapped_column(String(50), index=True)  # VIP, Thường, Mới...


class DimBranch(Base):
    __tablename__ = "dim_branch"

    branch_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    branch_code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    branch_name: Mapped[str] = mapped_column(String(255))
    region: Mapped[str] = mapped_column(String(50), index=True)  # Bắc/Trung/Nam
    city: Mapped[str] = mapped_column(String(100))
    manager: Mapped[str] = mapped_column(String(255))


class DimTime(Base):
    __tablename__ = "dim_time"

    time_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    full_date: Mapped[date] = mapped_column(Date, unique=True, index=True)
    day: Mapped[int] = mapped_column(Integer)
    month: Mapped[int] = mapped_column(Integer, index=True)
    quarter: Mapped[int] = mapped_column(Integer, index=True)
    year: Mapped[int] = mapped_column(Integer, index=True)
    weekday: Mapped[int] = mapped_column(Integer)  # 0=Thứ Hai ... 6=Chủ Nhật
    is_weekend: Mapped[int] = mapped_column(Integer, default=0)
