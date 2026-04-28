# Backend Architecture — Microservices (Go + Python)

## 1. Mục tiêu thiết kế

Backend được triển khai theo mô hình **microservices**, trong đó:

- **Golang API Service** là service chính, public-facing, chịu trách nhiệm:
  - expose toàn bộ API theo tài liệu `API_DOCs_v1.md`
  - quản lý authentication / authorization
  - quản lý kết nối và thao tác với PostgreSQL
  - xử lý business logic, orchestration, validation, SSE streaming
- **Python AI Service** là service nội bộ, chỉ tập trung vào:
  - OCR
  - LLM inference / summarization
  - AI recommendation / model serving

> Frontend chỉ gọi vào Golang API Service. Golang sẽ gọi tiếp Python AI Service khi cần AI.

---

## 2. Kiến trúc tổng thể

```text
Frontend / Web / Mobile
          |
          v
   Golang API Service
   - REST API /api/v1
   - JWT Auth
   - SSE chat stream
   - PostgreSQL access
   - Business orchestration
          |
          +--------------------+
          |                    |
          v                    v
    PostgreSQL           Python AI Service
    - users              - LLM summary
    - chat_session       - chat generation
    - chat_message       - OCR inference
```

### Nguyên tắc giao tiếp

- **Frontend → Golang**: HTTP REST / SSE
- **Golang → Python**: internal HTTP API
- **Golang → PostgreSQL**: SQL / repository layer

Giai đoạn đầu nên dùng **HTTP nội bộ** giữa Go và Python để dễ triển khai. Khi hệ thống lớn hơn có thể chuyển sang **gRPC**.

---

## 3. Phân chia trách nhiệm theo service

### 3.1. Golang API Service

Đây là service trung tâm của backend.

**Phụ trách các nhóm endpoint public:**

- `/api/v1/radar/*`
- `/api/v1/compare/*`
- `/api/v1/graph/*`
- `/api/v1/auth/*`
- `/api/v1/chat/*`

**Nhiệm vụ chính:**

- parse request và validate input
- kiểm tra JWT / quyền truy cập
- đọc / ghi dữ liệu PostgreSQL
- tổng hợp dữ liệu trả về cho frontend
- gọi Python AI Service ở các luồng cần AI
- stream phản hồi chat qua SSE

### 3.2. Python AI Service

Đây là service nội bộ, không expose trực tiếp cho frontend.

**Chức năng chính:**

- sinh nội dung LLM summary cho `/compare/llm-summary`
- xử lý chatbot generation cho `/chat/session/{session_id}/messages`
- OCR pipeline cho dữ liệu tài liệu / ảnh nếu cần mở rộng
- nạp model, inference, prompt orchestration

**Internal endpoints gợi ý:**

- `POST /internal/ai/llm-summary`
- `POST /internal/ai/chat-stream`
- `POST /internal/ai/ocr`
- `GET /internal/health`

---

## 4. Mapping API tài liệu sang service thực tế

| Nhóm API | Public endpoint | Service sở hữu chính | Ghi chú |
| --- | --- | --- | --- |
| Radar | `/api/v1/radar/top4`, `/search`, `/top10`, `/export-*` | Golang | đọc dữ liệu analytics từ PostgreSQL / view / materialized view |
| Compare | `/api/v1/compare/search` | Golang | business logic + query dữ liệu thống kê |
| Compare AI Summary | `/api/v1/compare/llm-summary` | Golang gọi Python | Go điều phối, Python sinh summary |
| Graph | `/api/v1/graph/explore`, `/filter` | Golang | query dữ liệu graph / relation |
| Authentication | `/api/v1/auth/*` | Golang | login, register, refresh, me |
| Chatbot | `/api/v1/chat/*` | Golang gọi Python | Go quản session + message DB, Python sinh câu trả lời |

---

## 5. Thiết kế thư mục backend đề xuất

```text
backend/
├── docker-compose.yml
├── .env.example
│
├── golang-api/
│   ├── cmd/
│   │   └── api/
│   │       └── main.go                # bootstrap HTTP server
│   ├── internal/
│   │   ├── config/                    # env, app config, db config
│   │   ├── middleware/                # auth, logging, recovery, cors
│   │   ├── domain/                    # entity / model nghiệp vụ
│   │   │   ├── user.go
│   │   │   ├── chat.go
│   │   │   ├── radar.go
│   │   │   ├── compare.go
│   │   │   └── graph.go
│   │   ├── dto/                       # request/response DTO
│   │   ├── handler/                   # HTTP handlers
│   │   │   ├── auth_handler.go
│   │   │   ├── radar_handler.go
│   │   │   ├── compare_handler.go
│   │   │   ├── graph_handler.go
│   │   │   └── chat_handler.go
│   │   ├── service/                   # business logic
│   │   │   ├── auth_service.go
│   │   │   ├── radar_service.go
│   │   │   ├── compare_service.go
│   │   │   ├── graph_service.go
│   │   │   ├── chat_service.go
│   │   │   └── ai_client.go           # gọi Python AI Service
│   │   ├── repository/
│   │   │   ├── postgres/
│   │   │   │   ├── user_repository.go
│   │   │   │   ├── chat_session_repository.go
│   │   │   │   ├── chat_message_repository.go
│   │   │   │   ├── radar_repository.go
│   │   │   │   ├── compare_repository.go
│   │   │   │   └── graph_repository.go
│   │   ├── router/
│   │   │   └── router.go              # mount /api/v1 routes
│   │   └── sse/
│   │       └── stream.go              # SSE helper cho chat
│   ├── migrations/                    # SQL migration files
│   ├── Dockerfile
│   └── go.mod
│
├── python-api/
│   ├── app/
│   │   ├── main.py                    # FastAPI internal AI service
│   │   ├── routers/
│   │   │   ├── llm.py
│   │   │   └── ocr.py
│   │   ├── services/
│   │   │   ├── model_loader.py
│   │   │   ├── inference.py
│   │   │   └── prompt_builder.py
│   │   ├── schemas/
│   │   │   ├── llm.py
│   │   │   └── ocr.py
│   │   └── core/
│   │       └── config.py
│   ├── models/
│   ├── requirements.txt
│   └── Dockerfile
│
└── k8s/
    ├── golang-api.yaml
    ├── python-api.yaml
    └── postgres.yaml
```

---

## 6. Thiết kế theo domain từ tài liệu API

### 6.1. Radar Domain

Phục vụ:

- top 4 công nghệ tăng trưởng nhanh
- search biểu đồ xu hướng
- export PNG / CSV
- top 10 công nghệ

**Nên nằm hoàn toàn ở Golang**, vì đây là nghiệp vụ query dữ liệu và trả response cho frontend.

### 6.2. Compare Domain

Phục vụ:

- so sánh chỉ số tăng trưởng giữa các công nghệ
- sinh summary bằng LLM

**Phần search / thống kê** nằm ở Golang.  
**Phần summary AI** gọi Python.

### 6.3. Graph Domain

Phục vụ:

- explore graph
- filter graph theo sentiment, salary, location

**Nên nằm ở Golang** vì đây là orchestration + data query layer.

### 6.4. Auth Domain

Phục vụ:

- register
- login
- refresh
- logout
- me

**Nằm hoàn toàn ở Golang**, dùng PostgreSQL để lưu user, password hash, session/token metadata nếu cần.

### 6.5. Chat Domain

Phục vụ:

- tạo chat session
- load lịch sử message
- gửi message mới và nhận phản hồi dạng SSE

**Go** quản lý session/message persistence trong PostgreSQL.  
**Python** sinh nội dung assistant reply.

---

## 7. Thiết kế database theo tài liệu hiện có

Theo `client_database_docs.md`, hiện PostgreSQL đã xác định rõ 3 bảng cốt lõi:

- `users`
- `chat_session`
- `chat_message`

### Ownership khuyến nghị

- Golang là service **duy nhất** được đọc/ghi trực tiếp vào PostgreSQL
- Python không truy cập database nghiệp vụ trực tiếp, trừ khi có use case đặc biệt
- Python chỉ nhận payload từ Go và trả kết quả AI

Cách này giúp:

- giữ logic dữ liệu tập trung
- dễ kiểm soát transaction
- tránh coupling giữa AI service và schema database

### Lưu ý về dữ liệu Radar / Compare / Graph

Tài liệu database hiện mới cover **auth và chat**. Để phục vụ đúng API tài liệu, sau này nên bổ sung thêm các nguồn dữ liệu analytics như:

- bảng thống kê công nghệ theo tháng
- bảng sentiment / salary aggregate
- bảng quan hệ công nghệ để dựng graph
- materialized views phục vụ dashboard query nhanh

---

## 8. Luồng xử lý đề xuất

### 8.1. Chat SSE Flow

```text
Frontend -> POST /api/v1/chat/session/{id}/messages
        -> Golang xác thực JWT
        -> Golang lưu user message vào PostgreSQL
        -> Golang gọi Python AI Service
        -> Python stream/generate assistant response
        -> Golang trả SSE về frontend
        -> Golang lưu assistant message vào PostgreSQL
```

### 8.2. Compare Summary Flow

```text
Frontend -> GET /api/v1/compare/llm-summary
        -> Golang query số liệu so sánh từ PostgreSQL
        -> Golang gửi payload sang Python
        -> Python tạo summary bằng LLM
        -> Golang trả JSON cho frontend
```

---

## 9. Nguyên tắc triển khai

### Bắt buộc

- mọi public API phải đi qua Golang
- mọi truy cập PostgreSQL nghiệp vụ phải đi qua repository của Golang
- Python chỉ là AI worker service
- versioning thống nhất dưới `/api/v1`
- auth bắt buộc cho các endpoint chat và thông tin người dùng

### Nên có thêm

- `GET /health` cho từng service
- structured logging
- request ID / trace ID
- timeout khi Go gọi Python
- retry có kiểm soát cho AI call
- rate limiting cho chat API

---

## 10. Kết luận

Thiết kế phù hợp nhất cho giai đoạn hiện tại là:

- **Golang = API Gateway + Business Service + PostgreSQL owner**
- **Python = Internal AI Inference Service**

Cách chia này bám sát cả hai tài liệu:

- đúng với phạm vi endpoint trong `API_DOCs_v1.md`
- đúng với ownership dữ liệu chat/user trong `client_database_docs.md`
- dễ scale độc lập giữa business backend và AI workload
- dễ deploy lên Docker Compose trước, sau đó nâng lên Kubernetes