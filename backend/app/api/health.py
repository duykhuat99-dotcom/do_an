"""Router kiểm tra sức khỏe hệ thống (Phase 0).

Ở Phase 0 mới chỉ kiểm tra app sống. Các kiểm tra MySQL / VectorDB / LLM
sẽ được bổ sung ở các Phase sau (database-test, system status...).
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.database import check_database_connection
from app.llm import LLMError, get_llm
from app.rag import vector_store
from app.schemas.chat import ComponentHealth, SystemStatusResponse
from app.schemas.common import HealthResponse
from app.schemas.llm import LLMTestRequest, LLMTestResponse

router = APIRouter(tags=["system"])

API_VERSION = "0.1.0"


@router.get("/health", response_model=HealthResponse, summary="Liveness check")
async def health() -> HealthResponse:
    """Trả về trạng thái cơ bản của ứng dụng."""
    return HealthResponse(
        status="ok",
        app_name=settings.app_name,
        app_env=settings.app_env,
        version=API_VERSION,
    )


@router.get("/database-test", summary="Kiểm tra kết nối MySQL DataMart")
async def database_test() -> dict[str, object]:
    """Ping MySQL (có retry) và trả về trạng thái + độ trễ."""
    return check_database_connection()


@router.get("/llm-status", summary="Kiểm tra kết nối LLM")
async def llm_status() -> dict[str, object]:
    """Kiểm tra provider LLM theo cấu hình `.env` (không sinh văn bản)."""
    return get_llm().health_check()


@router.get("/system-status", response_model=SystemStatusResponse, summary="Trạng thái toàn hệ thống")
async def system_status() -> SystemStatusResponse:
    """Tổng hợp trạng thái MySQL + Vector DB + LLM (cho Tab System Management)."""
    db = check_database_connection()
    mysql = ComponentHealth(
        healthy=bool(db.get("healthy")),
        detail=str(db.get("detail")),
        info={k: v for k, v in db.items() if k not in ("healthy", "detail")},
    )

    try:
        doc_count = vector_store.count()
        vdb = ComponentHealth(
            healthy=doc_count > 0,
            detail=(
                f"{doc_count} tài liệu" if doc_count > 0
                else "Vector DB trống — hãy chạy /rebuild-vector-db"
            ),
            info={"documents_in_store": doc_count, "collection": settings.chroma_collection},
        )
    except Exception as exc:  # noqa: BLE001
        vdb = ComponentHealth(healthy=False, detail=str(exc))

    try:
        hc = get_llm().health_check()
        llm = ComponentHealth(
            healthy=bool(hc.get("healthy")),
            detail=str(hc.get("detail")),
            info={k: v for k, v in hc.items() if k not in ("healthy", "detail")},
        )
    except Exception as exc:  # noqa: BLE001
        llm = ComponentHealth(healthy=False, detail=str(exc))

    return SystemStatusResponse(mysql=mysql, vector_db=vdb, llm=llm)


@router.post("/llm-test", response_model=LLMTestResponse, summary="Sinh thử văn bản từ LLM")
async def llm_test(req: LLMTestRequest) -> LLMTestResponse:
    """Gọi LLM sinh văn bản — dùng để kiểm thử provider/model."""
    try:
        resp = get_llm().generate(
            req.prompt, system=req.system, max_tokens=req.max_tokens
        )
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return LLMTestResponse(
        provider=resp.provider,
        model=resp.model,
        text=resp.text,
        latency_ms=resp.latency_ms,
        prompt_tokens=resp.prompt_tokens,
        completion_tokens=resp.completion_tokens,
    )
