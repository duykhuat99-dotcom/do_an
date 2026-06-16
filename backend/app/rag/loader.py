"""
Nạp metadata (YAML/JSON) -> tài liệu (documents) -> embedding -> ChromaDB.

CHỈ embedding siêu dữ liệu & tri thức nghiệp vụ (KHÔNG embedding dữ liệu fact dòng).
Sinh tài liệu ở nhiều mức để retrieval linh hoạt:
  - 1 tài liệu / bảng     (type=table)
  - 1 tài liệu / cột      (type=column)
  - 1 tài liệu / KPI      (type=kpi)
  - 1 tài liệu / quy tắc  (type=business_rule)

Mỗi tài liệu kèm metadata để hỗ trợ Metadata Filtering khi truy hồi.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from app.core.config import BASE_DIR, settings
from app.rag import embedder, vector_store
from app.utils import get_logger

logger = get_logger(__name__)


def _metadata_path() -> Path:
    """Đường dẫn tuyệt đối tới thư mục metadata."""
    p = Path(settings.metadata_dir)
    return p if p.is_absolute() else (BASE_DIR / p).resolve()


def _load_file(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in (".yaml", ".yml"):
        return yaml.safe_load(text) or {}
    if path.suffix.lower() == ".json":
        return json.loads(text)
    return {}


def _clean_meta(meta: dict) -> dict:
    """Chroma chỉ nhận str/int/float/bool; loại None và ép list->chuỗi."""
    out = {}
    for k, v in meta.items():
        if v is None:
            continue
        if isinstance(v, (list, tuple)):
            out[k] = ", ".join(str(x) for x in v)
        elif isinstance(v, (str, int, float, bool)):
            out[k] = v
        else:
            out[k] = str(v)
    return out


def _docs_from_table(data: dict) -> list[dict]:
    """Sinh tài liệu cho một file mô tả bảng (table + các cột)."""
    table = data["table"]
    ttype = data.get("type", "table")
    desc = (data.get("description") or "").strip()
    grain = (data.get("grain") or "").strip()
    columns = data.get("columns", []) or []

    docs: list[dict] = []

    # Tài liệu cấp bảng: gồm mô tả + liệt kê cột để trả lời "dùng bảng nào".
    col_summary = "; ".join(
        f"{c['name']} ({c.get('type','')}): {c.get('description','').strip()}"
        for c in columns
    )
    table_text = (
        f"Bảng {table} (loại {ttype}). {desc} "
        f"Grain: {grain} Các cột: {col_summary}"
    )
    docs.append(
        {
            "id": f"table::{table}",
            "text": table_text,
            "metadata": _clean_meta(
                {"type": "table", "table": table, "table_type": ttype}
            ),
        }
    )

    # Tài liệu cấp cột: chi tiết từng cột, kèm khóa ngoại nếu có.
    for c in columns:
        fk = c.get("foreign_key")
        col_text = (
            f"Cột {table}.{c['name']} kiểu {c.get('type','')}. "
            f"{c.get('description','').strip()}"
        )
        if fk:
            col_text += f" Khóa ngoại tới {fk}."
        docs.append(
            {
                "id": f"column::{table}.{c['name']}",
                "text": col_text,
                "metadata": _clean_meta(
                    {
                        "type": "column",
                        "table": table,
                        "column": c["name"],
                        "data_type": c.get("type"),
                        "foreign_key": fk,
                        "is_measure": bool(c.get("measure", False)),
                    }
                ),
            }
        )
    return docs


def _docs_from_kpis(data: dict) -> list[dict]:
    docs: list[dict] = []
    for kpi in data.get("kpis", []) or []:
        aliases = ", ".join(kpi.get("aliases", []) or [])
        text = (
            f"KPI '{kpi['name']}' (còn gọi: {aliases}). "
            f"{kpi.get('definition','').strip()} "
            f"Công thức: {kpi.get('formula','').strip()}"
        )
        docs.append(
            {
                "id": f"kpi::{kpi['name']}",
                "text": text,
                "metadata": _clean_meta(
                    {
                        "type": "kpi",
                        "name": kpi["name"],
                        "tables": kpi.get("tables"),
                        "formula": kpi.get("formula"),
                    }
                ),
            }
        )
    return docs


def _docs_from_rules(data: dict) -> list[dict]:
    docs: list[dict] = []
    for rule in data.get("business_rules", []) or []:
        text = (
            f"Quy tắc nghiệp vụ {rule.get('id','')} - {rule.get('name','')}: "
            f"{rule.get('description','').strip()}"
        )
        docs.append(
            {
                "id": f"rule::{rule.get('id', rule.get('name'))}",
                "text": text,
                "metadata": _clean_meta(
                    {
                        "type": "business_rule",
                        "rule_id": rule.get("id"),
                        "name": rule.get("name"),
                        "tables": rule.get("tables"),
                    }
                ),
            }
        )
    return docs


def build_documents() -> list[dict]:
    """Đọc mọi file metadata và sinh toàn bộ tài liệu để embedding."""
    meta_dir = _metadata_path()
    if not meta_dir.exists():
        raise FileNotFoundError(f"Không tìm thấy thư mục metadata: {meta_dir}")

    files = sorted(
        [p for p in meta_dir.iterdir() if p.suffix.lower() in (".yaml", ".yml", ".json")]
    )
    logger.info("Tìm thấy %d file metadata tại %s", len(files), meta_dir)

    docs: list[dict] = []
    for path in files:
        data = _load_file(path)
        if not data:
            continue
        if "table" in data:
            docs.extend(_docs_from_table(data))
        elif "kpis" in data:
            docs.extend(_docs_from_kpis(data))
        elif "business_rules" in data:
            docs.extend(_docs_from_rules(data))
        else:
            logger.warning("Bỏ qua file không nhận dạng được: %s", path.name)

    logger.info("Đã sinh %d tài liệu metadata", len(docs))
    return docs


def rebuild_vector_db(reset: bool = True) -> dict[str, Any]:
    """
    Nạp lại toàn bộ metadata vào ChromaDB.
      - reset=True  : xóa collection cũ rồi nạp lại (dùng cho /rebuild-vector-db).
      - reset=False : upsert đè (dùng cho /reload-metadata).
    """
    docs = build_documents()
    if reset:
        vector_store.reset_collection()

    ids = [d["id"] for d in docs]
    texts = [d["text"] for d in docs]
    metadatas = [d["metadata"] for d in docs]

    logger.info("Đang embedding %d tài liệu...", len(texts))
    embeddings = embedder.embed_texts(texts)
    vector_store.upsert_documents(ids, texts, embeddings, metadatas)

    total = vector_store.count()
    summary = {
        "documents_built": len(docs),
        "documents_in_store": total,
        "reset": reset,
        "by_type": _count_by_type(metadatas),
    }
    logger.info("Hoàn tất build vector DB: %s", summary)
    return summary


def _count_by_type(metadatas: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for m in metadatas:
        t = m.get("type", "unknown")
        counts[t] = counts.get(t, 0) + 1
    return counts
