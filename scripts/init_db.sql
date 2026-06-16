-- ============================================================
-- Khởi tạo MySQL DataMart (Star Schema) + bảng History.
-- File này được docker-compose mount vào /docker-entrypoint-initdb.d
-- để MySQL tự chạy lần đầu. Cũng có thể chạy tay:
--     mysql -u root -p < scripts/init_db.sql
-- ============================================================

CREATE DATABASE IF NOT EXISTS datamart
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE datamart;

-- ---------- DIMENSION TABLES ----------
CREATE TABLE IF NOT EXISTS dim_product (
  product_id   INT AUTO_INCREMENT PRIMARY KEY,
  product_code VARCHAR(32)  NOT NULL UNIQUE,
  product_name VARCHAR(255) NOT NULL,
  category     VARCHAR(100) NOT NULL,
  brand        VARCHAR(100) NOT NULL,
  unit_cost    DECIMAL(12,2) NOT NULL DEFAULT 0,
  unit_price   DECIMAL(12,2) NOT NULL DEFAULT 0,
  INDEX idx_product_category (category)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS dim_customer (
  customer_id   INT AUTO_INCREMENT PRIMARY KEY,
  customer_code VARCHAR(32)  NOT NULL UNIQUE,
  customer_name VARCHAR(255) NOT NULL,
  gender        VARCHAR(10)  NOT NULL,
  age_group     VARCHAR(20)  NOT NULL,
  city          VARCHAR(100) NOT NULL,
  segment       VARCHAR(50)  NOT NULL,
  INDEX idx_customer_city (city),
  INDEX idx_customer_segment (segment)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS dim_branch (
  branch_id   INT AUTO_INCREMENT PRIMARY KEY,
  branch_code VARCHAR(32)  NOT NULL UNIQUE,
  branch_name VARCHAR(255) NOT NULL,
  region      VARCHAR(50)  NOT NULL,
  city        VARCHAR(100) NOT NULL,
  manager     VARCHAR(255) NOT NULL,
  INDEX idx_branch_region (region)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS dim_time (
  time_id    INT AUTO_INCREMENT PRIMARY KEY,
  full_date  DATE NOT NULL UNIQUE,
  day        INT  NOT NULL,
  month      INT  NOT NULL,
  quarter    INT  NOT NULL,
  year       INT  NOT NULL,
  weekday    INT  NOT NULL,
  is_weekend TINYINT NOT NULL DEFAULT 0,
  INDEX idx_time_year (year),
  INDEX idx_time_month (month),
  INDEX idx_time_quarter (quarter)
) ENGINE=InnoDB;

-- ---------- FACT TABLES ----------
CREATE TABLE IF NOT EXISTS fact_sales (
  sale_id      INT AUTO_INCREMENT PRIMARY KEY,
  product_id   INT NOT NULL,
  customer_id  INT NOT NULL,
  branch_id    INT NOT NULL,
  time_id      INT NOT NULL,
  quantity     INT NOT NULL DEFAULT 0,
  unit_price   DECIMAL(12,2) NOT NULL DEFAULT 0,
  discount     DECIMAL(12,2) NOT NULL DEFAULT 0,
  total_amount DECIMAL(14,2) NOT NULL DEFAULT 0,
  FOREIGN KEY (product_id)  REFERENCES dim_product(product_id),
  FOREIGN KEY (customer_id) REFERENCES dim_customer(customer_id),
  FOREIGN KEY (branch_id)   REFERENCES dim_branch(branch_id),
  FOREIGN KEY (time_id)     REFERENCES dim_time(time_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS fact_orders (
  order_id     INT AUTO_INCREMENT PRIMARY KEY,
  customer_id  INT NOT NULL,
  branch_id    INT NOT NULL,
  time_id      INT NOT NULL,
  num_items    INT NOT NULL DEFAULT 0,
  order_status VARCHAR(20) NOT NULL,
  total_value  DECIMAL(14,2) NOT NULL DEFAULT 0,
  FOREIGN KEY (customer_id) REFERENCES dim_customer(customer_id),
  FOREIGN KEY (branch_id)   REFERENCES dim_branch(branch_id),
  FOREIGN KEY (time_id)     REFERENCES dim_time(time_id),
  INDEX idx_orders_status (order_status)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS fact_inventory (
  inventory_id   INT AUTO_INCREMENT PRIMARY KEY,
  product_id     INT NOT NULL,
  branch_id      INT NOT NULL,
  time_id        INT NOT NULL,
  stock_quantity INT NOT NULL DEFAULT 0,
  reorder_level  INT NOT NULL DEFAULT 0,
  stock_value    DECIMAL(14,2) NOT NULL DEFAULT 0,
  FOREIGN KEY (product_id) REFERENCES dim_product(product_id),
  FOREIGN KEY (branch_id)  REFERENCES dim_branch(branch_id),
  FOREIGN KEY (time_id)    REFERENCES dim_time(time_id)
) ENGINE=InnoDB;

-- ---------- HISTORY / SYSTEM TABLES ----------
CREATE TABLE IF NOT EXISTS conversation_history (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  session_id    VARCHAR(64) NOT NULL,
  role          VARCHAR(16) NOT NULL,
  question      TEXT,
  answer        TEXT,
  generated_sql TEXT,
  created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_conv_session (session_id),
  INDEX idx_conv_created (created_at)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS query_log (
  id                INT AUTO_INCREMENT PRIMARY KEY,
  session_id        VARCHAR(64) NOT NULL,
  question          TEXT NOT NULL,
  generated_sql     TEXT,
  success           TINYINT(1) NOT NULL DEFAULT 0,
  row_count         INT NOT NULL DEFAULT 0,
  execution_time_ms INT NOT NULL DEFAULT 0,
  error             TEXT,
  created_at        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_qlog_session (session_id),
  INDEX idx_qlog_created (created_at)
) ENGINE=InnoDB;

-- ---------- TÀI KHOẢN CHỈ-ĐỌC (cho Text-to-SQL guardrail, Phase 4) ----------
-- Chỉ cấp quyền SELECT → tầng phòng thủ cuối cùng nếu Validation Agent bị lọt.
CREATE USER IF NOT EXISTS 'datamart_ro'@'%' IDENTIFIED BY 'changeme';
GRANT SELECT ON datamart.* TO 'datamart_ro'@'%';
FLUSH PRIVILEGES;
