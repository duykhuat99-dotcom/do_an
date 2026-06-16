"""
Cấu hình tập trung cho toàn hệ thống.

Đọc biến môi trường từ file `.env` (qua pydantic-settings) và phơi bày
một đối tượng `settings` dùng chung. Mọi module khác KHÔNG đọc os.environ
trực tiếp — luôn import từ đây để đảm bảo nhất quán và dễ test.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Thư mục backend/ (chứa file .env). Trong container là /app.
BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Toàn bộ cấu hình hệ thống, ánh xạ 1-1 với các khóa trong `.env`."""

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---------- App ----------
    app_name: str = "RAG DataMart Chatbot"
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = True
    log_level: str = "INFO"
    log_dir: str = "logs"
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # ---------- MySQL ----------
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_database: str = "datamart"
    mysql_user: str = "datamart_user"
    mysql_password: str = "changeme"
    mysql_readonly_user: str | None = None
    mysql_readonly_password: str | None = None

    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout: int = 30
    db_pool_recycle: int = 1800
    db_connect_timeout: int = 5  # timeout mỗi lần kết nối (giây) — health check fail-fast

    # ---------- ChromaDB ----------
    chroma_persist_dir: str = "./chroma_db"
    chroma_collection: str = "datamart_metadata"

    # ---------- Embedding ----------
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    retrieval_top_k: int = 5

    # ---------- Text-to-SQL ----------
    sql_max_retries: int = 1  # số lần LLM tự sửa SQL khi thực thi lỗi
    history_context_turns: int = 3  # số lượt hội thoại gần nhất đưa vào ngữ cảnh (multi-turn)

    # ---------- LLM ----------
    llm_provider: str = "ollama"
    llm_model: str = "mistral:7b-instruct"
    llm_base_url: str = "http://localhost:11434"
    llm_api_key: str | None = None
    llm_temperature: float = 0.1
    llm_max_tokens: int = 1024
    llm_timeout: int = 120

    # ---------- Metadata ----------
    metadata_dir: str = "../metadata"

    # ---------- Auth (1 tài khoản cố định) ----------
    auth_username: str = "admin"
    auth_password: str = "admin123"
    jwt_secret: str = "doi-thanh-chuoi-bi-mat-ngau-nhien-dai-trong-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24 giờ

    # ----- Validators / computed -----
    @field_validator("log_level")
    @classmethod
    def _upper_log_level(cls, v: str) -> str:
        return v.upper()

    @property
    def cors_origin_list(self) -> list[str]:
        """Danh sách origin đã tách từ chuỗi cấu hình."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def database_url(self) -> str:
        """Chuỗi kết nối SQLAlchemy cho tài khoản chính (đọc/ghi history)."""
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}?charset=utf8mb4"
        )

    @property
    def readonly_database_url(self) -> str:
        """Chuỗi kết nối chỉ-đọc dùng để thực thi SQL do LLM sinh.

        Nếu chưa cấu hình tài khoản read-only thì fallback về tài khoản chính.
        """
        user = self.mysql_readonly_user or self.mysql_user
        pwd = self.mysql_readonly_password or self.mysql_password
        return (
            f"mysql+pymysql://{user}:{pwd}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}?charset=utf8mb4"
        )


@lru_cache
def get_settings() -> Settings:
    """Trả về singleton Settings (cache để không đọc lại .env mỗi lần)."""
    return Settings()


# Đối tượng dùng chung tiện import nhanh: `from app.core import settings`
settings = get_settings()
