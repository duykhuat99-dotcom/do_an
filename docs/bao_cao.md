# ĐỒ ÁN TỐT NGHIỆP

## Đề tài: Ứng dụng RAG (Retrieval Augmented Generation) và Large Language Model trong xây dựng Chatbot AI phân tích dữ liệu từ DataMart

| Mục | Thông tin |
|-----|-----------|
| Sinh viên thực hiện | *(điền tên)* |
| Mã sinh viên | *(điền MSSV)* |
| Lớp / Khóa | *(điền)* |
| Giảng viên hướng dẫn | *(điền)* |
| Cơ sở đào tạo | *(điền)* |
| Năm thực hiện | 2026 |

> *Ghi chú: Tài liệu được soạn ở định dạng Markdown để tiện chỉnh sửa; khi nộp cần định dạng lại theo mẫu Word của Khoa/Trường (font, lề, đánh số chương–mục, mục lục tự động, danh mục hình–bảng).*

---

# MỞ ĐẦU

## 1. Lý do chọn đề tài

Trong bối cảnh chuyển đổi số, các doanh nghiệp tích lũy khối lượng dữ liệu ngày càng lớn và tổ chức chúng trong các **Kho dữ liệu (Data Warehouse)** hoặc **Kho dữ liệu chủ đề (DataMart)**. Tuy nhiên, để khai thác được giá trị từ dữ liệu, người dùng nghiệp vụ thường phải phụ thuộc vào đội ngũ phân tích biết viết câu lệnh truy vấn **SQL** — một rào cản kỹ thuật khiến việc ra quyết định bị chậm trễ.

Sự phát triển mạnh mẽ của **Mô hình ngôn ngữ lớn (Large Language Model – LLM)** đã mở ra khả năng cho phép người dùng "hỏi dữ liệu" bằng **ngôn ngữ tự nhiên**. Tuy vậy, nếu sử dụng LLM một cách trực tiếp, hệ thống gặp ba vấn đề nghiêm trọng:

1. **Ảo giác (hallucination):** LLM có thể bịa ra tên bảng, tên cột không tồn tại, dẫn đến câu truy vấn sai.
2. **Không biết dữ liệu riêng:** LLM được huấn luyện trên dữ liệu công khai, không nắm được cấu trúc cơ sở dữ liệu nội bộ của doanh nghiệp.
3. **Rủi ro an toàn:** một câu lệnh do mô hình sinh ra có thể vô tình hoặc cố ý phá hoại dữ liệu (xóa, sửa).

Kỹ thuật **RAG (Retrieval Augmented Generation)** giải quyết hai vấn đề đầu bằng cách *truy hồi* tri thức liên quan (ở đây là **siêu dữ liệu – metadata** mô tả cấu trúc kho dữ liệu) rồi cung cấp cho LLM làm ngữ cảnh trước khi sinh câu trả lời. Vấn đề an toàn được xử lý bằng cơ chế **Guardrail** kết hợp tài khoản chỉ-đọc.

Xuất phát từ nhu cầu thực tế đó, đề tài xây dựng một **Chatbot AI phân tích dữ liệu** cho phép người dùng đặt câu hỏi bằng tiếng Việt, hệ thống tự động sinh câu lệnh SQL an toàn, thực thi trên DataMart và trả về **câu trả lời, biểu đồ trực quan cùng nhận định phân tích**.

## 2. Mục tiêu đề tài

**Mục tiêu tổng quát:** Nghiên cứu và xây dựng hệ thống Chatbot phân tích dữ liệu ứng dụng RAG + LLM theo kiến trúc đa tác vụ (Multi-Agent), đạt chuẩn triển khai thực tế (Production).

**Mục tiêu cụ thể:**

- Nghiên cứu cơ sở lý thuyết về LLM, RAG, embedding, vector database và bài toán Text-to-SQL.
- Thiết kế kiến trúc hệ thống nhiều tầng: Frontend – Backend – Orchestrator – RAG Engine – DataMart.
- Hiện thực **sáu tác tử (agents)**: Metadata, SQL, Validation (Guardrail), Insight, Visualization, History.
- Bảo đảm **an toàn dữ liệu**: chỉ cho phép truy vấn đọc (SELECT), chặn mọi thao tác ghi/phá hoại.
- Xây dựng giao diện web trực quan và đóng gói hệ thống bằng Docker.
- Đánh giá định lượng độ chính xác sinh SQL và hiệu năng hệ thống.

## 3. Đối tượng và phạm vi nghiên cứu

**Đối tượng nghiên cứu:**

- Mô hình ngôn ngữ lớn và kỹ thuật RAG.
- Mô hình kho dữ liệu Star Schema (Dimension – Fact).
- Bài toán chuyển ngôn ngữ tự nhiên sang SQL (Text-to-SQL) và các cơ chế bảo đảm an toàn.

**Phạm vi nghiên cứu:**

- Dữ liệu thử nghiệm: tập dữ liệu **đặt tour du lịch Việt Nam** (~4.400 lượt đặt), tổ chức theo Star Schema gồm một bảng Fact (`FactBooking`) và bốn bảng Dimension (`DimDate`, `DimDestination`, `DimCustomerSegment`, `DimTour`).
- Hệ quản trị CSDL: **MySQL 8**.
- LLM: các mô hình mã nguồn mở/Thương mại theo chuẩn OpenAI-compatible (Groq Llama 3, Google Gemini) và mô hình cục bộ qua Ollama (Qwen 2.5), có cơ chế dự phòng (fallback) khi hết hạn mức.
- Phạm vi truy vấn: các câu hỏi phân tích tổng hợp (doanh thu, lượng khách, số booking, điểm hài lòng) theo các chiều thời gian, điểm đến, nhóm khách, loại tour.

## 4. Phương pháp nghiên cứu

- **Phương pháp nghiên cứu lý thuyết:** tổng hợp tài liệu về LLM, RAG, embedding, vector search, mô hình hóa kho dữ liệu.
- **Phương pháp phân tích – thiết kế:** phân rã bài toán thành các tác tử độc lập theo kiến trúc Multi-Agent; thiết kế luồng dữ liệu và cơ sở dữ liệu.
- **Phương pháp thực nghiệm:** hiện thực hệ thống, xây dựng bộ câu hỏi kiểm thử, đo lường định lượng (độ chính xác thực thi, độ chính xác chọn bảng, độ trễ) và kiểm thử đơn vị (unit test).

## 5. Bố cục đồ án

Đồ án gồm phần Mở đầu, bốn chương nội dung và phần Kết luận:

- **Chương 1 – Cơ sở lý thuyết:** trình bày nền tảng về LLM, RAG, embedding, vector database, Text-to-SQL, mô hình Star Schema và kiến trúc Multi-Agent.
- **Chương 2 – Phân tích và thiết kế hệ thống:** khảo sát yêu cầu, thiết kế kiến trúc tổng thể, sáu tác tử, cơ sở dữ liệu và các luồng xử lý.
- **Chương 3 – Triển khai hệ thống:** trình bày công nghệ sử dụng và quá trình hiện thực từng thành phần, giao diện người dùng.
- **Chương 4 – Thực nghiệm và đánh giá:** mô tả môi trường, kịch bản kiểm thử và phân tích kết quả định lượng.
- **Kết luận và hướng phát triển.**

---

# CHƯƠNG 1: CƠ SỞ LÝ THUYẾT

Chương này trình bày các nền tảng lý thuyết và công nghệ được sử dụng trong đồ án, làm cơ sở cho việc phân tích – thiết kế ở Chương 2 và hiện thực ở Chương 3.

## 1.1. Mô hình ngôn ngữ lớn (Large Language Model – LLM)

### 1.1.1. Khái niệm

Mô hình ngôn ngữ lớn là các mạng nơ-ron sâu, chủ yếu dựa trên kiến trúc **Transformer**, được huấn luyện trên khối lượng văn bản khổng lồ để học khả năng dự đoán từ/token tiếp theo trong một chuỗi. Nhờ quy mô tham số lớn (từ vài tỷ đến hàng trăm tỷ), LLM thể hiện khả năng hiểu và sinh ngôn ngữ tự nhiên, suy luận, lập trình và làm theo chỉ dẫn (instruction following). Một số dòng mô hình tiêu biểu: GPT, Llama, Gemini, Mistral, Qwen, Gemma.

### 1.1.2. Cơ chế hoạt động cơ bản

LLM nhận đầu vào là một **prompt** (chuỗi văn bản) và sinh đầu ra theo cơ chế tự hồi quy (auto-regressive): dự đoán token tiếp theo dựa trên toàn bộ ngữ cảnh phía trước. Hai khái niệm quan trọng khi ứng dụng:

- **Prompt (lời nhắc):** cách diễn đạt yêu cầu đưa vào mô hình. Việc thiết kế prompt (prompt engineering) ảnh hưởng lớn đến chất lượng đầu ra. Trong đồ án, mỗi tác tử có một *system prompt* và *few-shot example* riêng.
- **Tham số sinh:** `temperature` (độ ngẫu nhiên), `max_tokens` (độ dài tối đa)… Với bài toán sinh SQL cần tính xác định cao, đồ án đặt `temperature` thấp.

### 1.1.3. Hạn chế của LLM khi áp dụng trực tiếp

- **Ảo giác (hallucination):** mô hình có thể sinh ra thông tin sai sự thật một cách "tự tin", ví dụ bịa tên bảng/cột.
- **Giới hạn tri thức:** mô hình chỉ biết những gì có trong dữ liệu huấn luyện, không nắm được cấu trúc cơ sở dữ liệu riêng của doanh nghiệp.
- **Mốc thời gian tri thức (knowledge cutoff):** không cập nhật dữ liệu/thông tin mới.

Những hạn chế này là động cơ trực tiếp cho việc áp dụng **RAG** và **Guardrail** trong đồ án.

## 1.2. Kỹ thuật RAG (Retrieval Augmented Generation)

### 1.2.1. Khái niệm và động cơ

RAG là kỹ thuật **tăng cường khả năng sinh của LLM bằng cách bổ sung tri thức truy hồi từ nguồn ngoài** vào ngữ cảnh prompt. Thay vì để mô hình "tự nhớ", hệ thống chủ động tìm các đoạn tri thức liên quan tới câu hỏi và đưa cho mô hình tham khảo. RAG giúp:

- Khắc phục ảo giác và giới hạn tri thức (mô hình trả lời dựa trên tài liệu được cung cấp).
- Cập nhật tri thức linh hoạt mà không cần huấn luyện lại mô hình.
- Tiết kiệm chi phí so với tinh chỉnh (fine-tuning).

### 1.2.2. Kiến trúc RAG tổng quát

Một hệ RAG điển hình gồm hai pha:

**a) Pha lập chỉ mục (Indexing – thực hiện trước, offline):**
1. Thu thập tài liệu nguồn.
2. Chia nhỏ thành các đoạn (chunking).
3. Mã hóa mỗi đoạn thành **vector embedding** bằng mô hình embedding.
4. Lưu vector cùng metadata vào **Vector Database**.

**b) Pha truy hồi & sinh (Retrieval & Generation – khi có câu hỏi):**
1. Mã hóa câu hỏi thành vector.
2. Tìm **Top-K** đoạn có độ tương đồng cao nhất trong Vector Database (similarity search).
3. Ghép các đoạn truy hồi được vào prompt làm ngữ cảnh.
4. LLM sinh câu trả lời dựa trên ngữ cảnh đó.

### 1.2.3. Đặc thù áp dụng RAG trong đồ án

Điểm khác biệt quan trọng: đồ án **không embedding dữ liệu nghiệp vụ (các dòng Fact)** mà **chỉ embedding siêu dữ liệu (metadata) và tri thức nghiệp vụ** — tên bảng, mô tả bảng, tên cột, mô tả cột, định nghĩa KPI và các quy tắc nghiệp vụ. Lý do:

- Dữ liệu Fact có thể rất lớn và thay đổi liên tục; embedding chúng vừa tốn kém vừa không cần thiết.
- Cái LLM cần để sinh SQL là **hiểu cấu trúc dữ liệu**, không phải bản thân dữ liệu.
- Khi truy vấn, câu SQL được sinh ra sẽ chạy *trực tiếp (live)* trên CSDL, nên dữ liệu mới luôn được phản ánh chính xác mà không cần lập chỉ mục lại.

Đây là cách tiếp cận **RAG cho schema-linking** trong bài toán Text-to-SQL: truy hồi đúng phần cấu trúc liên quan tới câu hỏi để định hướng cho LLM.

## 1.3. Embedding và Vector Database

### 1.3.1. Vector embedding

**Embedding** là quá trình ánh xạ một đoạn văn bản thành một vector số thực trong không gian nhiều chiều, sao cho các đoạn có ngữ nghĩa gần nhau thì vector của chúng gần nhau. Đồ án sử dụng mô hình **`sentence-transformers/all-MiniLM-L6-v2`** — một mô hình bi-encoder nhẹ, sinh vector **384 chiều**, chạy được cục bộ, phù hợp triển khai không phụ thuộc dịch vụ ngoài.

### 1.3.2. Đo độ tương đồng (Similarity Search)

Độ liên quan giữa câu hỏi và tài liệu được đo bằng **độ tương đồng cosine** giữa hai vector: giá trị càng lớn (góc càng nhỏ) thì càng tương đồng. Thao tác **Top-K Retrieval** trả về K tài liệu có độ tương đồng cao nhất.

### 1.3.3. Cơ sở dữ liệu vector (Vector Database) – ChromaDB

**Vector Database** là CSDL chuyên lưu trữ và tìm kiếm vector hiệu quả. Đồ án dùng **ChromaDB** vì: mã nguồn mở, nhẹ, hỗ trợ lưu bền (persistent), tìm kiếm tương đồng và **lọc theo metadata** (ví dụ chỉ lấy tài liệu loại "bảng" hay "cột"). ChromaDB đóng vai trò "thủ thư": khi người dùng hỏi, nó nhanh chóng tìm đúng các mô tả schema liên quan để cung cấp cho LLM, thay vì đưa toàn bộ cấu trúc CSDL vào mỗi lần.

## 1.4. Bài toán Text-to-SQL

### 1.4.1. Khái niệm

**Text-to-SQL** là bài toán tự động chuyển một câu hỏi bằng ngôn ngữ tự nhiên thành câu lệnh SQL tương ứng, thực thi được trên cơ sở dữ liệu. Ví dụ: *"Doanh thu theo điểm đến?"* → `SELECT d.DestinationName, SUM(f.Revenue) ... GROUP BY d.DestinationName`.

### 1.4.2. Các thách thức chính

- **Schema linking:** mô hình phải xác định đúng bảng và cột cần dùng, đúng cách JOIN giữa Fact và Dimension. RAG hỗ trợ giải quyết bằng cách cung cấp đúng ngữ cảnh schema.
- **Tính đúng cú pháp và ngữ nghĩa:** câu SQL phải đúng cú pháp MySQL và đúng ý nghĩa nghiệp vụ (ví dụ "doanh thu" = `SUM(Revenue)`).
- **An toàn:** tuyệt đối không cho phép sinh các câu lệnh phá hoại dữ liệu.
- **Câu hỏi nối tiếp (multi-turn):** hiểu các câu rút gọn dựa vào ngữ cảnh hội thoại trước đó.

## 1.5. Kho dữ liệu và mô hình Star Schema

### 1.5.1. DataMart

**DataMart** là một phân hệ chủ đề của Kho dữ liệu, phục vụ một lĩnh vực nghiệp vụ cụ thể (ở đây là *đặt tour du lịch*). Dữ liệu trong DataMart được tổ chức để tối ưu cho phân tích, thay vì cho giao dịch.

### 1.5.2. Mô hình Star Schema (Dimension – Fact)

**Star Schema** là mô hình thiết kế kho dữ liệu phổ biến, gồm:

- **Bảng Fact (sự kiện):** lưu các phép đo (measures) có thể tổng hợp được, ví dụ `FactBooking` với các cột `Revenue`, `Pax`, `BookingCount`, `SatisfactionScore`. Mỗi dòng Fact trỏ tới các bảng Dimension qua khóa ngoại.
- **Bảng Dimension (chiều):** lưu các thuộc tính mô tả để phân tích theo nhiều góc nhìn, ví dụ `DimDate` (thời gian), `DimDestination` (điểm đến), `DimCustomerSegment` (nhóm khách), `DimTour` (loại tour).

Mô hình hình sao này giúp câu truy vấn phân tích trở nên đơn giản (JOIN Fact với các Dimension), dễ mở rộng và rất phù hợp cho các hệ thống BI cũng như bài toán Text-to-SQL.

## 1.6. Kiến trúc đa tác vụ (Multi-Agent)

**Kiến trúc Multi-Agent** chia một bài toán phức tạp thành nhiều **tác tử (agent)** chuyên trách, mỗi tác tử đảm nhiệm một nhiệm vụ hẹp và phối hợp với nhau qua một bộ **điều phối (Orchestrator)**. Ưu điểm: tách bạch trách nhiệm, dễ kiểm thử, dễ thay thế từng thành phần và minh bạch luồng xử lý. Đồ án thiết kế **sáu tác tử**: Metadata Agent, SQL Agent, Validation Agent, Insight Agent, Visualization Agent và History Agent (chi tiết ở Chương 2).

## 1.7. Cơ chế an toàn truy vấn (Guardrail)

Vì câu SQL do LLM sinh ra có thể tiềm ẩn rủi ro, đồ án áp dụng **cơ chế phòng thủ nhiều lớp (defense-in-depth)**:

1. **Tầng nhắc nhở (prompt):** chỉ dẫn LLM chỉ sinh câu `SELECT`.
2. **Tầng kiểm duyệt bằng Regex:** quét chuỗi SQL, chặn tuyệt đối các từ khóa nguy hiểm (`DROP`, `DELETE`, `UPDATE`, `INSERT`, `ALTER`, `TRUNCATE`…), chặn nhiều câu lệnh nối nhau và cú pháp khả nghi.
3. **Tầng kiểm duyệt bằng LLM:** mô hình soát lại ý đồ câu lệnh.
4. **Tầng cơ sở dữ liệu:** thực thi bằng **tài khoản chỉ-đọc** chỉ có quyền `SELECT`.

Đây là tầng quan trọng nhất bảo đảm tính an toàn của hệ thống.

## 1.8. Các công nghệ nền tảng

| Tầng | Công nghệ | Vai trò |
|------|-----------|---------|
| Frontend | React, Vite, Material UI, Plotly | Giao diện người dùng, biểu đồ tương tác |
| Backend | FastAPI (Python), Pydantic | API, xác thực dữ liệu, điều phối agent |
| CSDL | MySQL 8, SQLAlchemy | Lưu trữ DataMart và lịch sử |
| RAG | ChromaDB, sentence-transformers | Vector store và embedding |
| LLM | Groq / Gemini / Ollama (chuẩn OpenAI) | Sinh SQL, phân tích, phân loại |
| Hạ tầng | Docker, docker-compose | Đóng gói, triển khai |

## Kết luận chương 1

Chương 1 đã trình bày các nền tảng lý thuyết cốt lõi: mô hình ngôn ngữ lớn và những hạn chế của nó; kỹ thuật RAG như một giải pháp tăng cường tri thức; embedding và vector database; bài toán Text-to-SQL cùng các thách thức; mô hình kho dữ liệu Star Schema; kiến trúc Multi-Agent và cơ chế Guardrail bảo đảm an toàn. Đây là cơ sở để Chương 2 tiến hành phân tích yêu cầu và thiết kế kiến trúc hệ thống.

---

# CHƯƠNG 2: PHÂN TÍCH VÀ THIẾT KẾ HỆ THỐNG

Chương này phân tích yêu cầu của hệ thống, thiết kế kiến trúc tổng thể, đặc tả sáu tác tử, các luồng xử lý chính, cơ sở dữ liệu và mô hình ca sử dụng (use-case).

## 2.1. Khảo sát và phân tích yêu cầu

### 2.1.1. Mô tả bài toán

Hệ thống cần cho phép người dùng nghiệp vụ **đặt câu hỏi phân tích bằng tiếng Việt** về dữ liệu đặt tour, và tự động trả về: câu trả lời bằng ngôn ngữ tự nhiên, câu lệnh SQL đã sinh, biểu đồ trực quan và nhận định phân tích — mà người dùng **không cần biết SQL**. Toàn bộ quá trình phải bảo đảm **an toàn dữ liệu** (chỉ đọc) và **lưu vết lịch sử** để duy trì ngữ cảnh hội thoại.

### 2.1.2. Yêu cầu chức năng

| Mã | Yêu cầu chức năng | Mô tả |
|----|-------------------|-------|
| FR1 | Hội thoại ngôn ngữ tự nhiên | Người dùng đặt câu hỏi; hệ thống trả lời kèm SQL, biểu đồ, insight, thời gian thực thi |
| FR2 | Phân loại câu hỏi | Phân biệt câu hỏi *dữ liệu* (cần truy vấn) và câu hỏi *thường* (trò chuyện) |
| FR3 | Truy hồi ngữ cảnh schema (RAG) | Tìm bảng/cột/KPI/quy tắc liên quan tới câu hỏi |
| FR4 | Sinh câu lệnh SQL | Tạo câu `SELECT` từ câu hỏi và ngữ cảnh schema |
| FR5 | Kiểm duyệt an toàn (Guardrail) | Chặn mọi câu lệnh ghi/phá hoại; chỉ cho phép `SELECT` |
| FR6 | Thực thi truy vấn | Chạy SQL trên DataMart bằng tài khoản chỉ-đọc, trả về dữ liệu |
| FR7 | Tự sửa lỗi SQL | Khi thực thi lỗi, đưa lỗi lại cho LLM sửa và thử lại |
| FR8 | Phân tích insight | Tính thống kê, tăng trưởng, điểm nổi bật và diễn giải bằng văn bản |
| FR9 | Sinh biểu đồ | Chọn loại biểu đồ phù hợp và đóng gói cấu hình Plotly |
| FR10 | Quản lý lịch sử hội thoại | Lưu, liệt kê, đổi tên, xóa các cuộc trò chuyện; hỗ trợ hỏi nối tiếp (multi-turn) |
| FR11 | Dashboard phân tích | Khung phân tích nhiều câu liên tục kèm biểu đồ, bảng dữ liệu, insight |
| FR12 | Quản trị RAG | Nạp lại metadata, dựng lại vector database |
| FR13 | Giám sát hệ thống | Theo dõi trạng thái real-time của MySQL, Vector DB, LLM; thống kê truy vấn |
| FR14 | Đánh giá câu trả lời | Người dùng đánh giá 👍/👎; hệ thống lưu phục vụ cải tiến |
| FR15 | Xác thực người dùng | Đăng nhập bằng tài khoản, bảo vệ các API nghiệp vụ |

### 2.1.3. Yêu cầu phi chức năng

| Mã | Yêu cầu | Mô tả |
|----|---------|-------|
| NFR1 | **An toàn** | Phòng thủ nhiều lớp: Regex + LLM + tài khoản chỉ-đọc; xác thực JWT |
| NFR2 | **Hiệu năng** | Độ trễ một truy vấn ở mức chấp nhận được (vài giây); health-check nhanh |
| NFR3 | **Khả năng mở rộng** | Đổi mô hình/nhà cung cấp LLM chỉ bằng cấu hình `.env`, không sửa mã |
| NFR4 | **Độ tin cậy** | Chuỗi LLM dự phòng (fallback) khi hết hạn mức; hệ thống không sập khi DB/LLM lỗi |
| NFR5 | **Khả năng bảo trì** | Kiến trúc Multi-Agent tách bạch; có bộ kiểm thử đơn vị |
| NFR6 | **Tính khả chuyển** | Đóng gói bằng Docker, chạy bằng một lệnh `docker compose up` |
| NFR7 | **Khả dụng** | Giao diện trực quan, tiếng Việt, biểu đồ tương tác |

## 2.2. Kiến trúc tổng thể hệ thống

Hệ thống thiết kế theo mô hình **client–server nhiều tầng**, kết hợp **Micro-Agent** và **RAG Layer**.

```
┌─────────────────────────────────────────────────────────────────┐
│  NGƯỜI DÙNG (trình duyệt)                                         │
└───────────────┬─────────────────────────────────────────────────┘
                │ HTTP/JSON (có JWT)
                ▼
┌─────────────────────────────────────────────────────────────────┐
│  FRONTEND — React + Vite + Material UI + Plotly (nginx)           │
│  3 Tab: Chat Assistant | Analytics Dashboard | System Management  │
└───────────────┬─────────────────────────────────────────────────┘
                │ REST API (/chat, /chart, /history, /system-status…)
                ▼
┌─────────────────────────────────────────────────────────────────┐
│  BACKEND — FastAPI                                                │
│   ├─ Tầng API + Xác thực (JWT) + Exception handling              │
│   ├─ AI ORCHESTRATOR (điều phối)                                 │
│   │     0. Router Agent  → phân loại data / general              │
│   │     1. Metadata Agent → RAG Engine (Retriever + ChromaDB)    │
│   │     2. SQL Agent      → sinh câu SELECT                       │
│   │     3. Validation Agent (Guardrail) → Regex + LLM            │
│   │     4. SQL Executor   → MySQL (read-only) → DataFrame         │
│   │     5. Insight Agent  → phân tích                             │
│   │     6. Visualization Agent → Plotly JSON                     │
│   │     7. History Agent  → lưu hội thoại + nhật ký               │
│   └─ LLM Abstraction Layer (chuỗi fallback)                      │
└──────┬───────────────────────┬──────────────────────┬───────────┘
       ▼                       ▼                      ▼
┌────────────┐        ┌─────────────────┐     ┌──────────────────┐
│ ChromaDB   │        │  MySQL DataMart │     │ LLM Providers    │
│ (metadata) │        │  (Star Schema)  │     │ Groq→OpenRouter  │
│            │        │  + History      │     │ →Gemini→Ollama   │
└────────────┘        └─────────────────┘     └──────────────────┘
```

**Mô tả các tầng:**

- **Frontend (React):** giao diện đơn trang (SPA) gồm ba tab, gọi API qua Axios, hiển thị biểu đồ Plotly.
- **Backend (FastAPI):** cung cấp REST API với schema Pydantic, xác thực JWT, xử lý ngoại lệ tập trung; chứa **Orchestrator** điều phối các tác tử.
- **RAG Engine (ChromaDB):** lưu trữ vector của siêu dữ liệu, phục vụ truy hồi ngữ cảnh.
- **MySQL DataMart:** lưu dữ liệu Star Schema (đọc) và các bảng lịch sử (đọc/ghi).
- **LLM Abstraction Layer:** lớp trừu tượng cho phép gọi nhiều nhà cung cấp LLM qua một giao diện chung, có **chuỗi dự phòng**.

## 2.3. Thiết kế các tác tử (Multi-Agent)

Hệ thống điều phối qua một **Router Agent** (phân loại) và **sáu tác tử nghiệp vụ**, được **Orchestrator** kết nối theo trình tự.

### 2.3.0. Router Agent và Orchestrator

- **Router Agent:** phân loại câu hỏi thành `data` (cần truy vấn DataMart) hoặc `general` (trò chuyện thông thường như "hôm nay là ngày nào"). Nhờ đó, câu hỏi thường được trả lời trực tiếp, không bị ép sinh SQL vô nghĩa.
- **Orchestrator:** điều phối toàn bộ luồng `process_chat`, gọi lần lượt các tác tử, tổng hợp kết quả và xử lý các nhánh lỗi.

### 2.3.1. Metadata Agent (Tác tử #1)

- **Nhiệm vụ:** truy hồi ngữ cảnh schema liên quan tới câu hỏi từ ChromaDB.
- **Đầu vào:** câu hỏi người dùng.
- **Đầu ra:** đoạn ngữ cảnh schema (mô tả bảng/cột/KPI/quy tắc) và danh sách bảng liên quan.
- **Cơ chế:** embedding câu hỏi → similarity search Top-K → định dạng thành ngữ cảnh.

### 2.3.2. SQL Agent (Tác tử #2)

- **Nhiệm vụ:** sinh câu lệnh `SELECT` MySQL từ câu hỏi và ngữ cảnh schema.
- **Đầu vào:** câu hỏi, ngữ cảnh schema, (tùy chọn) lịch sử hội thoại.
- **Đầu ra:** câu SQL đã làm sạch (loại bỏ markdown/giải thích).
- **Cơ chế:** prompt gồm *system prompt* (quy tắc) + *few-shot example* (ví dụ mẫu) + ngữ cảnh; có hàm `fix()` để sửa SQL khi thực thi lỗi.

### 2.3.3. Validation Agent – Guardrail (Tác tử #3)

- **Nhiệm vụ:** kiểm duyệt an toàn câu SQL trước khi thực thi.
- **Đầu vào:** câu SQL.
- **Đầu ra:** kết luận an toàn / không an toàn kèm lý do.
- **Cơ chế:** tầng **Regex** (quyết định) chặn từ khóa nguy hiểm, nhiều câu lệnh, comment khả nghi; tầng **LLM** (bổ sung) soát lại; chỉ chấp nhận câu bắt đầu bằng `SELECT`/`WITH`.

### 2.3.4. Insight Agent (Tác tử #4)

- **Nhiệm vụ:** phân tích bảng kết quả (Pandas DataFrame) để rút ra nhận định.
- **Đầu vào:** câu hỏi, DataFrame kết quả.
- **Đầu ra:** đoạn văn nhận định (tăng trưởng, xu hướng, giá trị nổi bật).
- **Cơ chế:** tính thống kê **xác định** bằng Pandas (tổng, trung bình, min/max, tăng trưởng), sau đó LLM diễn giải; có cơ chế dự phòng theo quy tắc khi LLM lỗi.

### 2.3.5. Visualization Agent (Tác tử #5)

- **Nhiệm vụ:** chọn loại biểu đồ phù hợp và đóng gói cấu hình Plotly JSON.
- **Đầu vào:** câu hỏi, DataFrame.
- **Đầu ra:** cấu hình Plotly (loại biểu đồ Bar/Line/Pie/Area/Scatter, trục, tiêu đề, đơn vị).
- **Cơ chế:** LLM gợi ý kết hợp **heuristic** theo hình dạng dữ liệu (chuỗi thời gian → line, so sánh hạng mục → bar, tỷ trọng → pie…).

### 2.3.6. History Agent (Tác tử #6)

- **Nhiệm vụ:** quản lý ghi/đọc lịch sử hội thoại và nhật ký truy vấn.
- **Đầu vào/Đầu ra:** thao tác lưu lượt hội thoại, ghi nhật ký SQL, liệt kê/đổi tên/xóa phiên, đọc lịch sử.
- **Cơ chế:** thao tác trên các bảng `conversation_history`, `query_log`, `chat_session`, `feedback`; mọi thao tác đều "best-effort" (lỗi DB không làm sập luồng trả lời).

## 2.4. Thiết kế luồng xử lý chính

### 2.4.1. Luồng hội thoại (`process_chat`)

```
Người dùng        Orchestrator   Router  Metadata  SQL   Validation  Executor  Insight/Chart  History
   │   câu hỏi         │            │        │       │        │          │           │           │
   ├─────────────────►│            │        │       │        │          │           │           │
   │                  ├──phân loại►│        │       │        │          │           │           │
   │                  │◄──data─────┤        │       │        │          │           │           │
   │                  ├──RAG──────────────►│       │        │          │           │           │
   │                  │◄──ngữ cảnh schema──┤       │        │          │           │           │
   │                  ├──sinh SQL─────────────────►│        │          │           │           │
   │                  │◄──câu SELECT───────────────┤        │          │           │           │
   │                  ├──kiểm duyệt────────────────────────►│          │           │           │
   │                  │◄──an toàn──────────────────────────┤          │           │           │
   │                  ├──thực thi (read-only)─────────────────────────►│           │           │
   │                  │◄──DataFrame───────────────────────────────────┤           │           │
   │                  ├──phân tích + vẽ biểu đồ──────────────────────────────────►│           │
   │                  │◄──insight + Plotly JSON──────────────────────────────────┤           │
   │                  ├──lưu hội thoại + nhật ký──────────────────────────────────────────────►│
   │ ◄────────────────┤ (answer + SQL + chart + insight + thời gian)              │           │
```

Nếu câu hỏi được phân loại là `general`, Orchestrator bỏ qua các bước RAG/SQL và để LLM trả lời trực tiếp.

### 2.4.2. Cơ chế tự sửa lỗi SQL (Self-correction)

Khi câu SQL thực thi gặp lỗi (sai cú pháp/tên cột), Orchestrator đưa **thông báo lỗi từ MySQL** trở lại cho SQL Agent để sinh lại câu lệnh đã sửa, sau đó kiểm duyệt và thực thi lại (tối đa số lần cấu hình được). Câu SQL sửa lại vẫn phải qua Guardrail.

### 2.4.3. Cơ chế dự phòng LLM (Fallback Chain)

Lớp trừu tượng LLM được tổ chức thành **chuỗi nhiều nhà cung cấp**: *Groq → OpenRouter → Gemini → Ollama (cục bộ)*. Khi nhà cung cấp hiện tại hết hạn mức (lỗi HTTP 429) hoặc gặp sự cố, hệ thống **tự động chuyển sang nhà cung cấp kế tiếp**; mô hình cục bộ Ollama đóng vai trò "lưới an toàn" luôn sẵn sàng. Nhà cung cấp nào thiếu khóa API sẽ tự động bị bỏ qua.

## 2.5. Thiết kế cơ sở dữ liệu

### 2.5.1. Mô hình DataMart – Star Schema "Vietnam Tour Bookings"

Gồm một bảng Fact và bốn bảng Dimension:

**FactBooking** (bảng sự kiện – mỗi dòng là một lượt đặt tour):

| Cột | Kiểu | Ý nghĩa |
|-----|------|---------|
| BookingID | BIGINT (PK) | Mã lượt đặt |
| DateKey | INT (FK→DimDate) | Ngày đặt |
| DestinationKey | INT (FK→DimDestination) | Điểm đến |
| SegmentKey | INT (FK→DimCustomerSegment) | Nhóm khách |
| TourKey | INT (FK→DimTour) | Loại tour |
| Revenue | DECIMAL(18,2) | Doanh thu (VNĐ) |
| Pax | INT | Số lượng khách |
| BookingCount | INT | Số booking (=1/dòng) |
| SatisfactionScore | DECIMAL(4,2) | Điểm hài lòng (1–5) |

**Các bảng Dimension:**

- **DimDate** (DateKey, FullDate, DayOfMonth, DayName, WeekOfYear, MonthNumber, MonthName, QuarterNumber, YearNumber, IsWeekend) — chiều thời gian.
- **DimDestination** (DestinationKey, DestinationName, Province, Region, DestinationType) — điểm đến.
- **DimCustomerSegment** (SegmentKey, SegmentName, AgeGroup, CustomerType) — nhóm khách.
- **DimTour** (TourKey, TourName, TourCategory, DurationDays, TransportationType) — loại tour.

```
                ┌──────────┐
                │ DimDate  │
                └────┬─────┘
                     │ DateKey
 ┌─────────────┐     │      ┌────────────────────┐
 │DimDestination├────┤      │ DimCustomerSegment │
 └──────┬──────┘     │      └─────────┬──────────┘
DestinationKey │  ┌──▼───────────┐    │ SegmentKey
        └──────►│  FactBooking   │◄───┘
               │ (Revenue, Pax, │
        ┌──────►│  Booking,      │◄───┐
   TourKey │   │  Satisfaction) │   │
 ┌─────────┴┐  └────────────────┘   │
 │ DimTour  │                       │
 └──────────┘                       │
```

### 2.5.2. Các bảng hệ thống (lịch sử và quản trị)

- **conversation_history:** lưu từng lượt hội thoại (vai trò user/assistant, câu hỏi, câu trả lời, SQL đã sinh, biểu đồ và insight dạng JSON).
- **query_log:** nhật ký mỗi lần sinh/thực thi SQL (câu hỏi, SQL, thành công/thất bại, số dòng, thời gian thực thi, lỗi).
- **chat_session:** tên tùy chỉnh (đặt lại) cho cuộc trò chuyện.
- **feedback:** đánh giá 👍/👎 của người dùng cho câu trả lời.

### 2.5.3. Tài khoản chỉ-đọc

Hệ thống tạo một tài khoản MySQL **`datamart_ro`** chỉ có quyền `SELECT`, dùng riêng cho việc thực thi SQL do LLM sinh ra — đây là **tầng phòng thủ cuối cùng** của cơ chế Guardrail.

## 2.6. Thiết kế ca sử dụng (Use-case)

### 2.6.1. Tác nhân (Actor)

- **Người dùng phân tích (Analyst/User):** đặt câu hỏi, xem biểu đồ, quản lý lịch sử, đánh giá câu trả lời.
- **Quản trị viên (Admin):** thực hiện đăng nhập, quản trị RAG (dựng lại vector DB, nạp lại metadata), giám sát hệ thống. *(Trong phạm vi đồ án, hai vai trò dùng chung một tài khoản cố định.)*

### 2.6.2. Danh sách ca sử dụng chính

```
                ┌───────────────────────────────────────┐
                │            HỆ THỐNG CHATBOT            │
   ┌──────┐     │  (UC1) Đăng nhập                      │
   │      ├─────┤  (UC2) Đặt câu hỏi phân tích (chat)   │
   │ Người│     │  (UC3) Xem biểu đồ + insight          │
   │ dùng ├─────┤  (UC4) Hỏi nối tiếp (multi-turn)      │
   │      │     │  (UC5) Quản lý lịch sử (đổi tên/xóa)  │
   │      ├─────┤  (UC6) Phân tích trên Dashboard       │
   └──────┘     │  (UC7) Đánh giá câu trả lời           │
   ┌──────┐     │  (UC8) Quản trị RAG                   │
   │Admin ├─────┤  (UC9) Giám sát trạng thái hệ thống   │
   └──────┘     │  (UC10) Xuất dữ liệu (CSV) / tải biểu đồ│
                └───────────────────────────────────────┘
```

### 2.6.3. Đặc tả ca sử dụng tiêu biểu — UC2: Đặt câu hỏi phân tích

| Mục | Nội dung |
|-----|----------|
| **Tên** | Đặt câu hỏi phân tích |
| **Tác nhân** | Người dùng |
| **Tiền điều kiện** | Đã đăng nhập; hệ thống và DataMart sẵn sàng |
| **Luồng chính** | 1. Người dùng nhập câu hỏi tiếng Việt và gửi. 2. Hệ thống phân loại câu hỏi. 3. Truy hồi ngữ cảnh schema (RAG). 4. Sinh SQL. 5. Kiểm duyệt an toàn. 6. Thực thi truy vấn (chỉ-đọc). 7. Phân tích insight + sinh biểu đồ. 8. Lưu lịch sử. 9. Hiển thị câu trả lời, SQL, biểu đồ, insight. |
| **Luồng phụ** | 5a. SQL không an toàn → từ chối, thông báo lý do. 6a. Thực thi lỗi → tự sửa SQL và thử lại. 2a. Câu hỏi thường → trả lời trực tiếp, không sinh SQL. |
| **Hậu điều kiện** | Lượt hội thoại được lưu vào lịch sử |

## Kết luận chương 2

Chương 2 đã phân tích yêu cầu (chức năng và phi chức năng), thiết kế kiến trúc tổng thể nhiều tầng theo mô hình Multi-Agent + RAG, đặc tả nhiệm vụ của Router Agent và sáu tác tử nghiệp vụ, mô tả các luồng xử lý chính (hội thoại, tự sửa lỗi, dự phòng LLM), thiết kế cơ sở dữ liệu Star Schema cùng các bảng hệ thống, và mô hình ca sử dụng. Đây là cơ sở để Chương 3 trình bày quá trình hiện thực hệ thống.

---

# CHƯƠNG 3: TRIỂN KHAI HỆ THỐNG

Chương này trình bày công nghệ sử dụng và quá trình hiện thực từng thành phần của hệ thống, kèm các đoạn mã tiêu biểu và giao diện kết quả.

## 3.1. Công nghệ và cấu trúc mã nguồn

### 3.1.1. Công nghệ sử dụng

| Thành phần | Công nghệ / Thư viện | Phiên bản |
|------------|----------------------|-----------|
| Ngôn ngữ backend | Python | 3.12 |
| Web framework | FastAPI, Uvicorn | 0.115 |
| Xác thực dữ liệu | Pydantic, pydantic-settings | 2.x |
| ORM / CSDL | SQLAlchemy, PyMySQL, MySQL | 2.0 / 8.0 |
| Vector DB | ChromaDB | 0.5 |
| Embedding | sentence-transformers (all-MiniLM-L6-v2) | 3.x |
| Xử lý dữ liệu | Pandas | 2.x |
| LLM client | httpx (chuẩn OpenAI) | 0.27 |
| Xác thực phiên | PyJWT | 2.10 |
| Frontend | React, Vite, Material UI, react-plotly.js, Axios | 18 / 6 |
| Đóng gói | Docker, docker-compose | — |

### 3.1.2. Cấu trúc thư mục

```
do_an/
├── backend/
│   ├── app/
│   │   ├── api/         # Routers: chat, query, admin, auth, health
│   │   ├── agents/      # 7 agents: router, metadata, sql, validation, insight, chart, history
│   │   ├── rag/         # embedder, vector_store, loader, retriever
│   │   ├── llm/         # interface, providers, fallback, factory
│   │   ├── services/    # orchestrator, text_to_sql, analysis, sql_executor
│   │   ├── database/    # connection pool, base
│   │   ├── models/      # ORM: dimensions, facts, history
│   │   ├── schemas/     # Pydantic request/response
│   │   ├── prompts/     # prompt cho từng agent
│   │   └── core/, utils/# config, logger, security
│   ├── tests/           # unit test (pytest)
│   └── main.py, Dockerfile, requirements.txt
├── frontend/            # React SPA (3 Tab)
├── metadata/            # *.yaml mô tả schema + KPI + business rules
├── scripts/             # init_db.sql, load_tour_datamart.py, build_vector_db.py, evaluate.py
└── docker-compose.yml
```

## 3.2. Hiện thực tầng dữ liệu

### 3.2.1. Mô hình ORM và kết nối

Các bảng được định nghĩa bằng **SQLAlchemy 2.0** (kiểu khai báo `Mapped`). Kết nối dùng **Connection Pool** kèm `pool_pre_ping` (tự kiểm tra kết nối) và cơ chế **retry** khi khởi động. Hệ thống dùng **hai engine**: một engine đọc/ghi (cho lịch sử) và một engine **chỉ-đọc** (cho việc thực thi SQL của LLM).

```python
class FactBooking(Base):
    __tablename__ = "FactBooking"
    BookingID: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    DateKey: Mapped[int] = mapped_column(ForeignKey("DimDate.DateKey"), index=True)
    DestinationKey: Mapped[int] = mapped_column(ForeignKey("DimDestination.DestinationKey"))
    Revenue: Mapped[float] = mapped_column(Numeric(18, 2))
    Pax: Mapped[int] = mapped_column(Integer)
    SatisfactionScore: Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True)
```

### 3.2.2. Quy trình ETL nạp dữ liệu

Script `load_tour_datamart.py` đọc tệp `raw_data.csv`, **làm sạch dữ liệu** (gộp lỗi chính tả điểm đến như *HaLongg → Hạ Long*, *bech → Beach*; thay giá trị thiếu bằng "Không xác định"), dựng bốn bảng Dimension với khóa thay thế (surrogate key), xây bảng FactBooking và nạp vào MySQL. Kết quả: **4.418 lượt đặt, 1.276 ngày, 11 điểm đến, 5 nhóm khách, 6 loại tour**.

> *[Hình 3.1: Kết quả chạy ETL nạp dữ liệu vào DataMart]*

## 3.3. Hiện thực RAG Engine

### 3.3.1. Tổ chức siêu dữ liệu

Mỗi bảng được mô tả trong một tệp `metadata/*.yaml` (tên bảng, mô tả, danh sách cột và mô tả cột). Ngoài ra có tệp định nghĩa **KPI** và **quy tắc nghiệp vụ**. Ví dụ trích đoạn:

```yaml
table: FactBooking
type: fact
description: Bảng sự kiện đặt tour, mỗi dòng là một lượt đặt...
columns:
  - name: Revenue
    type: DECIMAL
    description: Doanh thu của lượt đặt (VNĐ). Doanh thu = SUM(Revenue).
    measure: true
```

### 3.3.2. Sinh tài liệu, embedding và lưu trữ

Module `loader.py` đọc các tệp YAML và sinh **tài liệu đa mức**: cấp bảng, cấp cột, cấp KPI, cấp quy tắc (tổng cộng 51 tài liệu). Mỗi tài liệu được embedding bằng `all-MiniLM-L6-v2` rồi nạp vào **ChromaDB** kèm metadata để hỗ trợ lọc.

### 3.3.3. Truy hồi ngữ cảnh

`retriever.py` embedding câu hỏi, thực hiện **Top-K similarity search** và định dạng kết quả thành ngữ cảnh schema cho SQL Agent.

> *[Hình 3.2: Trạng thái Vector DB sau khi nạp 51 tài liệu metadata]*

## 3.4. Hiện thực tầng trừu tượng LLM (LLM Abstraction Layer)

### 3.4.1. Giao diện trừu tượng

Toàn bộ tác tử chỉ phụ thuộc vào giao diện `LLMProviderInterface`, nhờ đó có thể đổi mô hình/nhà cung cấp chỉ bằng cấu hình `.env`.

```python
class LLMProviderInterface(abc.ABC):
    @abc.abstractmethod
    def generate(self, prompt, *, system=None, temperature=None,
                 max_tokens=None, stop=None) -> LLMResponse: ...
    @abc.abstractmethod
    def health_check(self) -> dict: ...
```

Hai hiện thực: `OllamaProvider` (mô hình cục bộ) và `OpenAICompatProvider` (mọi dịch vụ chuẩn OpenAI: Groq, OpenRouter, Gemini…).

### 3.4.2. Chuỗi dự phòng (Fallback)

`FallbackProvider` nhận một danh sách provider và thử lần lượt; khi gặp lỗi hết hạn mức (`LLMRateLimitError` – HTTP 429) hoặc lỗi khác, nó tự động chuyển sang provider kế tiếp.

```python
for provider in self.providers:
    try:
        return provider.generate(prompt, system=system, ...)
    except LLMRateLimitError:
        continue   # hết hạn mức → thử provider kế tiếp
```

Chuỗi cấu hình mặc định: **Groq → OpenRouter → Gemini → Ollama (cục bộ)**.

## 3.5. Hiện thực các tác tử và Orchestrator

### 3.5.1. SQL Agent

Prompt gồm *system prompt* (các quy tắc: chỉ `SELECT`, giữ đúng tên bảng dạng PascalCase, JOIN `DimDate` để lọc thời gian, định nghĩa "doanh thu" = `SUM(Revenue)`…) và **few-shot example** mẫu trên schema tour. Đầu ra được làm sạch (loại bỏ markdown, tiền tố) để lấy đúng câu lệnh.

### 3.5.2. Validation Agent (Guardrail)

Tầng Regex chặn danh sách từ khóa nguy hiểm:

```python
FORBIDDEN_KEYWORDS = ["DROP", "DELETE", "TRUNCATE", "ALTER", "UPDATE",
    "INSERT", "CREATE", "REPLACE", "MERGE", "GRANT", "REVOKE", "EXEC", ...]
```

Câu lệnh phải bắt đầu bằng `SELECT`/`WITH`, không chứa nhiều câu lệnh nối nhau, không có comment khả nghi. Tầng LLM soát lại lần nữa. Kết quả kiểm thử cho thấy guardrail chặn **100% các câu phá hoại** trong bộ thử.

### 3.5.3. Insight Agent và Visualization Agent

Insight Agent tính thống kê **xác định** bằng Pandas rồi để LLM diễn giải. Visualization Agent chọn loại biểu đồ (heuristic + LLM) và đóng gói **Plotly JSON** với tên trục, **đơn vị** (VNĐ, khách, điểm…) và `automargin`.

### 3.5.4. SQL Executor và Orchestrator

`sql_executor.py` thực thi câu lệnh trên **engine chỉ-đọc**, tự chèn `LIMIT` và đặt `MAX_EXECUTION_TIME` (giới hạn thời gian), trả về `DataFrame`. `orchestrator.py` điều phối toàn bộ và lưu lịch sử.

## 3.6. Hiện thực API Backend và xác thực

### 3.6.1. Hệ thống API

Hệ thống cung cấp các endpoint chính (đều có schema Pydantic và xử lý ngoại lệ tập trung):

| Nhóm | Endpoint |
|------|----------|
| Hội thoại | `POST /chat`, `POST /generate-sql`, `POST /chart`, `POST /history`, `GET /sessions`, `POST /suggest-questions` |
| Hệ thống | `GET /health`, `GET /database-test`, `GET /system-status`, `GET /stats` |
| Quản trị RAG | `POST /rebuild-vector-db`, `POST /reload-metadata`, `POST /metadata-search` |
| Xác thực | `POST /auth/login`, `GET /auth/me` |

### 3.6.2. Xác thực JWT

Đăng nhập bằng một tài khoản cố định (cấu hình trong `.env`); hệ thống trả về **JWT** có thời hạn. Mọi endpoint nghiệp vụ được bảo vệ bằng dependency kiểm tra token; token hết hạn/không hợp lệ trả mã 401.

> *[Hình 3.3: Giao diện Swagger UI liệt kê các API]*

## 3.7. Hiện thực giao diện (Frontend)

Giao diện đơn trang (SPA) gồm **ba tab**, gọi backend qua Axios (tự đính token, tự xử lý 401).

### 3.7.1. Màn hình đăng nhập

> *[Hình 3.4: Màn hình đăng nhập]*

### 3.7.2. Tab 1 — Chat Assistant

Khung chat hiển thị câu trả lời (hiệu ứng gõ chữ), câu SQL (thu gọn), nhãn an toàn guardrail, biểu đồ, insight và thời gian thực thi. Sidebar liệt kê các cuộc trò chuyện, hỗ trợ **tạo mới, đổi tên, xóa** và **hỏi nối tiếp (multi-turn)**; sau mỗi câu trả lời có **gợi ý câu hỏi tiếp theo** và nút đánh giá 👍/👎.

> *[Hình 3.5: Tab Chat Assistant — câu trả lời kèm SQL, biểu đồ, insight]*
> *[Hình 3.6: Sidebar lịch sử và menu đổi tên/xóa]*

### 3.7.3. Tab 2 — Analytics Dashboard

Khung phân tích cho phép **hỏi nhiều câu liên tục**, mỗi câu cho ra biểu đồ Plotly tương tác, bảng dữ liệu (xuất CSV được) và AI Insight; hỗ trợ multi-turn và lưu lịch sử phân tích.

> *[Hình 3.7: Tab Analytics Dashboard — biểu đồ tương tác + bảng dữ liệu + insight]*

### 3.7.4. Tab 3 — System Management

Hiển thị trạng thái **real-time** của MySQL, Vector DB và LLM; các nút quản trị RAG (dựng lại vector DB, nạp lại metadata, kiểm tra LLM); và bảng **thống kê truy vấn** (tổng truy vấn, tỷ lệ thành công, thời gian trung bình, câu hỏi phổ biến, biểu đồ truy vấn theo ngày).

> *[Hình 3.8: Tab System Management — trạng thái hệ thống và thống kê]*

## 3.8. Đóng gói và triển khai bằng Docker

Hệ thống được đóng gói thành **bốn dịch vụ** trong `docker-compose.yml`: `mysql`, `ollama`, `backend`, `frontend` (phục vụ bằng nginx, có reverse proxy `/api`). Toàn bộ hệ thống khởi chạy bằng một lệnh:

```bash
docker compose up -d --build
docker compose exec backend python /scripts/load_tour_datamart.py   # nạp dữ liệu
curl -X POST http://localhost:8000/rebuild-vector-db                 # dựng vector DB
```

Backend tự động tạo các bảng còn thiếu và nâng cấp lược đồ khi khởi động (auto-migration).

## Kết luận chương 3

Chương 3 đã trình bày công nghệ sử dụng và quá trình hiện thực đầy đủ các thành phần: tầng dữ liệu (ORM, ETL), RAG Engine (metadata, embedding, ChromaDB), tầng trừu tượng LLM với chuỗi dự phòng, bảy tác tử cùng Orchestrator, hệ thống API có xác thực JWT, giao diện ba tab và đóng gói Docker. Hệ thống đã chạy hoàn chỉnh; Chương 4 sẽ tiến hành thực nghiệm và đánh giá định lượng.

---

# CHƯƠNG 4: THỰC NGHIỆM VÀ ĐÁNH GIÁ

Chương này trình bày môi trường thực nghiệm, bộ dữ liệu, phương pháp và chỉ số đánh giá, sau đó phân tích kết quả định lượng về độ chính xác sinh SQL, mức độ an toàn, độ tin cậy, hiệu năng và kiểm thử của hệ thống.

## 4.1. Môi trường thực nghiệm

| Thành phần | Cấu hình |
|------------|----------|
| Triển khai | Docker, 4 dịch vụ (mysql, ollama, backend, frontend) |
| CSDL | MySQL 8.0 |
| Vector DB | ChromaDB (51 tài liệu metadata) |
| Embedding | sentence-transformers/all-MiniLM-L6-v2 (384 chiều) |
| LLM | Chuỗi: Groq `llama-3.1-8b-instant` → Gemini `gemini-2.5-flash-lite` → Ollama `qwen2.5:1.5b` |

## 4.2. Bộ dữ liệu thử nghiệm

Dữ liệu đặt tour gồm **4.418 lượt đặt**, tổ chức theo Star Schema: bảng Fact `FactBooking` và bốn bảng Dimension (`DimDate` – 1.276 ngày, `DimDestination` – 11 điểm đến, `DimCustomerSegment` – 5 nhóm khách, `DimTour` – 6 loại tour). Để đánh giá độ chính xác sinh SQL, xây dựng **bộ câu hỏi kiểm thử gồm 18 câu** bằng tiếng Việt, bao phủ các chiều phân tích (doanh thu, lượng khách, số booking, điểm hài lòng) theo điểm đến, vùng miền, loại tour, nhóm khách và thời gian. Mỗi câu hỏi kèm danh sách **bảng kỳ vọng** (expected tables) để đo độ chính xác chọn bảng.

## 4.3. Phương pháp và chỉ số đánh giá

Hệ thống tự động hóa đánh giá bằng module `evaluate.py`: chạy lần lượt từng câu hỏi qua toàn bộ pipeline (RAG → sinh SQL → kiểm duyệt → thực thi), ghi nhận các chỉ số sau:

- **Tỷ lệ sinh được SQL (Generation rate):** tỷ lệ câu hỏi sinh ra được câu lệnh.
- **Tỷ lệ qua Guardrail:** tỷ lệ câu lệnh được kiểm duyệt là an toàn.
- **Độ chính xác thực thi (Execution accuracy):** tỷ lệ câu lệnh **thực thi thành công** (không lỗi) và trả về kết quả — chỉ số quan trọng nhất trong đánh giá Text-to-SQL.
- **Độ chính xác chọn bảng (Table-selection accuracy):** tỷ lệ câu lệnh sử dụng đúng các bảng kỳ vọng.
- **Số câu phải tự sửa SQL:** số trường hợp kích hoạt cơ chế self-correction.
- **Độ trễ trung bình:** thời gian trung bình xử lý một câu hỏi.

## 4.4. Kết quả đánh giá độ chính xác sinh SQL

Kết quả chạy trên bộ 18 câu hỏi:

| Chỉ số | Giá trị |
|--------|---------|
| Tổng số câu hỏi | 18 |
| Tỷ lệ sinh được SQL | **100,0%** |
| Tỷ lệ qua Guardrail | **100,0%** |
| **Độ chính xác thực thi (Execution accuracy)** | **94,4%** (17/18) |
| Tỷ lệ trả về dữ liệu | 94,4% |
| **Độ chính xác chọn bảng (Table-selection)** | **100,0%** |
| Số câu phải tự sửa SQL | 1 |
| Độ trễ trung bình | 1.732 ms (~1,7 giây) |

> *[Hình 4.1: Kết quả chạy benchmark độ chính xác sinh SQL]*

**Nhận xét:**

- Hệ thống **sinh được SQL cho 100% câu hỏi** và **100% câu lệnh đều an toàn** (qua Guardrail), cho thấy prompt và cơ chế kiểm duyệt hoạt động ổn định.
- **Độ chính xác chọn bảng đạt 100%** — nhờ RAG truy hồi đúng ngữ cảnh schema, hệ thống luôn chọn đúng bảng Fact và Dimension cần thiết.
- **Độ chính xác thực thi đạt 94,4%** (17/18 câu chạy thành công và trả về dữ liệu đúng kỳ vọng) — một kết quả tốt đối với bài toán Text-to-SQL tiếng Việt.
- Phần lớn câu hỏi có độ trễ rất thấp (~0,4–0,6 giây); một số câu cao hơn do phải gọi mô hình dự phòng (xem mục 4.6).

### 4.4.1. Phân tích trường hợp lỗi

Câu duy nhất thất bại là *"Số booking theo quý?"*: mô hình **bịa ra bảng `DimQuarter` và cột `QuarterKey`** không tồn tại (trong khi quý nằm ở cột `DimDate.QuarterNumber`). Cơ chế **self-correction** đã được kích hoạt nhưng câu sửa lại vẫn sai. Đây là biểu hiện điển hình của **ảo giác (hallucination)** ở mô hình ngôn ngữ. Hướng khắc phục: bổ sung quy tắc nghiệp vụ/few-shot ví dụ về truy vấn theo quý, hoặc dùng mô hình embedding đa ngôn ngữ để truy hồi mô tả cột `QuarterNumber` chính xác hơn.

## 4.5. Đánh giá cơ chế an toàn (Guardrail)

Để kiểm tra khả năng phòng thủ, bộ kiểm thử đơn vị đưa vào **12 câu lệnh phá hoại** (DROP, DELETE, UPDATE, INSERT, TRUNCATE, ALTER, stacked queries, comment injection, `INTO OUTFILE`, truy cập `information_schema`…) và **các câu lệnh hợp lệ**. Kết quả: hệ thống **chặn 100% câu lệnh phá hoại** và **không chặn nhầm câu lệnh hợp lệ**. Kết hợp với tài khoản MySQL chỉ-đọc, hệ thống bảo đảm dữ liệu nguồn không thể bị thay đổi qua giao diện chatbot.

## 4.6. Đánh giá độ tin cậy — Cơ chế dự phòng LLM

Trong quá trình chạy benchmark, nhà cung cấp chính (Groq) **nhiều lần đạt giới hạn hạn mức (HTTP 429)**. Tại các thời điểm đó, hệ thống đã **tự động chuyển sang mô hình dự phòng** (Gemini / Ollama) và **hoàn thành toàn bộ 18/18 câu hỏi mà không gián đoạn**. Điều này chứng minh chuỗi fallback hoạt động đúng thiết kế, giúp hệ thống **duy trì hoạt động liên tục** ngay cả khi một nhà cung cấp gặp sự cố — một yêu cầu phi chức năng quan trọng (NFR4).

> *[Hình 4.2: Nhật ký cho thấy hệ thống tự chuyển sang provider dự phòng khi gặp lỗi 429]*

## 4.7. Đánh giá hiệu năng và tài nguyên

Đo lường tài nguyên các container (ở trạng thái nghỉ):

| Container | RAM | CPU | Ghi chú |
|-----------|-----|-----|---------|
| backend | ~0,5–1,5 GB | ~0% | Tăng khi nạp mô hình embedding |
| mysql | ~0,4 GB | thấp | — |
| frontend | ~10 MB | ~0% | nginx phục vụ tĩnh |
| ollama | ~50 MB (nghỉ) | ~0% | Chỉ tải mô hình khi cần fallback |

**Nhận xét:** Nhờ **offload phần suy luận LLM sang dịch vụ API**, mức sử dụng CPU của hệ thống rất thấp; tài nguyên tiêu tốn chủ yếu là RAM của tiến trình backend (mô hình embedding) và MySQL. Hệ thống chạy tốt trên một máy tính cá nhân thông thường.

## 4.8. Kiểm thử đơn vị (Unit test)

Hệ thống có bộ **64 unit test** (pytest) kiểm tra các thành phần quan trọng: guardrail (chặn câu phá hoại, cho phép câu hợp lệ), làm sạch SQL, nhận diện cột thời gian, Insight/Chart agent, chuỗi fallback (chuyển provider khi 429), Router Agent (phân loại), và các endpoint API. **Toàn bộ 64 test đều đạt (pass)**, bảo đảm tính đúng đắn và độ ổn định khi bảo trì.

> *[Hình 4.3: Kết quả chạy 64 unit test đều pass]*

## 4.9. Nhận xét chung

Kết quả thực nghiệm cho thấy hệ thống đạt được các mục tiêu đề ra:

- Sinh SQL chính xác cao (execution accuracy 94,4%, table-selection 100%) cho câu hỏi tiếng Việt.
- An toàn tuyệt đối với dữ liệu (chặn 100% thao tác phá hoại).
- Độ tin cậy cao nhờ chuỗi LLM dự phòng.
- Hiệu năng tốt, tài nguyên hợp lý, dễ triển khai.

## Kết luận chương 4

Chương 4 đã thực nghiệm và đánh giá hệ thống trên bộ dữ liệu đặt tour thực tế. Hệ thống đạt **độ chính xác thực thi 94,4%** và **độ chính xác chọn bảng 100%** trên bộ 18 câu hỏi kiểm thử, **chặn 100% câu lệnh phá hoại**, **duy trì hoạt động liên tục** nhờ cơ chế dự phòng và **vượt qua toàn bộ 64 unit test**. Các kết quả này khẳng định tính khả thi và hiệu quả của giải pháp ứng dụng RAG + LLM trong phân tích dữ liệu.

---

# KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN

## 1. Kết quả đạt được

Đồ án đã hoàn thành mục tiêu xây dựng một **Chatbot AI phân tích dữ liệu từ DataMart** ứng dụng RAG và LLM theo kiến trúc Multi-Agent, đạt chuẩn triển khai thực tế. Cụ thể:

- **Về lý thuyết:** nắm vững và vận dụng các kỹ thuật LLM, RAG, embedding, vector database, Text-to-SQL và mô hình kho dữ liệu Star Schema.
- **Về thiết kế:** đề xuất kiến trúc nhiều tầng kết hợp Micro-Agent và RAG Layer, với bảy tác tử chuyên trách và một Orchestrator điều phối.
- **Về hiện thực:** xây dựng hoàn chỉnh hệ thống gồm backend (FastAPI), RAG Engine (ChromaDB), tầng trừu tượng LLM có **chuỗi dự phòng**, cơ chế **Guardrail nhiều lớp**, frontend ba tab và đóng gói Docker.
- **Về kết quả:** hệ thống cho phép người dùng hỏi dữ liệu bằng tiếng Việt, tự sinh SQL an toàn, trả về câu trả lời, biểu đồ và nhận định; đạt **execution accuracy 94,4%**, **table-selection 100%**, chặn **100%** thao tác phá hoại và vượt **64 unit test**.

## 2. Hạn chế

- Mô hình embedding `all-MiniLM-L6-v2` thiên về tiếng Anh, có thể làm giảm chất lượng truy hồi với một số câu hỏi tiếng Việt.
- Vẫn còn trường hợp mô hình **bịa cấu trúc** (như bảng `DimQuarter`); self-correction chưa khắc phục được mọi lỗi.
- Hệ thống mới dùng **một tài khoản đăng nhập cố định**, chưa quản lý nhiều người dùng/phân quyền.
- Khi phải dùng mô hình cục bộ nhỏ (fallback), chất lượng sinh SQL có thể giảm.

## 3. Hướng phát triển

- **Nâng cấp RAG:** dùng mô hình embedding **đa ngôn ngữ** (multilingual-e5, BGE-M3), bổ sung **tìm kiếm lai (hybrid: BM25 + vector)** và **re-ranking** để tăng độ chính xác truy hồi; bổ sung **dynamic few-shot** (truy hồi cặp câu hỏi–SQL tương tự).
- **Mở rộng quản trị:** hỗ trợ **nhiều người dùng, phân quyền**, gắn lịch sử theo từng người.
- **Mở rộng phân tích:** dự báo (forecasting), phát hiện bất thường (anomaly detection), so sánh kỳ trước tự động.
- **Cải thiện độ chính xác:** tinh chỉnh prompt/business rules, hoặc đánh giá thử nghiệm mô hình lớn hơn; bổ sung kiểm chứng kết quả (result verification).
- **Quan trắc (observability):** thêm logging/tracing chi tiết để theo dõi và tối ưu chất lượng liên tục.

---

*— Hết —*
