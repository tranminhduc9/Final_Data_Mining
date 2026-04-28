# RAG Service — Context Brief

Tài liệu này mô tả bối cảnh, kiến trúc và trạng thái hiện tại của phần RAG service trong đồ án **"Phân tích xu hướng công nghệ dựa trên Đồ thị tri thức"**. Đưa tài liệu này cho AI assistant hoặc thành viên mới để họ nắm được việc đang làm mà không cần đọc lại toàn bộ báo cáo.

---

## 1. Bối cảnh dự án

Đồ án xây dựng một hệ thống tự động thu thập dữ liệu IT từ nhiều nguồn tại Việt Nam (tin tuyển dụng TopDev/ITviec/TopCV, tin tức VnExpress Tech, blog/mạng xã hội), chuyển thành **đồ thị tri thức (Knowledge Graph)** trên Neo4j, và cung cấp một chatbot dựa trên kiến trúc **Graph RAG** để:

- Phân tích xu hướng công nghệ theo thời gian.
- Trả lời câu hỏi về thị trường lao động IT (lương, kỹ năng, công ty).
- Tư vấn lộ trình học tập cá nhân hóa, phân tích khoảng cách kỹ năng.

Khác biệt chính so với RAG truyền thống: hệ thống **kết hợp vector search với graph traversal** để khai thác được các mối quan hệ có cấu trúc (ví dụ: `Job -REQUIRES-> Technology <-USES- Company`).

## 2. Phạm vi của phần này (RAG Service)

Tài liệu này chỉ nói về **RAG service** — một microservice Python độc lập. Các phần khác của hệ thống (backend Go quản lý user, frontend React, data crawler) không nằm trong phạm vi.

RAG service chịu trách nhiệm:

- Embedding dữ liệu Article trong Neo4j (one-shot job).
- Xử lý câu hỏi từ người dùng qua pipeline Graph RAG.
- Trả về câu trả lời có trích dẫn nguồn.
- Cá nhân hóa dựa trên profile người dùng.

## 3. Stack công nghệ đã chọn

| Thành phần | Công nghệ |
|---|---|
| Ngôn ngữ | Python |
| Framework orchestration | LangChain, LangSmith (tracing) |
| Embedding model | `intfloat/multilingual-e5-base` |
| Reranker | `BAAI/bge-reranker-m3` |
| NER (tiếng Việt) | PhoBERT fine-tuned (hoặc Gemini làm tạm) |
| LLM sinh câu trả lời | Gemini 2.5 Flash |
| Graph database | Neo4j (dùng cả graph + vector index native) |
| Relational database | PostgreSQL (user profile, chat history) |
| Cache | Redis (dự kiến) |
| API framework | FastAPI |
| Đánh giá | RAGAS framework |

**Lưu ý quan trọng**: stack này đã được chốt, không thay đổi. Đừng đề xuất Pinecone, Weaviate, hay chuyển sang OpenAI — nhóm dùng Neo4j vector index và Gemini.

## 4. Trạng thái hiện tại

- Data trong Neo4j AuraDB: **đã có** — 526 Article, 384 Technology, 1,735 Company, 120 Job, 318 Skill, 9 Person.
- Embedding trên Article: **chưa có** (0/526) — đây là việc cần làm đầu tiên.
- Vector index trên Neo4j: **chưa tạo**.
- RAG pipeline: **đang code** — config, db client, embedder, retriever đã xong; reranker, prompt_builder, generator, pipeline chưa.
- API service: **chưa bắt đầu**.

## 5. Schema đồ thị tri thức (Neo4j) — ĐÃ KIỂM TRA THỰC TẾ

> Schema này được lấy trực tiếp từ AuraDB (inspect ngày 25/04/2026). Dùng đây làm chuẩn khi viết Cypher và code — không dùng schema cũ trong tài liệu gốc vì có nhiều sai lệch.

### Nodes

| Label | Properties | Số lượng |
|---|---|---|
| `Article` | `title, content, published_date, sentiment_score, source` | 526 |
| `Technology` | `name, category, description, trend_score` | 384 |
| `Company` | `name, industry, location, size, rating` | 1,735 |
| `Job` | `title, level, company_name, salary_min, salary_max, posted_date, source_url` | 120 |
| `Skill` | `name, category, demand_score` | 318 |
| `Person` | `name, role` | 9 |

**Lưu ý quan trọng về Article:**
- Trường text chính là `content` (không phải `description`).
- `source` hiện tại đa số = `"Unknown"` — không dùng làm URL trích dẫn.
- **Không có** property `is_relevant`, `article_type`, `url`, `id` (dùng Neo4j internal `elementId()`).
- `sentiment_score` có thể là `None` hoặc giá trị float (-1.0 đến 1.0).
- Dùng `title + content` để embed — không dùng `title + description`.

### Relationships thực tế (có số lượng)

| Relationship | Số cạnh |
|---|---|
| `(Company)-[:USES]->(Technology)` | 10,445 |
| `(Article)-[:MENTIONS]->(Technology)` | 2,876 |
| `(Job)-[:REQUIRES]->(Technology)` | 1,211 |
| `(Job)-[:REQUIRES]->(Skill)` | 977 |
| `(Article)-[:MENTIONS]->(Company)` | 568 |
| `(Job)-[:HIRES_FOR]->(Company)` | 86 |
| `(Technology)-[:RELATED_TO]->(Technology)` | 70 |
| `(Skill)-[:IS_TECHNOLOGY]->(Technology)` | 22 |

**Lưu ý:** Tất cả relationships hiện **không có thuộc tính** (properties rỗng).

### Sai lệch so với thiết kế ban đầu

| Thiết kế ban đầu | Thực tế trong DB |
|---|---|
| Label `JobRole` | Label `Job` |
| `Article.description` | `Article.content` |
| `Article.url` | `Article.source` (đa số = Unknown) |
| `Article.is_relevant` | Không tồn tại |
| `Article.article_type` | Không tồn tại |
| `Technology.aliases` | `Technology.description` |
| `Company.company_size` | `Company.size` |
| `(Company)-[:HIRES_FOR]->(JobRole)` | `(Job)-[:HIRES_FOR]->(Company)` (đảo chiều) |
| Label `TimePeriod`, `Platform` | Không tồn tại |

## 6. Schema PostgreSQL (chỉ phần RAG cần)

- `users` — `id (UUID), email, password_hash, full_name`.
- `user_profile` — `user_id, job_role, technologies (text[]), location, bio`.
- `chat_session` — `id (UUID), user_id, title, created_at`.
- `chat_message` — `id, session_id, role, content, prompt_tokens, completion_tokens, finish_reason`.

## 7. Kiến trúc RAG Pipeline

### Giai đoạn 1 — Indexing (offline, chạy định kỳ)

```
Data Sources → Selenium Crawler → Gemini Classifier (lọc IT)
    → Cleaning & Chunking → [NER + Embedding song song] → Neo4j
```

### Giai đoạn 2 — Query (online, mỗi lần user hỏi)

```
Câu hỏi → NER + Query Embedding
    → [Vector Search ∥ Graph Traversal ∥ User Context] (song song)
    → Rerank (bge-reranker-m3)
    → Prompt Assembly (LangChain)
    → Gemini 2.5 Flash
    → Phản hồi + trích dẫn nguồn → Lưu lịch sử PostgreSQL
```

**Latency budget** (<3s): Query processing ~200ms, Retrieval ~500ms, Rerank ~300ms, LLM ~1500ms, overhead ~500ms.

## 8. Cấu trúc thư mục RAG Service

```
rag-service/
├── app/
│   ├── main.py                      # FastAPI entrypoint
│   ├── config.py                    # Settings, env
│   ├── api/                         # HTTP layer
│   │   ├── routes_chat.py
│   │   ├── routes_health.py
│   │   └── schemas.py               # Pydantic models
│   ├── core/                        # Các mắt xích RAG
│   │   ├── embedder.py              # multilingual-e5-base
│   │   ├── ner.py                   # PhoBERT
│   │   ├── retriever_vector.py      # Vector search Neo4j
│   │   ├── retriever_graph.py       # Cypher traversal
│   │   ├── retriever_user.py        # User profile từ Postgres
│   │   ├── reranker.py              # bge-reranker-m3
│   │   ├── prompt_builder.py
│   │   ├── generator.py             # Gemini 2.5 Flash
│   │   └── pipeline.py              # Orchestrator
│   ├── db/                          # Connection clients
│   │   ├── neo4j_client.py
│   │   ├── postgres_client.py
│   │   └── redis_client.py
│   ├── models/                      # SQLAlchemy ORM
│   ├── services/                    # Logic nghiệp vụ
│   │   ├── chat_service.py
│   │   └── history_service.py
│   ├── prompts/                     # Prompt templates .txt
│   │   ├── system_prompt.txt
│   │   ├── rag_template.txt
│   │   └── roadmap_template.txt
│   └── utils/
├── scripts/                         # One-shot jobs
│   ├── embed_articles.py            # ⭐ Chặng 0
│   ├── create_vector_index.py
│   ├── reindex.py
│   └── eval_ragas.py
├── tests/
│   ├── unit/
│   ├── integration/
│   └── eval/
├── notebooks/
├── .env.example
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## 9. Lộ trình implement theo chặng

Nguyên tắc: **dựng đường ống thô end-to-end trước, tối ưu sau**.

### Chặng 0 — Embedding & Vector Index (LÀM NGAY)
- Viết `scripts/embed_articles.py`: load `multilingual-e5-base`, quét toàn bộ 526 `Article` trong Neo4j, embed `title + content` (dùng `content`, không phải `description`), ghi lại làm property `embedding` (768 chiều).
- Viết `scripts/create_vector_index.py`: tạo vector index Neo4j bằng `CREATE VECTOR INDEX ... FOR (a:Article) ON (a.embedding)` với cosine similarity.
- Test bằng `db.index.vector.queryNodes` — phải trả về kết quả.
- **Không dùng** filter `WHERE a.is_relevant = true` (property không tồn tại trong DB thực tế).

### Chặng 1 — RAG thô chạy được
Bỏ qua rerank, user context, cache. Mục tiêu: hỏi → ra câu trả lời.
- `core/embedder.py` ✅ — wrapper reuse model (đã xong).
- `core/retriever.py` ✅ — vector search Neo4j (đã xong, cần fix filter `is_relevant`).
- `core/retriever_graph.py` — nhận list entity từ query, chạy Cypher 1-hop trên graph thực tế (dùng `Job`, `Company`, `Technology`, `Skill`).
- `core/prompt_builder.py` — ghép context vào template có đánh số `[1][2]`.
- `core/generator.py` — gọi Gemini 2.5 Flash qua LangChain.
- `core/pipeline.py` — hàm `answer(query)` ghép tất cả.
- Chạy thử bằng script hoặc notebook.

### Chặng 2 — Thêm NER
- `core/ner.py` — dùng PhoBERT (hoặc Gemini tạm) extract entities từ query.
- Thay phần hardcode entity ở chặng 1.

### Chặng 3 — Thêm Reranker
- `core/reranker.py` — bge-reranker-m3, nhận query + candidates, trả top-5.
- Chèn vào giữa retrieval và prompt_builder.
- So sánh chất lượng trước/sau bằng RAGAS hoặc eval thủ công 20 câu.

### Chặng 4 — Thêm User Context
- `db/postgres_client.py`, `models/user_profile.py`.
- `core/retriever_user.py` — lấy profile từ Postgres.
- User context **không** qua reranker, chỉ nhét thẳng vào prompt ở block riêng.

### Chặng 5 — API & hoàn thiện
- Viết `api/routes_chat.py`, `services/chat_service.py`.
- Lưu `chat_session`, `chat_message` vào Postgres.
- Redis cache cho query embedding.
- Fallback: graph rỗng → pure vector + prefix "Dựa trên bài viết liên quan...".
- Bật LangSmith tracing.

## 10. Các lưu ý khi code

- **Prompt tách file**: để trong `prompts/*.txt`, không nhúng vào Python string. Prompt sẽ sửa rất nhiều trong quá trình tuning.
- **Cypher query**: viết dưới dạng tham số hóa (parameterized), không dùng f-string nối vào — tránh Cypher injection và dễ cache plan.
- **Connection pool Neo4j**: dùng driver singleton, đừng tạo session mỗi request.
- **Model loading**: embedder và reranker load một lần khi start service (lazy singleton), đừng load mỗi lần gọi.
- **Fallback khi retrieval rỗng**: phải có, đừng để LLM tự bịa.
- **Trích dẫn nguồn**: LLM phải trả về format `[1]`, `[2]` khớp với Article trong context. Validate output trước khi trả về user.

## 11. Đội hình và trách nhiệm

| Người | Vai trò | Việc trong RAG service |
|---|---|---|
| Nguyễn Thế Quang | AI Engineer | Chặng 0, 1, 2, 3 (core RAG) |
| Nguyễn Hữu An | Database & DevOps | Neo4j index, Redis, Postgres setup |
| Nguyễn Việt Phúc | Backend | Chặng 4, 5 (API, user context, history) |
| Nguyễn Trung Kiên | Tester/QA | Bộ test 50 câu, RAGAS eval, song song với chặng 1–3 |

---

## Cách dùng tài liệu này với AI assistant

Khi hỏi AI (Claude, ChatGPT, Gemini...) về task liên quan đến RAG service, hãy:

1. Paste toàn bộ file này vào đầu cuộc hội thoại.
2. Nêu rõ đang ở **chặng nào** và cần hỗ trợ việc gì cụ thể.
3. Nhấn mạnh các ràng buộc: stack đã chốt, không đề xuất thay đổi công nghệ, không sinh code khi chưa cần.

Ví dụ prompt tốt:

> "Đây là context dự án của mình [paste file]. Mình đang ở Chặng 1, đã embed xong toàn bộ Article và tạo vector index. Giờ mình muốn viết `core/retriever_vector.py` — hãy gợi ý approach, không cần code."
