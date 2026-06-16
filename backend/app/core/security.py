"""
Tiện ích bảo mật: tạo & giải mã JWT access token.

Hệ thống chỉ có 1 tài khoản cố định (cấu hình trong `.env`), nên không cần bảng
users hay băm mật khẩu. Token mang `sub` = username và thời hạn `exp`.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import settings


def create_access_token(subject: str) -> str:
    """Tạo JWT cho user (subject), hết hạn theo cấu hình."""
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict:
    """Giải mã & kiểm tra JWT. Ném jwt.PyJWTError nếu sai/hết hạn."""
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
