"""
Sinh dữ liệu mẫu cho MySQL DataMart (Star Schema).

- Tạo bảng nếu chưa có (Base.metadata.create_all) — idempotent.
- Nạp Dimension trước, sau đó sinh Fact tham chiếu hợp lệ.
- Dùng seed cố định để kết quả lặp lại được.

Chạy (từ thư mục gốc dự án, sau khi đã cấu hình backend/.env):
    python scripts/seed_data.py
    python scripts/seed_data.py --sales 5000 --reset
"""
from __future__ import annotations

import argparse
import random
import sys
from datetime import date, timedelta
from pathlib import Path

# Cho phép import package `app`: ở host là ../backend, trong container là /app.
BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR) if BACKEND_DIR.exists() else "/app")

from faker import Faker  # noqa: E402
from sqlalchemy import func, select  # noqa: E402

from app.database import Base, get_engine, get_session_factory  # noqa: E402
from app.models import (  # noqa: E402
    DimBranch,
    DimCustomer,
    DimProduct,
    DimTime,
    FactInventory,
    FactOrders,
    FactSales,
)
from app.utils import get_logger  # noqa: E402

logger = get_logger("seed")

SEED = 42
fake = Faker("vi_VN")
Faker.seed(SEED)
random.seed(SEED)

CATEGORIES = {
    "Điện thoại": ["Apple", "Samsung", "Xiaomi", "Oppo"],
    "Laptop": ["Dell", "HP", "Asus", "Lenovo"],
    "Phụ kiện": ["Anker", "Baseus", "Logitech", "JBL"],
    "Đồng hồ": ["Apple", "Garmin", "Casio", "Xiaomi"],
    "Máy tính bảng": ["Apple", "Samsung", "Xiaomi"],
}
REGIONS = {
    "Miền Bắc": ["Hà Nội", "Hải Phòng", "Bắc Ninh"],
    "Miền Trung": ["Đà Nẵng", "Huế", "Nha Trang"],
    "Miền Nam": ["TP. Hồ Chí Minh", "Cần Thơ", "Bình Dương"],
}
SEGMENTS = ["VIP", "Thân thiết", "Thường", "Mới"]
AGE_GROUPS = ["18-25", "26-35", "36-45", "46-60", "60+"]
ORDER_STATUS = ["completed", "completed", "completed", "cancelled", "returned"]


def reset_tables() -> None:
    """Xóa toàn bộ bảng rồi tạo lại (DROP ALL + CREATE ALL)."""
    engine = get_engine()
    logger.warning("Reset: DROP toàn bộ bảng...")
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


def ensure_tables() -> None:
    Base.metadata.create_all(get_engine())


def already_seeded(session) -> bool:
    return session.scalar(select(func.count()).select_from(DimProduct)) > 0


def seed_dimensions(session, n_products: int, n_customers: int):
    # --- dim_branch ---
    branches: list[DimBranch] = []
    code = 1
    for region, cities in REGIONS.items():
        for city in cities:
            branches.append(
                DimBranch(
                    branch_code=f"BR{code:03d}",
                    branch_name=f"Chi nhánh {city}",
                    region=region,
                    city=city,
                    manager=fake.name(),
                )
            )
            code += 1
    session.add_all(branches)

    # --- dim_product ---
    products: list[DimProduct] = []
    for i in range(1, n_products + 1):
        category = random.choice(list(CATEGORIES))
        brand = random.choice(CATEGORIES[category])
        cost = round(random.uniform(500_000, 30_000_000), -3)
        price = round(cost * random.uniform(1.15, 1.6), -3)
        products.append(
            DimProduct(
                product_code=f"SP{i:04d}",
                product_name=f"{brand} {category} {fake.bothify('Model-##?').upper()}",
                category=category,
                brand=brand,
                unit_cost=cost,
                unit_price=price,
            )
        )
    session.add_all(products)

    # --- dim_customer ---
    customers: list[DimCustomer] = []
    for i in range(1, n_customers + 1):
        region = random.choice(list(REGIONS))
        customers.append(
            DimCustomer(
                customer_code=f"KH{i:05d}",
                customer_name=fake.name(),
                gender=random.choice(["Nam", "Nữ"]),
                age_group=random.choice(AGE_GROUPS),
                city=random.choice(REGIONS[region]),
                segment=random.choice(SEGMENTS),
            )
        )
    session.add_all(customers)

    session.flush()  # lấy id
    return branches, products, customers


def seed_dim_time(session, start: date, end: date):
    days = (end - start).days + 1
    times: list[DimTime] = []
    for offset in range(days):
        d = start + timedelta(days=offset)
        times.append(
            DimTime(
                full_date=d,
                day=d.day,
                month=d.month,
                quarter=(d.month - 1) // 3 + 1,
                year=d.year,
                weekday=d.weekday(),
                is_weekend=1 if d.weekday() >= 5 else 0,
            )
        )
    session.add_all(times)
    session.flush()
    return times


def seed_facts(session, branches, products, customers, times, n_sales: int):
    p_ids = [p.product_id for p in products]
    c_ids = [c.customer_id for c in customers]
    b_ids = [b.branch_id for b in branches]
    t_ids = [t.time_id for t in times]
    price_by_pid = {p.product_id: float(p.unit_price) for p in products}
    cost_by_pid = {p.product_id: float(p.unit_cost) for p in products}

    # --- fact_sales ---
    sales: list[FactSales] = []
    for _ in range(n_sales):
        pid = random.choice(p_ids)
        qty = random.randint(1, 5)
        unit_price = price_by_pid[pid]
        gross = unit_price * qty
        discount = round(gross * random.choice([0, 0, 0.05, 0.1]), -3)
        sales.append(
            FactSales(
                product_id=pid,
                customer_id=random.choice(c_ids),
                branch_id=random.choice(b_ids),
                time_id=random.choice(t_ids),
                quantity=qty,
                unit_price=unit_price,
                discount=discount,
                total_amount=gross - discount,
            )
        )
    session.add_all(sales)

    # --- fact_orders ---
    n_orders = max(1, n_sales // 3)
    orders: list[FactOrders] = []
    for _ in range(n_orders):
        num_items = random.randint(1, 6)
        orders.append(
            FactOrders(
                customer_id=random.choice(c_ids),
                branch_id=random.choice(b_ids),
                time_id=random.choice(t_ids),
                num_items=num_items,
                order_status=random.choice(ORDER_STATUS),
                total_value=round(random.uniform(500_000, 50_000_000), -3),
            )
        )
    session.add_all(orders)

    # --- fact_inventory: snapshot tồn kho cuối mỗi tháng cho mỗi (sp, chi nhánh) mẫu ---
    month_end_tids = {}
    for t in times:
        key = (t.year, t.month)
        # giữ time_id của ngày lớn nhất trong tháng
        if key not in month_end_tids or t.day > month_end_tids[key][1]:
            month_end_tids[key] = (t.time_id, t.day)
    snapshot_tids = [v[0] for v in month_end_tids.values()]

    inventory: list[FactInventory] = []
    sample_products = random.sample(p_ids, min(len(p_ids), 30))
    for tid in snapshot_tids:
        for bid in b_ids:
            for pid in sample_products:
                stock = random.randint(0, 200)
                inventory.append(
                    FactInventory(
                        product_id=pid,
                        branch_id=bid,
                        time_id=tid,
                        stock_quantity=stock,
                        reorder_level=random.choice([10, 20, 30]),
                        stock_value=round(stock * cost_by_pid[pid], 2),
                    )
                )
    session.add_all(inventory)

    return len(sales), len(orders), len(inventory)


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed dữ liệu mẫu cho DataMart")
    parser.add_argument("--products", type=int, default=120)
    parser.add_argument("--customers", type=int, default=300)
    parser.add_argument("--sales", type=int, default=3000)
    parser.add_argument("--start", default="2024-01-01")
    parser.add_argument("--end", default="2024-12-31")
    parser.add_argument("--reset", action="store_true", help="DROP toàn bộ trước khi seed")
    args = parser.parse_args()

    if args.reset:
        reset_tables()
    else:
        ensure_tables()

    session = get_session_factory()()
    try:
        if not args.reset and already_seeded(session):
            logger.warning(
                "DataMart đã có dữ liệu (dùng --reset để nạp lại). Bỏ qua seed."
            )
            return

        logger.info("Nạp Dimension...")
        branches, products, customers = seed_dimensions(
            session, args.products, args.customers
        )
        start = date.fromisoformat(args.start)
        end = date.fromisoformat(args.end)
        times = seed_dim_time(session, start, end)

        logger.info("Sinh Fact (sales=%d)...", args.sales)
        n_s, n_o, n_i = seed_facts(session, branches, products, customers, times, args.sales)

        session.commit()
        logger.info(
            "HOÀN TẤT seed: %d sản phẩm, %d khách, %d chi nhánh, %d ngày | "
            "fact_sales=%d, fact_orders=%d, fact_inventory=%d",
            len(products), len(customers), len(branches), len(times), n_s, n_o, n_i,
        )
    except Exception:
        session.rollback()
        logger.exception("Lỗi khi seed dữ liệu — đã rollback")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
