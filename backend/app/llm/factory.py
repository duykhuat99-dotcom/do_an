"""
Factory chọn LLM Provider theo cấu hình `.env` (LLM_PROVIDER).

Dùng:
    from app.llm import get_llm
    llm = get_llm()
    resp = llm.generate("Xin chào", system="Bạn là trợ lý.")
"""
from __future__ import annotations

from threading import Lock

from app.core.config import settings
from app.llm.base import LLMProviderInterface
from app.utils import get_logger

logger = get_logger(__name__)

_PROVIDERS = {
    "ollama": "app.llm.ollama_provider:OllamaProvider",
    "openai_compat": "app.llm.openai_compat_provider:OpenAICompatProvider",
}

_instance: LLMProviderInterface | None = None
_lock = Lock()


def _create_provider(name: str) -> LLMProviderInterface:
    key = name.lower().strip()
    if key not in _PROVIDERS:
        raise ValueError(
            f"LLM_PROVIDER='{name}' không hợp lệ. Chọn một trong: {list(_PROVIDERS)}"
        )
    module_path, cls_name = _PROVIDERS[key].split(":")
    import importlib

    module = importlib.import_module(module_path)
    provider_cls = getattr(module, cls_name)
    logger.info("Khởi tạo LLM provider '%s' (model=%s)", key, settings.llm_model)
    return provider_cls()


def _build_one(item: dict) -> LLMProviderInterface | None:
    """Tạo 1 provider từ phần tử cấu hình chuỗi. Bỏ qua tier API thiếu key."""
    prov = (item.get("provider") or "").lower().strip()
    model = item.get("model")
    base_url = item.get("base_url")
    if prov == "ollama":
        from app.llm.ollama_provider import OllamaProvider

        return OllamaProvider(model=model, base_url=base_url)
    if prov == "openai_compat":
        key = (item.get("api_key") or "").strip()
        if not key:
            logger.info("Bỏ qua tier (chưa có API key): %s", base_url)
            return None
        from app.llm.openai_compat_provider import OpenAICompatProvider

        return OpenAICompatProvider(model=model, base_url=base_url, api_key=key)
    logger.warning("Bỏ qua tier provider không hợp lệ: %s", prov)
    return None


def _build_chain() -> LLMProviderInterface:
    """Dựng FallbackProvider từ cấu hình LLM_CHAIN; tier thiếu key sẽ bị bỏ qua."""
    from app.llm.fallback_provider import FallbackProvider

    providers = [p for p in (_build_one(i) for i in settings.llm_chain_list) if p is not None]
    if not providers:
        logger.warning("LLM_CHAIN không có tier hợp lệ -> dùng provider đơn")
        return _create_provider(settings.llm_provider)
    if len(providers) == 1:
        return providers[0]
    logger.info("Khởi tạo chuỗi fallback %d provider", len(providers))
    return FallbackProvider(providers)


def get_llm() -> LLMProviderInterface:
    """Trả về LLM provider (lazy singleton): chuỗi fallback nếu có LLM_CHAIN, ngược lại provider đơn."""
    global _instance
    if _instance is None:
        with _lock:
            if _instance is None:
                if settings.llm_chain_list:
                    _instance = _build_chain()
                else:
                    _instance = _create_provider(settings.llm_provider)
    return _instance


def reset_llm() -> None:
    """Xóa singleton (hữu ích khi đổi cấu hình lúc chạy hoặc trong test)."""
    global _instance
    _instance = None
