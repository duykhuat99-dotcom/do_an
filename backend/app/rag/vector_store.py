"""
Quản lý ChromaDB Vector Store cho metadata.

Trách nhiệm:
  - Tạo/kết nối PersistentClient (lưu xuống đĩa theo CHROMA_PERSIST_DIR).
  - Quản lý collection (get_or_create, reset).
  - Upsert tài liệu kèm embedding + metadata.
  - Similarity Search (Top-K) có hỗ trợ Metadata Filtering (where).

Ta tự tính embedding bằng app.rag.embedder (all-MiniLM-L6-v2) rồi truyền vào
Chroma, nên không phụ thuộc embedding function mặc định của Chroma.
"""
from __future__ import annotations

from threading import Lock

from app.core.config import settings
from app.utils import get_logger

logger = get_logger(__name__)

_client = None
_lock = Lock()


def get_client():
    """Trả về Chroma PersistentClient (lazy singleton)."""
    global _client
    if _client is not None:
        return _client
    with _lock:
        if _client is None:
            import chromadb
            from chromadb.config import Settings as ChromaSettings

            logger.info("Khởi tạo ChromaDB tại: %s", settings.chroma_persist_dir)
            _client = chromadb.PersistentClient(
                path=settings.chroma_persist_dir,
                settings=ChromaSettings(anonymized_telemetry=False, allow_reset=True),
            )
    return _client


def get_collection():
    """Lấy (hoặc tạo) collection metadata, dùng cosine distance."""
    return get_client().get_or_create_collection(
        name=settings.chroma_collection,
        metadata={"hnsw:space": "cosine"},
    )


def reset_collection():
    """Xóa và tạo lại collection (dùng khi rebuild toàn bộ vector DB)."""
    client = get_client()
    try:
        client.delete_collection(settings.chroma_collection)
        logger.info("Đã xóa collection cũ: %s", settings.chroma_collection)
    except Exception:
        logger.info("Collection chưa tồn tại, tạo mới: %s", settings.chroma_collection)
    return get_collection()


def upsert_documents(
    ids: list[str],
    documents: list[str],
    embeddings: list[list[float]],
    metadatas: list[dict],
) -> None:
    """Thêm/cập nhật tài liệu vào collection."""
    if not ids:
        return
    get_collection().upsert(
        ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas
    )
    logger.info("Đã upsert %d tài liệu vào vector store", len(ids))


def query(
    query_embedding: list[float],
    top_k: int | None = None,
    where: dict | None = None,
) -> list[dict]:
    """
    Similarity Search Top-K. `where` để lọc theo metadata (vd {"type": "table"}).
    Trả về list dict: {id, document, metadata, distance}.
    """
    k = top_k or settings.retrieval_top_k
    res = get_collection().query(
        query_embeddings=[query_embedding],
        n_results=k,
        where=where,
        include=["documents", "metadatas", "distances"],
    )
    out: list[dict] = []
    ids = res.get("ids", [[]])[0]
    docs = res.get("documents", [[]])[0]
    metas = res.get("metadatas", [[]])[0]
    dists = res.get("distances", [[]])[0]
    for i in range(len(ids)):
        out.append(
            {
                "id": ids[i],
                "document": docs[i],
                "metadata": metas[i],
                "distance": dists[i],
            }
        )
    return out


def count() -> int:
    """Số tài liệu hiện có trong collection."""
    try:
        return get_collection().count()
    except Exception as exc:  # collection có thể chưa tồn tại
        logger.warning("Không đếm được collection: %s", exc)
        return 0
