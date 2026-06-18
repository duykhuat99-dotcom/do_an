"""
ETL: nạp raw_data.csv -> Star Schema "Vietnam Tour Bookings" trong MySQL.

  - Làm sạch dữ liệu (typo điểm đến/tour, NaN -> "Không xác định").
  - Dựng 4 Dimension (DimDate, DimDestination, DimCustomerSegment, DimTour) + FactBooking.
  - XÓA các bảng DataMart cũ (fact_sales, dim_product, qlnv_chitiet, ...) và nạp mới.
  - Giữ nguyên các bảng hệ thống (conversation_history, query_log, feedback, chat_session).

Chạy (từ thư mục gốc dự án, MySQL đang chạy):
    python scripts/load_tour_datamart.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR) if BACKEND_DIR.exists() else "/app")

import pandas as pd  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.database import Base, get_engine  # noqa: E402
import app.models  # noqa: E402,F401  - đăng ký model
from app.models import (  # noqa: E402
    DimCustomerSegment,
    DimDate,
    DimDestination,
    DimTour,
    FactBooking,
)
from app.utils import get_logger  # noqa: E402

logger = get_logger("etl")

UNKNOWN = "Không xác định"

# ---------- BẢNG ÁNH XẠ (chuẩn hóa) ----------
# Điểm đến: gom mọi biến thể/typo về tên chuẩn.
DEST_CANON = {
    "Phú Quốc": "Phú Quốc", "PhuQuoc": "Phú Quốc",
    "Đà Nẵng": "Đà Nẵng", "Da Nang": "Đà Nẵng", "đà nẵng": "Đà Nẵng",
    "DNang": "Đà Nẵng", "DA NANG": "Đà Nẵng",
    "Hội An": "Hội An",
    "Nha Trang": "Nha Trang",
    "Hạ Long": "Hạ Long", "HaLongg": "Hạ Long",
    "Đà Lạt": "Đà Lạt",
    "TP.HCM": "TP.HCM", "TP HCM": "TP.HCM", "tp.hcm": "TP.HCM", "Ho Chi Minh City": "TP.HCM",
    "Huế": "Huế",
    "Hà Nội": "Hà Nội", "HA NOI": "Hà Nội", "Ha Noi": "Hà Nội",
    "Sa Pa": "Sa Pa",
    "Unknown": UNKNOWN,
}
# Tên chuẩn -> (Province, Region, DestinationType)
DEST_ATTR = {
    "Phú Quốc": ("Kiên Giang", "Miền Nam", "Island"),
    "Đà Nẵng": ("Đà Nẵng", "Miền Trung", "Beach"),
    "Hội An": ("Quảng Nam", "Miền Trung", "Historical"),
    "Nha Trang": ("Khánh Hòa", "Miền Trung", "Beach"),
    "Hạ Long": ("Quảng Ninh", "Miền Bắc", "Beach"),
    "Đà Lạt": ("Lâm Đồng", "Miền Trung", "Mountain"),
    "TP.HCM": ("TP. Hồ Chí Minh", "Miền Nam", "City"),
    "Huế": ("Thừa Thiên Huế", "Miền Trung", "Historical"),
    "Hà Nội": ("Hà Nội", "Miền Bắc", "City"),
    "Sa Pa": ("Lào Cai", "Miền Bắc", "Mountain"),
    UNKNOWN: (UNKNOWN, UNKNOWN, UNKNOWN),
}
# Nhóm khách: SegmentName -> (AgeGroup, CustomerType)
SEG_ATTR = {
    "Family": ("30-50", "Domestic"),
    "Young Professional": ("25-35", "Domestic"),
    "Student": ("18-25", "Domestic"),
    "Corporate": ("30-55", "Business"),
    UNKNOWN: (UNKNOWN, UNKNOWN),
}
# Loại tour: typo -> chuẩn
TOUR_CANON = {"bech": "Beach", "Cultral": "Cultural"}
# Tên chuẩn -> (TourName, TourCategory, DurationDays, TransportationType)
# DurationDays & TransportationType KHÔNG có trong CSV -> giá trị đại diện theo loại tour.
TOUR_ATTR = {
    "Beach": ("Tour Biển", "Domestic", 3, "Flight"),
    "Cultural": ("Tour Văn hóa", "Domestic", 3, "Bus"),
    "Family": ("Tour Gia đình", "Domestic", 4, "Flight"),
    "Adventure": ("Tour Mạo hiểm", "Domestic", 4, "Bus"),
    "City Break": ("Tour Thành phố", "Domestic", 2, "Flight"),
    "Foodie": ("Tour Ẩm thực", "Domestic", 2, "Bus"),
    UNKNOWN: ("Tour khác", "Domestic", 3, "Other"),
}

OLD_TABLES = [
    "fact_sales", "fact_orders", "fact_inventory",
    "dim_product", "dim_customer", "dim_branch", "dim_time", "qlnv_chitiet",
]
NEW_TABLES = ["FactBooking", "DimDate", "DimDestination", "DimCustomerSegment", "DimTour"]


def clean_dest(v) -> str:
    if pd.isna(v):
        return UNKNOWN
    return DEST_CANON.get(str(v).strip(), UNKNOWN)


def clean_seg(v) -> str:
    if pd.isna(v):
        return UNKNOWN
    s = str(v).strip()
    return s if s in SEG_ATTR else UNKNOWN


def clean_tour(v) -> str:
    if pd.isna(v):
        return UNKNOWN
    s = str(v).strip()
    s = TOUR_CANON.get(s, s)
    return s if s in TOUR_ATTR else UNKNOWN


def build_dim_date(dates: pd.Series) -> pd.DataFrame:
    d = pd.to_datetime(dates.dropna().unique())
    df = pd.DataFrame({"FullDate": sorted(d)})
    dt = pd.to_datetime(df["FullDate"])
    df["DateKey"] = dt.dt.strftime("%Y%m%d").astype(int)
    df["DayOfMonth"] = dt.dt.day
    df["DayName"] = dt.dt.day_name()
    df["WeekOfYear"] = dt.dt.isocalendar().week.astype(int)
    df["MonthNumber"] = dt.dt.month
    df["MonthName"] = dt.dt.month_name()
    df["QuarterNumber"] = dt.dt.quarter
    df["YearNumber"] = dt.dt.year
    df["IsWeekend"] = dt.dt.weekday >= 5
    df["FullDate"] = dt.dt.date
    return df[
        ["DateKey", "FullDate", "DayOfMonth", "DayName", "WeekOfYear",
         "MonthNumber", "MonthName", "QuarterNumber", "YearNumber", "IsWeekend"]
    ]


def main() -> None:
    csv_path = ROOT / "raw_data.csv"
    logger.info("Đọc %s", csv_path)
    df = pd.read_csv(csv_path)
    logger.info("Tổng %d dòng", len(df))

    # Làm sạch chiều
    df["dest_c"] = df["destination"].map(clean_dest)
    df["seg_c"] = df["cust_segment"].map(clean_seg)
    df["tour_c"] = df["tour_type"].map(clean_tour)
    df["bdate"] = pd.to_datetime(df["booking_date"], errors="coerce")
    df = df[df["bdate"].notna()].copy()  # bỏ dòng không có ngày đặt
    logger.info("Còn %d dòng sau khi lọc ngày hợp lệ", len(df))

    engine = get_engine()

    # 1) Xóa bảng cũ + bảng mới (để chạy lại được), giữ bảng hệ thống
    with engine.begin() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS=0"))
        for t in OLD_TABLES + NEW_TABLES:
            conn.execute(text(f"DROP TABLE IF EXISTS `{t}`"))
        conn.execute(text("SET FOREIGN_KEY_CHECKS=1"))
    logger.info("Đã xóa bảng DataMart cũ + mới")

    # 2) Tạo lại bảng mới (chỉ DataMart; history giữ nguyên)
    Base.metadata.create_all(engine, tables=[
        Base.metadata.tables[t] for t in NEW_TABLES
    ])
    logger.info("Đã tạo 5 bảng Star Schema")

    # 3) Dimension DataFrames + gán surrogate key
    dim_date = build_dim_date(df["bdate"])

    dests = [d for d in DEST_ATTR if d in set(df["dest_c"])]
    dim_dest = pd.DataFrame({"DestinationKey": range(1, len(dests) + 1), "DestinationName": dests})
    dim_dest[["Province", "Region", "DestinationType"]] = [DEST_ATTR[d] for d in dests]
    dest_key = dict(zip(dim_dest["DestinationName"], dim_dest["DestinationKey"]))

    segs = [s for s in SEG_ATTR if s in set(df["seg_c"])]
    dim_seg = pd.DataFrame({"SegmentKey": range(1, len(segs) + 1), "SegmentName": segs})
    dim_seg[["AgeGroup", "CustomerType"]] = [SEG_ATTR[s] for s in segs]
    seg_key = dict(zip(dim_seg["SegmentName"], dim_seg["SegmentKey"]))

    tours = [t for t in TOUR_ATTR if t in set(df["tour_c"])]
    dim_tour = pd.DataFrame({"TourKey": range(1, len(tours) + 1)})
    dim_tour[["TourName", "TourCategory", "DurationDays", "TransportationType"]] = [
        TOUR_ATTR[t] for t in tours
    ]
    tour_key = {t: i + 1 for i, t in enumerate(tours)}

    # 4) Fact
    fact = pd.DataFrame()
    fact["DateKey"] = df["bdate"].dt.strftime("%Y%m%d").astype(int)
    fact["DestinationKey"] = df["dest_c"].map(dest_key)
    fact["SegmentKey"] = df["seg_c"].map(seg_key)
    fact["TourKey"] = df["tour_c"].map(tour_key)
    fact["Revenue"] = pd.to_numeric(df["revenue_vnd"], errors="coerce").fillna(0)
    fact["Pax"] = pd.to_numeric(df["pax"], errors="coerce").fillna(0).astype(int)
    fact["BookingCount"] = 1
    fact["SatisfactionScore"] = pd.to_numeric(df["satisfaction"], errors="coerce")

    # 5) Nạp (dimension trước, fact sau)
    dim_date.to_sql("DimDate", engine, if_exists="append", index=False)
    dim_dest.to_sql("DimDestination", engine, if_exists="append", index=False)
    dim_seg.to_sql("DimCustomerSegment", engine, if_exists="append", index=False)
    dim_tour.to_sql("DimTour", engine, if_exists="append", index=False)
    fact.to_sql("FactBooking", engine, if_exists="append", index=False, chunksize=1000)

    logger.info(
        "HOÀN TẤT: DimDate=%d, DimDestination=%d, DimCustomerSegment=%d, DimTour=%d, FactBooking=%d",
        len(dim_date), len(dim_dest), len(dim_seg), len(dim_tour), len(fact),
    )


if __name__ == "__main__":
    main()
