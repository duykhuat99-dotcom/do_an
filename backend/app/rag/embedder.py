"""
Embedding model wrapper — sentence-transformers/all-MiniLM-L6-v2 (chạy local).

Model được nạp lười (lazy singleton) để app vẫn khởi động nhanh và không bắt buộc
cài sẵn thư viện nặng cho các tác vụ không cần embedding. Lần gọi đầu sẽ tải model
(≈90MB) về cache của HuggingFace.
"""
from __future__ import annotations

from threading import Lock

from app.core.config import settings
from app.utils import get_logger

logger = get_logger(__name__)

_model = None
_lock = Lock()
# all-MiniLM-L6-v2 sinh vector 384 chiều
EMBEDDING_DIM = 384


def _load_model():
    """Nạp SentenceTransformer (chỉ import thư viện nặng khi thực sự cần)."""
    global _model
    if _model is not None:
        return _model
    with _lock:
        if _model is None:
            from sentence_transformers import SentenceTransformer

            logger.info("Đang nạp embedding model: %s", settings.embedding_model)
            _model = SentenceTransformer(settings.embedding_model)
            logger.info("Đã nạp embedding model (dim=%d)", EMBEDDING_DIM)
    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embedding một danh sách văn bản → list vector (list[float])."""
    if not texts:
        return []
    model = _load_model()
    vectors = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=False,
        normalize_embeddings=True,  # chuẩn hóa để cosine ~ dot product
        convert_to_numpy=True,
    )
    return vectors.tolist()


def embed_query(text: str) -> list[float]:
    """Embedding một câu truy vấn → một vector."""
    return embed_texts([text])[0]
