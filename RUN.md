# Hướng Dẫn Chạy Dự Án — RAG DataMart Chatbot

Tài liệu này hướng dẫn chạy hệ thống từ A→Z theo **2 cách**:
- **Cách A — Docker** (khuyến nghị, ít thao tác nhất).
- **Cách B — Chạy thủ công** (phù hợp khi phát triển / sửa code).

---

## 0. Yêu cầu hệ thống

| Thành phần | Phiên bản | Ghi chú |
|-----------|-----------|---------|
| Docker + Docker Compose | 24+ | Cho Cách A |
| Python | 3.12 | Cho Cách B (backend) |
| Node.js + npm | 20+ | Cho Cách B (frontend) |
| MySQL | 8.0 | Có thể chạy bằng Docker |
| Ollama | mới nhất | Chạy LLM local (mặc định `qwen2.5:1.5b`, nhẹ) |
| RAM trống | ≥ 4GB | `qwen2.5:1.5b` cần ~1.5GB khi suy luận |

> Lần đầu chạy sẽ tự tải: embedding model `all-MiniLM-L6-v2` (~90MB) và model LLM `qwen2.5:1.5b` (~1GB). Cần kết nối Internet cho lần đầu.
>
> Muốn dùng model khác (local nhẹ hơn/nặng hơn) hoặc **API key** (OpenRouter/Groq/DeepSeek/Gemini...): xem phần [Đổi model LLM](#đổi-model-llm) và các preset trong [backend/.env.example](backend/.env.example).

---

## Cách A — Chạy bằng Docker (khuyến nghị)

### A1. Dựng toàn bộ hệ thống
Tại thư mục gốc dự án (`do_an/`):
```bash
docker compose up -d --build
```
Lệnh này khởi động 4 service: **mysql**, **ollama**, **backend**, **frontend**.

Kiểm tra trạng thái container:
```bash
docker compose ps
```

### A2. Nạp dữ liệu mẫu vào DataMart
```bash
docker compose exec backend python /scripts/seed_data.py --reset
```
> Sinh dữ liệu Star Schema mẫu (sản phẩm, khách hàng, chi nhánh, thời gian + fact bán hàng/đơn hàng/tồn kho).

### A3. Tải model LLM về Ollama
```bash
docker compose exec ollama ollama pull qwen2.5:1.5b
```
> Mặc định dùng `qwen2.5:1.5b` (nhẹ). Có thể đổi sang `qwen2.5-coder:1.5b` (SQL tốt hơn), `qwen2.5:3b`, `gemma2:2b`... — nhớ sửa `LLM_MODEL` trong [docker-compose.yml](docker-compose.yml) cho khớp. Xem [Đổi model LLM](#đổi-model-llm).

### A4. Dựng Vector DB (RAG)
```bash
curl -X POST http://localhost:8000/rebuild-vector-db
```
> Embedding metadata (schema + KPI + business rules) vào ChromaDB.

### A5. Truy cập
- **Giao diện web:** <http://localhost>
- **API docs (Swagger):** <http://localhost:8000/docs>
- **Health check:** <http://localhost:8000/health>

> 🔐 **Đăng nhập:** ứng dụng yêu cầu đăng nhập. Tài khoản mặc định: **`admin` / `admin123`**.
> Đổi trong [docker-compose.yml](docker-compose.yml) (`AUTH_USERNAME`, `AUTH_PASSWORD`) hoặc `backend/.env`. Token có hạn 24 giờ; hết hạn sẽ tự quay về màn hình đăng nhập.

### A6. Dừng / xoá
```bash
docker compose down           # dừng, giữ dữ liệu
docker compose down -v        # dừng + xoá toàn bộ volume (mất dữ liệu)
```

---

## Cách B — Chạy thủ công (phát triển)

### B1. Hạ tầng: MySQL + Ollama

**MySQL** (qua Docker cho nhanh — tự chạy `scripts/init_db.sql`):
```bash
docker compose up -d mysql
```

**Ollama** (cài bản native từ ollama.com, rồi):
```bash
ollama pull qwen2.5:1.5b
ollama serve        # nếu chưa tự chạy nền (mặc định cổng 11434)
```

### B2. Backend (FastAPI)
```bash
cd backend

# Tạo môi trường ảo
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS / Linux:
# source .venv/bin/activate

# Cài thư viện
pip install -r requirements.txt

# Cấu hình
copy .env.example .env        # Windows;  *nix: cp .env.example .env
# Mở .env, kiểm tra MYSQL_HOST=localhost, LLM_BASE_URL=http://localhost:11434

# Chạy server
uvicorn main:app --reload --port 8000
```
Backend chạy tại <http://localhost:8000> (Swagger: `/docs`).

### B3. Nạp dữ liệu + Vector DB
Mở terminal mới, tại thư mục gốc dự án:
```bash
# Seed dữ liệu mẫu vào MySQL
python scripts/seed_data.py --reset

# Dựng vector DB và truy hồi thử
python scripts/build_vector_db.py --test "doanh thu theo chi nhánh"
```

### B4. Frontend (React)
```bash
cd frontend
npm install
copy .env.example .env        # Windows;  *nix: cp .env.example .env
# .env: VITE_API_BASE_URL=http://localhost:8000
npm run dev
```
Giao diện chạy tại <http://localhost:5173>.

---

## Kiểm tra hệ thống hoạt động

### 1. Trạng thái 3 thành phần
```bash
curl http://localhost:8000/system-status
```
Mong đợi: `mysql.healthy=true`, `vector_db.healthy=true`, `llm.healthy=true`.

### 2. Thử hội thoại chính
```bash
curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" \
     -d "{\"question\":\"Doanh thu theo chi nhánh năm 2024?\"}"
```

### 3. Thử trên giao diện web
Mở web → **Tab 1 (Chat Assistant)** → bấm một câu hỏi gợi ý → xem câu trả lời + SQL + biểu đồ + insight.

---

## Chạy kiểm thử (unit test)

```bash
cd backend
pip install -r requirements-dev.txt
python -m pytest
```
Mong đợi: **39 passed** (guardrail an toàn SQL, các agent, API).

---

## Các lệnh quản trị hữu ích

| Mục đích | Lệnh / Endpoint |
|----------|-----------------|
| Kiểm tra kết nối MySQL | `GET http://localhost:8000/database-test` |
| Kiểm tra LLM | `GET http://localhost:8000/llm-status` |
| Sinh thử văn bản LLM | `POST http://localhost:8000/llm-test` body `{"prompt":"Chào"}` |
| Nạp lại metadata | `POST http://localhost:8000/reload-metadata` |
| Dựng lại vector DB | `POST http://localhost:8000/rebuild-vector-db` |
| Chỉ sinh SQL (không chạy) | `POST http://localhost:8000/generate-sql` body `{"question":"..."}` |
| Xem log backend (Docker) | `docker compose logs -f backend` |

---

## Xử lý sự cố thường gặp

| Triệu chứng | Nguyên nhân & cách khắc phục |
|-------------|------------------------------|
| `system-status` báo **mysql.healthy=false** | MySQL chưa chạy / sai mật khẩu. Kiểm tra `docker compose ps`, đối chiếu `MYSQL_*` trong `.env`. |
| **llm.healthy=false** | Ollama chưa chạy hoặc chưa `pull` model. Chạy `ollama serve` + `ollama pull qwen2.5:1.5b`. |
| **vector_db** trống (0 tài liệu) | Chưa dựng RAG. Gọi `POST /rebuild-vector-db`. |
| `/chat` trả lỗi LLM (502) | Model chưa tải xong hoặc thiếu RAM. Đợi pull xong; giảm sang `qwen2.5:0.5b` nếu máy yếu, hoặc dùng API key. |
| SQL sinh ra chất lượng thấp | Model 1.5B còn nhỏ. Nâng lên `qwen2.5:3b` / `qwen2.5-coder:1.5b`, hoặc dùng API key (xem [Đổi model LLM](#đổi-model-llm)). |
| Câu hỏi bị **"chặn bởi guardrail"** | Đúng theo thiết kế — hệ thống chỉ cho phép truy vấn `SELECT`. |
| Frontend gọi API lỗi CORS (chạy thủ công) | Kiểm tra `VITE_API_BASE_URL` trong `frontend/.env` trỏ đúng backend; backend đã bật CORS cho `localhost:5173`. |
| Lần đầu `/chat` rất chậm | Đang tải embedding model + nạp LLM vào RAM. Lần sau sẽ nhanh. |

---

## Đổi model LLM

Hệ thống có **LLM Abstraction Layer** nên đổi model/nhà cung cấp **chỉ cần sửa `.env`**, không sửa code. Sau khi sửa, **restart backend** (`docker compose restart backend` hoặc khởi động lại uvicorn).

### A) Dùng model local khác (Ollama)
Nhớ `pull` model trước rồi đặt `LLM_MODEL`:
```bash
ollama pull qwen2.5-coder:1.5b
```
```env
LLM_PROVIDER=ollama
LLM_BASE_URL=http://localhost:11434     # trong Docker: http://ollama:11434
LLM_MODEL=qwen2.5:1.5b                  # nhẹ, đa năng (mặc định)
# LLM_MODEL=qwen2.5-coder:1.5b          # chuyên SQL/code
# LLM_MODEL=qwen2.5:3b                  # chất lượng tốt hơn, vẫn nhẹ
# LLM_MODEL=gemma2:2b
```

| Model | Tag | RAM | Ghi chú |
|-------|-----|-----|---------|
| Qwen2.5 1.5B | `qwen2.5:1.5b` | ~1.5GB | Mặc định, cân bằng |
| Qwen2.5-Coder 1.5B | `qwen2.5-coder:1.5b` | ~1.5GB | Sinh SQL tốt hơn |
| Qwen2.5 3B | `qwen2.5:3b` | ~3GB | Chất lượng cao hơn |
| Qwen2.5 0.5B | `qwen2.5:0.5b` | ~0.8GB | Siêu nhẹ, chất lượng giảm |

### B) Dùng API key (chuẩn OpenAI — `openai_compat`)

Hệ thống dùng provider `openai_compat` để gọi **bất kỳ nhà cung cấp nào theo chuẩn OpenAI** bằng API key. Khi dùng API key thì **không cần Ollama** — chỉ cần bỏ qua bước pull model (A3); cứ để service `ollama` chạy idle. Nếu muốn xoá hẳn service `ollama` trong [docker-compose.yml](docker-compose.yml), nhớ xoá luôn dòng `ollama:` trong `depends_on` của `backend` để compose không báo lỗi.

Cần đặt **4 biến**:

| Biến | Ý nghĩa |
|------|---------|
| `LLM_PROVIDER` | Phải là `openai_compat` |
| `LLM_API_KEY` | API key của bạn |
| `LLM_BASE_URL` | URL endpoint của nhà cung cấp (kết thúc bằng `/v1` hoặc tương đương) |
| `LLM_MODEL` | Tên model của nhà cung cấp đó |

**Bảng cấu hình theo nhà cung cấp** (lấy key tại trang tương ứng):

| Nhà cung cấp | Lấy key tại | `LLM_BASE_URL` | `LLM_MODEL` ví dụ |
|---|---|---|---|
| Groq (free tier) | console.groq.com/keys | `https://api.groq.com/openai/v1` | `llama-3.1-8b-instant` |
| OpenRouter | openrouter.ai/keys | `https://openrouter.ai/api/v1` | `qwen/qwen-2.5-7b-instruct` |
| DeepSeek | platform.deepseek.com | `https://api.deepseek.com/v1` | `deepseek-chat` |
| Together AI | api.together.ai/settings/api-keys | `https://api.together.xyz/v1` | `Qwen/Qwen2.5-7B-Instruct-Turbo` |
| Google Gemini | aistudio.google.com/apikey | `https://generativelanguage.googleapis.com/v1beta/openai` | `gemini-2.0-flash` |
| OpenAI | platform.openai.com/api-keys | `https://api.openai.com/v1` | `gpt-4o-mini` |

#### B1. Khi chạy THỦ CÔNG (Cách B) — sửa `backend/.env`
Mở file `backend/.env`, sửa khối LLM thành (ví dụ Groq):
```env
LLM_PROVIDER=openai_compat
LLM_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=llama-3.1-8b-instant
```
Rồi khởi động lại backend:
```bash
# Ctrl+C để dừng uvicorn cũ, rồi chạy lại:
uvicorn main:app --reload --port 8000
```

#### B2. Khi chạy bằng DOCKER (Cách A) — sửa `docker-compose.yml`
Trong service `backend` → mục `environment`, sửa 4 biến:
```yaml
    environment:
      # ... các biến MYSQL_* giữ nguyên ...
      LLM_PROVIDER: openai_compat
      LLM_API_KEY: "gsk_xxxxxxxxxxxxxxxxxxxx"
      LLM_BASE_URL: https://api.groq.com/openai/v1
      LLM_MODEL: llama-3.1-8b-instant
```
Rồi áp dụng lại:
```bash
docker compose up -d backend          # nạp lại cấu hình cho backend
```
> Mẹo bảo mật: thay vì ghi key trực tiếp vào file, có thể đặt biến môi trường ngoài rồi tham chiếu `LLM_API_KEY: ${LLM_API_KEY}` trong compose, và export key ở shell trước khi `docker compose up`.

#### B3. Kiểm tra đã chạy đúng
```bash
# 1) Trạng thái LLM (mong đợi healthy=true)
curl http://localhost:8000/llm-status

# 2) Sinh thử văn bản
curl -X POST http://localhost:8000/llm-test -H "Content-Type: application/json" \
     -d "{\"prompt\":\"Xin chào, bạn là model gì?\"}"
```
Nếu `llm-status` báo lỗi 401/403 → sai API key; báo 404 model → sai `LLM_MODEL`; báo timeout → sai `LLM_BASE_URL`.

---

## Ví dụ đầy đủ: Dùng Google Gemini qua Docker

Dự án đã được cấu hình **sẵn cho Gemini** trong [docker-compose.yml](docker-compose.yml). Bạn chỉ cần làm 3 bước:

### Bước 1 — Lấy API key
Vào <https://aistudio.google.com/apikey> → **Create API key** → copy (dạng `AIza...`). Gemini có hạn mức miễn phí, đủ cho demo đồ án.

### Bước 2 — Đặt key vào file `.env` ở thư mục gốc
Tại thư mục gốc dự án (`do_an/`, nơi có `docker-compose.yml`):
```bash
copy .env.example .env        # Windows;  *nix: cp .env.example .env
```
Mở `.env` và điền key:
```env
GEMINI_API_KEY=AIzaxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```
> File `.env` đã được `.gitignore` bỏ qua nên key không bị commit. Docker Compose tự đọc file này và truyền vào biến `LLM_API_KEY` của backend.

Cấu hình Gemini đã đặt sẵn trong `docker-compose.yml` (không cần sửa):
```yaml
LLM_PROVIDER: openai_compat
LLM_API_KEY: ${GEMINI_API_KEY:-}
LLM_BASE_URL: https://generativelanguage.googleapis.com/v1beta/openai
LLM_MODEL: gemini-2.0-flash
```
> Đổi model khác: `gemini-2.0-flash-lite` (nhẹ/nhanh), `gemini-1.5-flash`, hoặc `gemini-2.5-flash`.

### Bước 3 — Khởi chạy
```bash
docker compose up -d --build

# Nạp dữ liệu + dựng vector DB (KHÔNG cần pull model Ollama vì đã dùng Gemini)
docker compose exec backend python /scripts/seed_data.py --reset
curl -X POST http://localhost:8000/rebuild-vector-db

# Kiểm tra LLM đã kết nối Gemini
curl http://localhost:8000/llm-status
```
Mong đợi `llm-status` trả `healthy: true`. Xong — mở <http://localhost> để dùng.

> Lưu ý: dùng Gemini thì service `ollama` trong compose chỉ chạy idle (không tốn model). Nếu muốn gọn, có thể xoá service `ollama` **và** dòng `ollama` trong `depends_on` của `backend`. Máy cần truy cập Internet để gọi Gemini.

> ⚠️ **Quan trọng:** Docker Compose chỉ đọc file **`.env`** (không phải `.env.example`). Key phải nằm trong `.env` ở thư mục gốc. Kiểm tra Docker đã nhận key chưa:
> ```bash
> docker compose config | findstr LLM_API_KEY    # Windows; *nix: grep
> ```
> Nếu thấy `LLM_API_KEY: ""` (rỗng) → chưa có `.env` hoặc key chưa điền.

### Test kết nối tới API key

**Cách 1 — Test trực tiếp tới Gemini (không cần chạy app):** xác nhận bản thân API key hợp lệ.

PowerShell (Windows):
```powershell
$key = (Get-Content .env | Select-String '^GEMINI_API_KEY=').Line.Split('=',2)[1].Trim().Trim('"')
Invoke-RestMethod -Method Post `
  -Uri "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions" `
  -Headers @{ Authorization = "Bearer $key" } -ContentType "application/json" `
  -Body '{"model":"gemini-2.5-flash","messages":[{"role":"user","content":"ping"}]}'
```
bash / curl (macOS/Linux/Git Bash):
```bash
source .env
curl https://generativelanguage.googleapis.com/v1beta/openai/chat/completions \
  -H "Authorization: Bearer $GEMINI_API_KEY" -H "Content-Type: application/json" \
  -d '{"model":"gemini-2.5-flash","messages":[{"role":"user","content":"ping"}]}'
```
- ✅ Trả về JSON có `choices[0].message.content` → **key hoạt động**.
- ❌ HTTP 401/403 → key sai/hết hạn; 404 → sai tên model.
- ⚠️ HTTP **429 `RESOURCE_EXHAUSTED`** → **key vẫn đúng**, nhưng đã hết hạn mức free tier (vd `gemini-2.5-flash` chỉ ~20 request/ngày). Cách xử lý:
  - Đổi sang model free tier hạn mức cao hơn: **`gemini-2.5-flash-lite`** (khuyến nghị), hoặc thử `gemini-2.0-flash`. Sửa `LLM_MODEL` trong [docker-compose.yml](docker-compose.yml) rồi `docker compose up -d backend`.
  - Hoặc đợi quota reset (theo ngày, giờ Thái Bình Dương) / bật billing để lên hạn mức cao hơn.
  - Quota tính **riêng theo từng model**, nên đổi model là cách khắc phục nhanh nhất. Xem hạn mức: <https://ai.google.dev/gemini-api/docs/rate-limits>.

**Cách 2 — Test qua app (sau khi `docker compose up`):** xác nhận cả hệ thống dùng được key.
```bash
# Trạng thái LLM (mong đợi "healthy": true)
curl http://localhost:8000/llm-status

# Sinh thử văn bản qua đúng provider/model đã cấu hình
curl -X POST http://localhost:8000/llm-test -H "Content-Type: application/json" \
     -d "{\"prompt\":\"Xin chào, bạn là model gì?\"}"
```
Nếu Cách 1 OK mà Cách 2 lỗi → kiểm tra lại biến trong `docker compose config` và đã `docker compose up -d backend` để nạp lại cấu hình chưa.

---

## Tóm tắt cổng dịch vụ

| Dịch vụ | Cổng (Docker) | Cổng (thủ công) |
|---------|---------------|-----------------|
| Frontend | 80 (`http://localhost`) | 5173 |
| Backend API | 8000 | 8000 |
| MySQL | 3306 | 3306 |
| Ollama | 11434 | 11434 |
