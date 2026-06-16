# Backend FastAPI — build với context = thư mục gốc dự án để copy cả metadata/.
#   docker build -f backend/Dockerfile -t datamart-backend .
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    METADATA_DIR=/metadata \
    CHROMA_PERSIST_DIR=/app/chroma_db

WORKDIR /app

# Thư viện hệ thống cần để build một số wheel (chromadb, torch...).
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ /app/
COPY metadata/ /metadata/
COPY scripts/ /scripts/

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD curl -fs http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
