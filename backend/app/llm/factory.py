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


def get_llm() -> LLMProviderInterface:
    """Trả về LLM provider (lazy singleton) theo `.env`."""
    global _instance
    if _instance is None:
        with _lock:
            if _instance is None:
                _instance = _create_provider(settings.llm_provider)
    return _instance


def reset_llm() -> None:
    """Xóa singleton (hữu ích khi đổi cấu hình lúc chạy hoặc trong test)."""
    global _instance
    _instance = None
