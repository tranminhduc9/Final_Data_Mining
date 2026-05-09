# Tiến độ xây dựng RAG Service

## Tổng quan pipeline (không NER, không Graph)

**Câu hỏi chung** (xu hướng tech, thị trường lao động):
```
query → embed → Neo4j vector search (top-20) → rerank (top-5) → build prompt → Gemini → answer
```

**Câu hỏi cá nhân hóa** (tư vấn lộ trình, gap kỹ năng):
```
query → embed → [Neo4j vector search ∥ Postgres user_profile] → rerank (top-5) → build prompt (+ user block) → Gemini → answer
```

---

## Các bước cần làm

| # | File | Trạng thái |
|---|---|---|
| 1 | `app/config.py` | ✅ Xong |
| 2 | `app/db/neo4j_client.py` | ✅ Xong |
| 3 | `app/db/postgres_client.py` | ✅ Xong |
| 4 | `app/core/embedder.py` | ✅ Xong |
| 5 | `app/core/retriever.py` | ✅ Xong (đã fix schema thực tế) |
| 6 | `app/core/retriever_user.py` | ⬜ Chưa |
| 7 | `app/core/reranker.py` | ✅ Xong |
| 8 | `app/prompts/system_prompt.txt` + `rag_template.txt` | ✅ Xong |
| 9 | `app/core/prompt_builder.py` | ✅ Xong |
| 10 | `app/core/generator.py` | ✅ Xong |
| 11 | `app/core/pipeline.py` | ✅ Xong |
| 12 | `app/models/chat.py` + `app/models/user.py` | ⬜ Chưa |
| 13 | `app/api/schemas.py` | ⬜ Chưa |
| 14 | `app/api/routes_chat.py` + `routes_health.py` | ⬜ Chưa |
| 15 | `app/services/chat_service.py` | ⬜ Chưa |
| 16 | `app/main.py` | ⬜ Chưa |
| 17 | `scripts/embed_articles.py` + `create_vector_index.py` | ✅ Xong (chưa chạy) |
| 18 | `requirements.txt` + `Dockerfile` | ⬜ Chưa |

---

## Chi tiết từng bước

### ✅ Bước 1 — `app/config.py`
**File:** `src/ai-rag-core/app/config.py`

**Giải thích nhanh:**
- Đọc tất cả biến môi trường từ `.env` qua `pydantic-settings` — tự validate kiểu dữ liệu, tự báo lỗi nếu thiếu key bắt buộc
- `neo4j_uri`, `neo4j_password`, `gemini_api_key` là bắt buộc — không có trong `.env` thì app crash ngay khi start (đúng ý đồ)
- `use_local_neo4j=true` trong `.env` → tự động dùng `localhost:7687` thay vì AuraDB — tiện khi dev
- `neo4j_vector_index` lưu tên index để dùng chung, không hardcode rải rác
- `@lru_cache` → `get_settings()` chỉ đọc `.env` một lần duy nhất, các module khác gọi `get_settings()` thoải mái
- **Đã bỏ Redis** — project không dùng

### ✅ Bước 5 — `app/core/retriever.py`
**File:** `src/ai-rag-core/app/core/retriever.py`

**Giải thích nhanh:**
- Embed câu hỏi bằng `embed_query()` (prefix `"query: "`) rồi gọi `db.index.vector.queryNodes` trên Neo4j
- Tên index lấy từ `settings.neo4j_vector_index` — không hardcode
- Trả về top-20 mặc định, sau đó reranker sẽ chọn lại top-5
- Cypher dùng parameterized (`$index_name`, `$embedding`) — không nối f-string

**Fix schema thực tế (25/04/2026):**
- Đổi `article.description` → `article.content` (field text thực tế trong DB)
- Đổi `article.url` → `article.source`
- Bỏ `WHERE article.is_relevant = true` (property không tồn tại trong DB)
- Đổi `article.id` → `elementId(article)` (node không có property `id`)
- Thêm `article.sentiment_score` vào kết quả trả về

---

### ✅ Bước 4 — `app/core/embedder.py`
**File:** `src/ai-rag-core/app/core/embedder.py`

**Giải thích nhanh:**
- Load model `intfloat/multilingual-e5-base` một lần duy nhất qua `@lru_cache` — không load lại mỗi request
- `embed_query()` — dùng prefix `"query: "` khi embed câu hỏi của user (đúng yêu cầu của multilingual-e5)
- `embed_passage()` — dùng prefix `"passage: "` khi embed Article để index, prefix khác thì cosine similarity mới chính xác
- `embed_batch()` — dùng trong script offline `embed_articles.py`, encode nhiều Article một lúc với `batch_size=32`

---

### ✅ Bước 3 — `app/db/postgres_client.py`
**File:** `src/ai-rag-core/app/db/postgres_client.py`

**Giải thích nhanh:**
- `Base` là class gốc cho tất cả ORM model (models/chat.py, models/user.py sẽ kế thừa)
- `get_engine()` — singleton engine, `pool_size=10` đủ cho dev, tự scale connection
- `get_session()` — async generator dùng làm dependency injection trong FastAPI (`Depends(get_session)`)
- `create_tables()` — gọi khi app start lần đầu để tạo bảng nếu chưa có
- `close_engine()` — gọi khi app shutdown trong lifespan FastAPI

---

### ✅ Bước 11 — `app/core/pipeline.py`
**File:** `src/ai-rag-core/app/core/pipeline.py`

**Giải thích nhanh:**
- Hàm `answer(query)` — entry point duy nhất của RAG pipeline
- Luồng: `vector_search(top-20)` → `rerank(top-5)` → `build_messages()` → `generate()` → trả dict
- Fallback: nếu vector search không trả về kết quả nào → trả thẳng câu thông báo, không gọi LLM
- Trả về `{"answer", "sources", "query"}` — `sources` là list article để frontend render trích dẫn

---

### ✅ Bước 10 — `app/core/generator.py`
**File:** `src/ai-rag-core/app/core/generator.py`

**Giải thích nhanh:**
- `get_llm()` — singleton `ChatGoogleGenerativeAI` với `temperature=0.2` (ít sáng tạo, bám sát context)
- `generate(messages)` — async, convert messages sang `SystemMessage`/`HumanMessage` của LangChain rồi gọi `ainvoke()`
- Dùng `langchain-google-genai` làm adapter — dễ swap model sau này

---

### ✅ Bước 9 — `app/core/prompt_builder.py`
**File:** `src/ai-rag-core/app/core/prompt_builder.py`

**Giải thích nhanh:**
- Load prompt từ file `.txt` trong `app/prompts/` — không hardcode string trong Python
- `build_messages()` — trả list messages format LangChain (`role/content`)
- `_build_context_block()` — đánh số `[1]`, `[2]`, ... cho từng article; cắt content tại 800 ký tự tránh vượt context window
- Hiển thị tiêu đề + ngày + nội dung để LLM có đủ thông tin trích dẫn

---

### ✅ Bước 8 — `app/prompts/`
**File:** `src/ai-rag-core/app/prompts/system_prompt.txt`, `rag_template.txt`

**Giải thích nhanh:**
- `system_prompt.txt` — định nghĩa vai trò AI, quy tắc trích dẫn `[1][2]`, không bịa thông tin, fallback nếu thiếu data
- `rag_template.txt` — template có 2 placeholder `{context}` và `{query}`, tách bạch context và câu hỏi rõ ràng

---

### ✅ Bước 7 — `app/core/reranker.py`
**File:** `src/ai-rag-core/app/core/reranker.py`

**Giải thích nhanh:**
- `get_reranker()` — load `BAAI/bge-reranker-m3` một lần qua `@lru_cache`, dùng `CrossEncoder` (khác embedder — không tạo vector, chấm điểm từng cặp query-passage trực tiếp)
- `rerank(query, candidates, top_k=5)` — nhận list dict từ `vector_search()`, tạo cặp `(query, title+content)`, gọi `model.predict()` batch một lần, gắn `rerank_score`, sort và trả top-5
- `_build_passage()` — ghép `title + content` nhất quán với cách embed

---

### ✅ Bước 2 — `app/db/neo4j_client.py`
**File:** `src/ai-rag-core/app/db/neo4j_client.py`

**Giải thích nhanh:**
- `_driver` là singleton global — chỉ tạo một lần duy nhất khi lần đầu gọi `get_driver()`, tất cả request dùng chung
- `max_connection_pool_size=50` — driver tự quản lý pool, không tạo connection mới mỗi request
- `run_query(cypher, params)` — hàm dùng chung toàn app, nhận Cypher parameterized (không dùng f-string nối thẳng vào query)
- `close_driver()` — gọi khi app shutdown (trong lifespan của FastAPI)
- `ping()` — dùng cho `GET /health` để kiểm tra Neo4j còn sống không

---

### ✅ Bước 17 — `scripts/embed_articles.py` + `scripts/create_vector_index.py`
**File:** `src/ai-rag-core/scripts/embed_articles.py`, `src/ai-rag-core/scripts/create_vector_index.py`

**Trạng thái:** Code xong, chưa chạy (cần chạy để embed 526 Article và tạo vector index).

**Giải thích nhanh — `embed_articles.py`:**
- Kết nối AuraDB, tự đổi `neo4j+s://` → `neo4j+ssc://` để bypass SSL verify trên macOS
- Lấy toàn bộ Article có `embedding IS NULL` (chạy lại an toàn, không overwrite bài đã embed)
- Ghép `title + content` làm văn bản đầu vào (không dùng `description`)
- Gọi `embed_batch()` với `batch_size=32`, có progress bar
- Ghi embedding lên Neo4j theo `WRITE_BATCH=100` dùng `UNWIND` + `elementId()`
- In kết quả verify cuối cùng

**Giải thích nhanh — `create_vector_index.py`:**
- Kiểm tra index đã tồn tại chưa trước khi tạo — chạy lại không bị lỗi
- Tạo `VECTOR INDEX article_embedding_index` trên `(a:Article) ON (a.embedding)`, 768 chiều, cosine similarity
- Poll trạng thái cho đến khi `ONLINE`
- Tự test bằng cách query 1 Article mẫu qua `db.index.vector.queryNodes`

**Cách chạy (thứ tự):**
```bash
cd src/ai-rag-core
python -m scripts.embed_articles       # Bước 1 — mất ~5-10 phút lần đầu (tải model)
python -m scripts.create_vector_index  # Bước 2 — tạo và verify index
```
