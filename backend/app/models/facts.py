"""
Fact Tables của Star Schema — đều trỏ về các Dimension qua khóa ngoại.

  - fact_sales     : từng dòng bán hàng
  - fact_orders    : từng đơn hàng (cấp đơn)
  - fact_inventory : tồn kho theo sản phẩm/chi nhánh/thời điểm
"""
from __future__ import annotations

from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class FactSales(Base):
    __tablename__ = "fact_sales"

    sale_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("dim_product.product_id"), index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("dim_customer.customer_id"), index=True)
    branch_id: Mapped[int] = mapped_column(ForeignKey("dim_branch.branch_id"), index=True)
    time_id: Mapped[int] = mapped_column(ForeignKey("dim_time.time_id"), index=True)

    quantity: Mapped[int] = mapped_column(Integer, default=0)
    unit_price: Mapped[float] = mapped_column(Numeric(12, 2), default=0)
    discount: Mapped[float] = mapped_column(Numeric(12, 2), default=0)  # số tiền giảm
    total_amount: Mapped[float] = mapped_column(Numeric(14, 2), default=0)  # thành tiền sau giảm


class FactOrders(Base):
    __tablename__ = "fact_orders"

    order_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("dim_customer.customer_id"), index=True)
    branch_id: Mapped[int] = mapped_column(ForeignKey("dim_branch.branch_id"), index=True)
    time_id: Mapped[int] = mapped_column(ForeignKey("dim_time.time_id"), index=True)

    num_items: Mapped[int] = mapped_column(Integer, default=0)
    order_status: Mapped[str] = mapped_column(String(20), index=True)  # completed/cancelled/returned
    total_value: Mapped[float] = mapped_column(Numeric(14, 2), default=0)


class FactInventory(Base):
    __tablename__ = "fact_inventory"

    inventory_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("dim_product.product_id"), index=True)
    branch_id: Mapped[int] = mapped_column(ForeignKey("dim_branch.branch_id"), index=True)
    time_id: Mapped[int] = mapped_column(ForeignKey("dim_time.time_id"), index=True)

    stock_quantity: Mapped[int] = mapped_column(Integer, default=0)
    reorder_level: Mapped[int] = mapped_column(Integer, default=0)
    stock_value: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
