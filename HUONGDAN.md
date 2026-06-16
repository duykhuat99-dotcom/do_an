# Hướng Dẫn Triển Khai Đồ Án

## Đề tài: Ứng dụng RAG & Large Language Model trong xây dựng Chatbot AI phân tích dữ liệu từ DataMart

> Tài liệu này tóm tắt cách hiểu kiến trúc và đề xuất **lộ trình triển khai mã nguồn theo từng giai đoạn (Phase)** — đi từ tầng Database/RAG cơ bản lên tới Multi-Agent và Frontend. Mục tiêu: làm tới đâu chắc tới đó, tránh quá tải, giữ chất lượng code chuẩn Production.

---

## 1. Xác nhận cách hiểu kiến trúc

### 1.1. Luồng dữ liệu tổng thể (Micro-Agent + RAG Layer)

```
Người dùng
   │  (câu hỏi ngôn ngữ tự nhiên)
   ▼
Frontend (React + Vite + MUI + Plotly)
   │  POST /chat
   ▼
Backend API (FastAPI)
   │
   ▼
AI Orchestrator  ───────────────────────────────┐
   │ 1. Metadata Agent → RAG Engine (Retriever + ChromaDB)
   │       └─ trả về Schema Context (bảng, cột, KPI, business rules liên quan)
   │ 2. SQL Agent → sinh câu lệnh MySQL từ câu hỏi + Schema Context
   │ 3. Validation Agent (Guardrail) → Regex + LLM chặn lệnh phá hoại
   │ 4. Thực thi SQL → MySQL DataMart (Star Schema) → Pandas DataFrame
   │ 5. Insight Agent → phân tích DataFrame (tăng trưởng, xu hướng, KPI…)
   │ 6. Visualization Agent → chọn loại chart + đóng gói Plotly JSON
   │ 7. History Agent → ghi lịch sử hội thoại + SQL + thời gian + kết quả
   └───────────────────────────────────────────────┘
   │
   ▼
Response (answer + SQL + chart config + insight + execution_time)
   ▼
Frontend hiển thị
```

### 1.2. Nguyên tắc RAG cốt lõi (RẤT QUAN TRỌNG)

- **KHÔNG embedding dữ liệu Fact dòng** (không nhúng từng dòng giao dịch).
- **Chỉ embedding Metadata + Business Knowledge**: tên bảng, mô tả bảng, tên cột, mô tả cột, định nghĩa KPI, Business Rules, Data Dictionary.
- Metadata lưu dưới dạng file `metadata/*.yaml` hoặc `metadata/*.json`.
- Embedding Model: `sentence-transformers/all-MiniLM-L6-v2` (chạy local, nhẹ, 384 chiều).
- Vector DB: **ChromaDB** (Collection, Similarity Search, Top-K Retrieval, Metadata Filtering).

→ Khi người dùng hỏi, ta truy hồi *ngữ cảnh schema* phù hợp rồi đưa cho LLM sinh SQL. LLM **không bao giờ thấy dữ liệu thật trong vector store**, chỉ thấy mô tả cấu trúc.

### 1.3. Tầng dữ liệu — Star Schema

| Loại | Bảng |
|------|------|
| Fact Tables | `fact_sales`, `fact_orders`, `fact_inventory` |
| Dimension Tables | `dim_product`, `dim_customer`, `dim_time`, `dim_branch` |
| History | bảng lưu hội thoại, SQL đã sinh, thời gian thực thi, kết quả |

- Kết nối qua **SQLAlchemy** (Connection Pool, Health Check, Retry, Logging).
- Cấu hình qua `.env`: `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD`.

### 1.4. LLM Abstraction Layer

- Interface trừu tượng `LLMProviderInterface` → đổi model qua `.env` không sửa code.
- Hỗ trợ model mã nguồn mở: **Mistral 7B Instruct, Llama 3 8B Instruct, Gemma 2B** (local qua Ollama / vLLM, hoặc API).

### 1.5. Sáu (6) Agents

| # | Agent | Nhiệm vụ |
|---|-------|----------|
| 1 | **Metadata Agent** | Tìm schema/table/column + business rules liên quan từ ChromaDB |
| 2 | **SQL Agent** | Sinh câu lệnh MySQL đúng cú pháp từ câu hỏi + Schema Context |
| 3 | **Validation Agent** | Guardrail — Regex + LLM chặn `DROP/DELETE/TRUNCATE/ALTER/UPDATE/INSERT` |
| 4 | **Insight Agent** | Phân tích DataFrame: tăng trưởng, xu hướng, KPI, so sánh kỳ trước |
| 5 | **Visualization Agent** | Chọn loại chart (Bar/Line/Pie/Area/Scatter) → Plotly JSON |
| 6 | **History Agent** | Ghi/đọc lịch sử hội thoại vào database |

---

## 2. Cấu trúc thư mục mục tiêu

```
do_an/
├── backend/
│   ├── app/
│   │   ├── api/          # Endpoints & Routers (FastAPI)
│   │   ├── agents/       # 6 Agents (metadata, sql, validation, insight, chart, history)
│   │   ├── rag/          # Embedding & ChromaDB Engine
│   │   ├── database/     # SQLAlchemy, Connection Pool, History Models
│   │   ├── services/     # Orchestrator & Business Logic
│   │   ├── prompts/      # Quản lý prompt cho từng Agent
│   │   ├── models/       # SQLAlchemy ORM models
│   │   ├── schemas/      # Pydantic Request/Response Schemas
│   │   ├── core/         # Config (.env loader), constants
│   │   ├── llm/          # LLMProviderInterface + providers
│   │   └── utils/        # Logger & Helpers
│   ├── main.py           # Entry point FastAPI
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/   # Chat, Chart, Status components
│   │   ├── pages/        # 3 Tab pages
│   │   ├── services/     # Axios API layer
│   │   └── hooks/
│   ├── package.json
│   └── vite.config.js
├── metadata/             # *.yaml / *.json mô tả schema + KPI + business rules
├── scripts/              # seed DB, build vector DB, init data
├── docker-compose.yml    # MySQL + ChromaDB + (Ollama) + backend + frontend
├── HUONGDAN.md           # (file này)
└── README.md
```

---

## 3. Lộ trình triển khai theo Giai đoạn (Phase)

Triển khai **từ dưới lên (bottom-up)**: dữ liệu → RAG → LLM → Agents → API → Frontend. Mỗi Phase có sản phẩm chạy được và kiểm thử được trước khi sang Phase sau.

### 🟢 Phase 0 — Khởi tạo & Nền móng (Foundation)
**Mục tiêu:** Dựng khung dự án, config, môi trường chạy.
- Tạo cấu trúc thư mục `backend/`, `frontend/`, `metadata/`, `scripts/`.
- `requirements.txt` (FastAPI, SQLAlchemy, PyMySQL, ChromaDB, sentence-transformers, pandas, plotly, pydantic-settings…).
- `core/config.py` đọc `.env` bằng `pydantic-settings`; tạo `.env.example`.
- `utils/logger.py` — logging chuẩn (rotating file + console).
- `docker-compose.yml` cho MySQL (và tùy chọn Ollama).
- **Output:** `uvicorn main:app` chạy được, trả `/health` cơ bản.

### 🟢 Phase 1 — Tầng Database & DataMart
**Mục tiêu:** Kết nối MySQL, dựng Star Schema, có dữ liệu mẫu.
- `database/connection.py` — SQLAlchemy Engine + Connection Pool + Health Check + Retry.
- `models/` — ORM cho `fact_*`, `dim_*`, và bảng `conversation_history`, `query_log`.
- `scripts/init_db.sql` + `scripts/seed_data.py` — tạo bảng và sinh dữ liệu mẫu (dùng Faker).
- Endpoint `/database-test` kiểm tra kết nối.
- **Output:** DB có dữ liệu thật, query thử bằng SQLAlchemy thành công.

### 🟢 Phase 2 — Metadata & RAG Engine
**Mục tiêu:** Có vector store mô tả schema, retrieve được context.
- Viết các file `metadata/*.yaml`: mô tả từng bảng, cột, KPI, business rules, data dictionary.
- `rag/embedder.py` — load `all-MiniLM-L6-v2`, hàm `embed(texts)`.
- `rag/vector_store.py` — ChromaDB client, tạo collection, upsert, similarity search, metadata filter.
- `rag/loader.py` — đọc YAML → chuẩn hóa thành "documents" → embed → nạp vào Chroma.
- `scripts/build_vector_db.py` — chạy 1 lệnh để build/rebuild vector DB.
- Endpoints `/reload-metadata`, `/rebuild-vector-db`.
- **Output:** Truy vấn "doanh thu theo chi nhánh" → trả đúng bảng `fact_sales`, `dim_branch`.

### 🟢 Phase 3 — LLM Abstraction Layer
**Mục tiêu:** Gọi được LLM, đổi model qua `.env`.
- `llm/base.py` — `LLMProviderInterface` (abstract: `generate(prompt, system, ...)`).
- `llm/ollama_provider.py` (Mistral/Llama3/Gemma), tùy chọn `llm/openai_compat_provider.py`.
- `llm/factory.py` — chọn provider theo `LLM_PROVIDER` trong `.env`.
- `prompts/` — template prompt cho từng agent (giữ tách biệt khỏi logic).
- **Output:** Gọi `llm.generate("Hello")` trả về text từ model local.

### 🟢 Phase 4 — Các Agent cốt lõi (Text-to-SQL Pipeline)
**Mục tiêu:** Từ câu hỏi → SQL an toàn → kết quả.
- `agents/metadata_agent.py` — gọi RAG lấy Schema Context.
- `agents/sql_agent.py` — ghép câu hỏi + context + prompt → sinh SQL (chỉ `SELECT`).
- `agents/validation_agent.py` — **Guardrail**: Regex chặn từ khóa nguy hiểm + LLM double-check; chỉ cho phép `SELECT`.
- `services/sql_executor.py` — thực thi SQL an toàn (read-only user, LIMIT, timeout) → Pandas DataFrame.
- **Output:** Hỏi → SQL hợp lệ → DataFrame kết quả; lệnh phá hoại bị chặn.

### 🟢 Phase 5 — Insight & Visualization Agents
**Mục tiêu:** Biến số liệu thành phân tích + biểu đồ.
- `agents/insight_agent.py` — phân tích DataFrame (tổng, trung bình, tăng trưởng %, top N, so sánh kỳ trước) → văn bản insight.
- `agents/chart_agent.py` — suy luận loại chart phù hợp → trả **Plotly JSON config**.
- **Output:** Có `insight` + `chart_config` sẵn sàng cho frontend.

### 🟢 Phase 6 — Orchestrator & History Agent
**Mục tiêu:** Ghép toàn bộ pipeline + lưu vết.
- `services/orchestrator.py` — điều phối: Metadata → SQL → Validation → Execute → Insight → Chart → History.
- `agents/history_agent.py` — ghi/đọc `conversation_history` (session, câu hỏi, SQL, thời gian, kết quả).
- Quản lý `session_id` để duy trì context phiên.
- **Output:** Một hàm `process_chat(question, session_id)` chạy trọn vẹn end-to-end.

### 🟢 Phase 7 — Backend API (FastAPI Contract)
**Mục tiêu:** Phơi bày API chuẩn với Pydantic + Exception Handling.
- `schemas/` — Request/Response cho mọi endpoint.
- `api/` routers:
  - `POST /chat` — hội thoại chính (full pipeline).
  - `POST /generate-sql` — chỉ sinh SQL.
  - `POST /chart` — sinh chart config.
  - `POST /history` — lấy lịch sử.
  - `GET /health`, `GET /database-test`.
  - `POST /reload-metadata`, `POST /rebuild-vector-db`.
- Middleware: CORS, exception handler toàn cục, request logging.
- **Output:** Swagger `/docs` đầy đủ, test bằng curl/Postman OK.

### 🟢 Phase 8 — Frontend (React SPA — 3 Tab)
**Mục tiêu:** Giao diện hoàn chỉnh.
- Khởi tạo Vite + React + Material UI + Axios + Plotly.
- `services/api.js` — Axios layer gọi backend.
- **Tab 1 — Chat Assistant:** khung chat, hiển thị SQL sinh ra, câu trả lời, execution_time.
- **Tab 2 — Analytics Dashboard:** câu hỏi + SQL + biểu đồ Plotly tương tác + AI Insight.
- **Tab 3 — System Management:** trạng thái real-time MySQL / Vector DB / LLM.
- **Output:** Người dùng hỏi và nhận trả lời + biểu đồ trực quan.

### 🟢 Phase 9 — Hoàn thiện & Đóng gói (Production-ready)
**Mục tiêu:** Chuẩn hóa, kiểm thử, tài liệu.
- Unit/integration test (pytest) cho agents & guardrail.
- Dockerfile backend + frontend, hoàn thiện `docker-compose`.
- `README.md`, hướng dẫn cài đặt, ảnh demo, sơ đồ kiến trúc.
- Xử lý lỗi biên, rate limit, caching kết quả retrieve.
- **Output:** Hệ thống chạy bằng `docker-compose up`, sẵn sàng bảo vệ đồ án.

---

## 4. Bảng phụ thuộc giữa các Phase

```
Phase 0 ─► Phase 1 ─► Phase 2 ─► Phase 4 ─► Phase 5 ─► Phase 6 ─► Phase 7 ─► Phase 8 ─► Phase 9
                 └────► Phase 3 ─────────────┘
```
- Phase 3 (LLM) song song được với Phase 1–2.
- Phase 4 cần xong Phase 2 (RAG) + Phase 3 (LLM).

---

## 5. Ngăn xếp công nghệ đề xuất

| Tầng | Công nghệ |
|------|-----------|
| Frontend | React 18, Vite, Material UI, Axios, react-plotly.js |
| Backend | FastAPI, Uvicorn, Pydantic v2, pydantic-settings |
| ORM/DB | SQLAlchemy 2.x, PyMySQL, MySQL 8 |
| RAG | ChromaDB, sentence-transformers (all-MiniLM-L6-v2) |
| LLM | Ollama (Mistral 7B / Llama 3 8B / Gemma 2B) |
| Data | Pandas, NumPy |
| Hạ tầng | Docker, docker-compose |

---

## 6. Bước tiếp theo

Tôi đã nắm rõ toàn bộ: kiến trúc Micro-Agent + RAG, luồng dữ liệu, nhiệm vụ 6 Agents, nguyên tắc "chỉ embedding metadata", và cấu trúc thư mục.

**Bạn muốn bắt đầu viết code chi tiết từ Giai đoạn nào trước?**
- Gợi ý đi tuần tự: **Phase 0 → Phase 1** (dựng nền + Database/DataMart) để có dữ liệu thật làm việc.
- Nếu muốn thấy "linh hồn" hệ thống sớm: bắt đầu **Phase 2 (RAG Engine)**.

Hãy cho tôi biết Phase bạn chọn, tôi sẽ viết mã nguồn đầy đủ cho Phase đó.
