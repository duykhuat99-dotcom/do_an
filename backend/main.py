"""
Điểm khởi chạy FastAPI cho hệ thống RAG DataMart Chatbot.

Phase 0: dựng app, CORS, logging, exception handler toàn cục và endpoint /health.
Các router nghiệp vụ (chat, generate-sql, chart, history, admin...) sẽ được
gắn dần ở các Phase sau.

Chạy:  uvicorn main:app --reload --port 8000
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api import admin, auth, chat, health, query
from app.api.deps import get_current_user
from app.core.config import settings
from app.database import dispose_engines, init_schema
from app.schemas.common import ErrorResponse
from app.utils import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Vòng đời ứng dụng: khởi tạo khi start, dọn dẹp khi shutdown."""
    logger.info("Khởi động %s (env=%s)", settings.app_name, settings.app_env)
    init_schema()  # tạo bảng thiếu (feedback) + nâng cấp cột chart_json/insight_json
    yield
    dispose_engines()
    logger.info("Tắt ứng dụng %s", settings.app_name)


app = FastAPI(
    title=settings.app_name,
    description="Chatbot AI phân tích dữ liệu DataMart bằng RAG + LLM (Multi-Agent).",
    version=health.API_VERSION,
    debug=settings.debug,
    lifespan=lifespan,
)

# ---------- Middleware ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Exception handlers toàn cục ----------
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    logger.warning("HTTP %s tại %s: %s", exc.status_code, request.url.path, exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(error=str(exc.detail)).model_dump(),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning("Lỗi validation tại %s: %s", request.url.path, exc.errors())
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error="Dữ liệu request không hợp lệ", detail=exc.errors()
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Lỗi không lường trước tại %s", request.url.path)
    detail = str(exc) if settings.debug else None
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(error="Lỗi máy chủ nội bộ", detail=detail).model_dump(),
    )


# ---------- Routers ----------
# Public: auth (đăng nhập) + health (cho Docker healthcheck & theo dõi hệ thống).
app.include_router(auth.router)
app.include_router(health.router)

# Yêu cầu đăng nhập (JWT) cho toàn bộ nghiệp vụ & quản trị RAG.
_protected = [Depends(get_current_user)]
app.include_router(admin.router, dependencies=_protected)
app.include_router(query.router, dependencies=_protected)
app.include_router(chat.router, dependencies=_protected)


@app.get("/", tags=["system"], summary="Thông tin gốc")
async def root():
    return {
        "app": settings.app_name,
        "version": health.API_VERSION,
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug,
    )
