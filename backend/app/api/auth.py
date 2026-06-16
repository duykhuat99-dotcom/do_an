"""
Router xác thực — đăng nhập 1 tài khoản cố định (cấu hình trong `.env`).

  - POST /auth/login : kiểm tra username/password, trả JWT.
  - GET  /auth/me    : thông tin user hiện tại (yêu cầu token hợp lệ).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.security import create_access_token
from app.schemas.auth import LoginRequest, TokenResponse, UserInfo
from app.utils import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["auth"])


@router.post("/auth/login", response_model=TokenResponse, summary="Đăng nhập")
async def login(req: LoginRequest) -> TokenResponse:
    """So khớp với tài khoản cố định trong cấu hình; trả về JWT nếu đúng."""
    if req.username != settings.auth_username or req.password != settings.auth_password:
        logger.warning("Đăng nhập thất bại cho user=%s", req.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sai tài khoản hoặc mật khẩu",
        )
    token = create_access_token(req.username)
    logger.info("Đăng nhập thành công: %s", req.username)
    return TokenResponse(
        access_token=token,
        username=req.username,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.get("/auth/me", response_model=UserInfo, summary="Thông tin user hiện tại")
async def me(user: str = Depends(get_current_user)) -> UserInfo:
    return UserInfo(username=user)
