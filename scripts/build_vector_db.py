"""
Dựng/nạp lại ChromaDB Vector Store từ các file metadata.

Chạy (từ thư mục gốc dự án):
    python scripts/build_vector_db.py            # rebuild (xóa & dựng lại)
    python scripts/build_vector_db.py --no-reset # upsert đè, giữ collection
    python scripts/build_vector_db.py --test "doanh thu theo chi nhánh"
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND_DIR) if BACKEND_DIR.exists() else "/app")

from app.rag import loader, retriever  # noqa: E402
from app.utils import get_logger  # noqa: E402

logger = get_logger("build_vector_db")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build ChromaDB từ metadata")
    parser.add_argument("--no-reset", action="store_true", help="Upsert đè thay vì xóa & dựng lại")
    parser.add_argument("--test", metavar="QUERY", help="Sau khi build, truy hồi thử câu hỏi này")
    args = parser.parse_args()

    summary = loader.rebuild_vector_db(reset=not args.no_reset)
    logger.info(
        "Kết quả: built=%d, in_store=%d, by_type=%s",
        summary["documents_built"],
        summary["documents_in_store"],
        summary["by_type"],
    )

    if args.test:
        logger.info("Truy hồi thử: %r", args.test)
        for i, r in enumerate(retriever.retrieve(args.test), 1):
            logger.info(
                "  #%d [%s] dist=%.4f | %s",
                i, r["metadata"].get("type"), r["distance"], r["document"][:90],
            )


if __name__ == "__main__":
    main()
