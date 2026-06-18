-- ============================================================
-- Khởi tạo MySQL cho DataMart "Vietnam Tour Bookings".
-- docker-compose mount file này vào /docker-entrypoint-initdb.d để chạy lần đầu.
--
-- Các bảng DataMart (DimDate, DimDestination, DimCustomerSegment, DimTour,
-- FactBooking) và bảng hệ thống được tạo tự động bởi ứng dụng / script ETL:
--     python scripts/load_tour_datamart.py
-- File này chỉ tạo database + tài khoản CHỈ-ĐỌC dùng cho guardrail Text-to-SQL.
-- ============================================================

CREATE DATABASE IF NOT EXISTS datamart
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Tài khoản chỉ-đọc (tầng phòng thủ cuối: chỉ có quyền SELECT trên toàn DB).
CREATE USER IF NOT EXISTS 'datamart_ro'@'%' IDENTIFIED BY 'changeme';
GRANT SELECT ON datamart.* TO 'datamart_ro'@'%';
FLUSH PRIVILEGES;
