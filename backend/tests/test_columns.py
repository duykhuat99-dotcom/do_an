"""Kiểm thử nhận diện cột thời gian (tránh false positive name<->nam)."""
import pandas as pd

from app.agents.columns import find_time_column, is_time_column


def test_detect_vietnamese_no_diacritics():
    assert is_time_column("thang") is True
    assert is_time_column("nam") is True


def test_detect_english():
    assert is_time_column("month") is True
    assert is_time_column("full_date") is True


def test_name_not_misdetected_as_time():
    # 'customer_name' chứa 'name' nhưng KHÔNG được nhận là 'nam'
    assert is_time_column("customer_name") is False


def test_measure_not_time():
    assert is_time_column("doanh_thu") is False
    assert is_time_column("total_amount") is False


def test_find_time_column_in_df():
    df = pd.DataFrame({"thang": [1, 2], "doanh_thu": [10, 20]})
    assert find_time_column(df) == "thang"


def test_find_time_column_datetime_dtype():
    df = pd.DataFrame({"ts": pd.to_datetime(["2024-01-01", "2024-02-01"]), "v": [1, 2]})
    assert find_time_column(df) == "ts"
