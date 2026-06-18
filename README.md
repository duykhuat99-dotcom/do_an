# RAG DataMart Chatbot

Chatbot AI phân tích dữ liệu từ DataMart bằng **RAG (Retrieval Augmented Generation)** kết hợp **Large Language Model**, kiến trúc **Multi-Agent (6 agents)**.

> Lộ trình triển khai chi tiết theo từng giai đoạn: xem [HUONGDAN.md](HUONGDAN.md).

## Trạng thái: HOÀN THÀNH (Phase 0 → 9) ✅

| Phase | Nội dung |
|-------|----------|
| 0 | Nền móng: cấu trúc, config `.env`, logging, FastAPI, Docker hạ tầng |
| 1 | Database: SQLAlchemy pool + retry, ORM Star Schema (3 fact + 4 dim) + 2 bảng History, seed dữ liệu |
| 2 | RAG: metadata `*.yaml`, embedder `all-MiniLM-L6-v2`, ChromaDB, retriever (71 tài liệu) |
| 3 | LLM Abstraction: `LLMProviderInterface` + Ollama/OpenAI-compat, factory theo `.env`, prompt management |
| 4 | Text-to-SQL: Metadata → SQL → **Validation (guardrail)** → Executor (read-only) → DataFrame |
| 5 | Insight Agent (thống kê + tăng trưởng + LLM) & Visualization Agent (Plotly JSON) |
| 6 | History Agent + **Orchestrator** điều phối trọn 6 agent (`process_chat`) |
| 7 | API contract đầy đủ (14 endpoints) + exception handling |
| 8 | Frontend React 3 Tab (Chat / Dashboard / System) |
| 9 | Dockerfile + docker-compose (4 service) + 39 unit test + tài liệu |

## Kiến trúc

```
Frontend (React) → Backend API (FastAPI) → Orchestrator
   → Metadata Agent → RAG (ChromaDB) → SQL Agent → Validation Agent (guardrail)
   → MySQL DataMart (read-only) → Insight Agent + Visualization Agent → History Agent → Frontend
```

## Cài đặt nhanh (khuyến nghị: Docker)

```bash
# 1) Dựng toàn bộ hệ thống
docker compose up -d --build

# 2) Nạp dữ liệu mẫu + model LLM + vector DB
docker compose exec backend python /scripts/load_tour_datamart.py
docker compose exec ollama ollama pull mistral:7b-instruct
curl -X POST http://localhost:8000/rebuild-vector-db
```

- Frontend: <http://localhost>
- API docs (Swagger): <http://localhost:8000/docs>

## Cài đặt thủ công (phát triển)

**Backend**
```bash
cd backend
python -m venv .venv && .venv\Scripts\Activate.ps1   # Win; *nix: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env                                  # chỉnh MYSQL_*, LLM_* nếu cần
uvicorn main:app --reload --port 8000
```

**Dữ liệu & RAG** (cần MySQL chạy — `docker compose up -d mysql`)
```bash
python scripts/load_tour_datamart.py                   # seed Star Schema
python scripts/build_vector_db.py --test "doanh thu theo chi nhánh"
```

**Frontend**
```bash
cd frontend
npm install
cp .env.example .env                                  # VITE_API_BASE_URL=http://localhost:8000
npm run dev                                            # http://localhost:5173
```

## Kiểm thử

```bash
cd backend
pip install -r requirements-dev.txt
python -m pytest                                       # 39 test: guardrail, agents, API
```

## Danh sách API (14 endpoints)

| Nhóm | Endpoint |
|------|----------|
| Hội thoại | `POST /chat`, `POST /generate-sql`, `POST /chart`, `POST /history` |
| Hệ thống | `GET /health`, `GET /database-test`, `GET /system-status`, `GET /llm-status`, `POST /llm-test` |
| Quản trị RAG | `POST /rebuild-vector-db`, `POST /reload-metadata`, `POST /metadata-search`, `GET /vector-db-status` |

Ví dụ:
```bash
curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" \
     -d '{"question":"Doanh thu theo chi nhánh năm 2024?"}'
```

## Cấu trúc thư mục

```
do_an/
├── backend/              # FastAPI + 6 Agents + RAG + Database
│   ├── app/
│   │   ├── api/          # Routers: chat, query, admin, health
│   │   ├── agents/       # metadata, sql, validation, insight, chart, history
│   │   ├── rag/          # embedder, vector_store, loader, retriever
│   │   ├── llm/          # LLMProviderInterface + providers + factory
│   │   ├── services/     # orchestrator, text_to_sql, analysis, sql_executor
│   │   ├── database/     # connection pool, base
│   │   ├── models/       # ORM: dimensions, facts, history
│   │   ├── schemas/      # Pydantic
│   │   ├── prompts/      # prompt 4 agent
│   │   └── core/ utils/  # config, logger
│   ├── tests/            # 39 unit test (pytest)
│   ├── Dockerfile  main.py  requirements.txt
├── frontend/             # React + Vite + MUI + Plotly (3 Tab)
│   ├── src/{components,pages,services,hooks}
│   ├── Dockerfile  nginx.conf
├── metadata/             # 9 file *.yaml (schema + KPI + business rules)
├── scripts/              # init_db.sql, load_tour_datamart.py, build_vector_db.py
├── docker-compose.yml    # mysql + ollama + backend + frontend
├── HUONGDAN.md           # Lộ trình triển khai
└── README.md
```

## Công nghệ

FastAPI · SQLAlchemy 2 · MySQL 8 · ChromaDB · sentence-transformers (all-MiniLM-L6-v2) · Ollama (Mistral/Llama3/Gemma) · Pandas · Plotly · React 18 · Vite · Material UI · Docker.
