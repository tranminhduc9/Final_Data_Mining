# Report 2 — Trạng thái triển khai code hiện tại

> Ngày: 2026-04-21  
> Phạm vi: `src/backend/golang-api` và `src/backend/python-api`

---

## 1. Tổng quan nhanh

| Thành phần | Trạng thái |
|---|---|
| Cấu trúc thư mục | Đầy đủ, đúng theo thiết kế |
| Kết nối PostgreSQL | **Hoàn chỉnh** |
| JWT Middleware | **Hoàn chỉnh** |
| Router / Route mount | **Hoàn chỉnh** |
| Auth handler (register/login/refresh/logout/me) | **Scaffold** — chưa đọc/ghi DB |
| Radar handler (top4/search/top10/export) | Stub `501 Not Implemented` |
| Compare handler (search/llm-summary) | Stub `501 Not Implemented` |
| Graph handler (explore/filter) | Stub `501 Not Implemented` |
| Chat handler (session/messages) | Stub `501 Not Implemented` |
| Repository layer (tất cả) | Struct rỗng, chưa có method |
| Service layer (radar/compare/graph/chat) | Struct rỗng, chưa có method |
| SSE helper | **Hoàn chỉnh** |
| Migration SQL | **Hoàn chỉnh** |
| Python AI Service | **Scaffold** — chỉ có health checks |

---

## 2. golang-api — Chi tiết từng thành phần

### 2.1. Entrypoint — `cmd/api/main.go`

Đã hoàn chỉnh. Thứ tự khởi động:
1. Load config từ `.env`
2. Kết nối PostgreSQL (timeout 10s)
3. Khởi tạo Gin engine qua `router.New(cfg, db)`
4. Listen trên `PORT` (default `8080`)

### 2.2. Config — `internal/config/config.go`

Đã hoàn chỉnh. Load từ các file `.env`, `.env.example` theo thứ tự ưu tiên. Các biến:

| Biến env | Default |
|---|---|
| `APP_ENV` | `development` |
| `PORT` | `8080` |
| `PostgreSQL_CONNECTION_STRING` | bắt buộc, lỗi nếu thiếu |
| `PYTHON_AI_BASE_URL` | `http://localhost:8001` |
| `JWT_SECRET` | `change-this-in-production` |

### 2.3. Database — `internal/database/postgres.go`

Đã hoàn chỉnh. Dùng `pgx/v5` connection pool, ping kiểm tra sau khi kết nối.

### 2.4. Middleware — `internal/middleware/jwt.go`

Đã hoàn chỉnh. Cung cấp:
- `GenerateToken(userID, email, role, ttl)` — ký HS256, claims: `sub`, `email`, `role`, `exp`, `iat`
- `RequireAuth()` — gin middleware, extract và validate Bearer token, set context keys: `user_id`, `email`, `role`

### 2.5. Router — `internal/router/router.go`

Đã hoàn chỉnh. Toàn bộ route đã mount đúng theo `API_DOCs_v1.md`:

| Route group | Auth required |
|---|---|
| `GET /health` | No |
| `GET /api/v1/health` | No |
| `GET /api/v1/radar`, `/compare`, `/graph` | No |
| `GET /api/v1/chat` | Yes |
| `GET/POST /api/v1/radar/*` | No |
| `GET /api/v1/compare/*` | No |
| `GET /api/v1/graph/*` | No |
| `POST /api/v1/auth/register`, `/login`, `/refresh` | No |
| `POST /api/v1/auth/logout`, `GET /auth/me` | Yes |
| `POST/GET /api/v1/chat/session/*` | Yes |

**Lưu ý:** `db` được truyền vào `router.New()` nhưng chưa được inject xuống handler/service/repository nào.

### 2.6. Domain models

Đã định nghĩa đầy đủ struct, chưa có method:

| File | Struct |
|---|---|
| `user.go` | `User{ID, Email, FullName, SubscriptionTier}` |
| `chat.go` | `ChatSession{ID, UserID, Title, ModelUsed}`, `ChatMessage{ID, SessionID, Role, Content}` |
| `radar.go` | `RadarTrend{Technology, Sentiment, JobCount, YoY, GrowthRate}` |
| `compare.go` | `CompareMetric{Technology, GrowthRate, YoY, MoM, Jobs}` |
| `graph.go` | `GraphNode{ID, Label}`, `GraphEdge{Source, Target}` |

**Thiếu:** `ChatSession` không có `SystemPrompt`, `CreatedAt`, `UpdatedAt` so với schema DB. `ChatMessage` không có `PromptTokens`, `CompletionTokens`, `FinishReason`, `CreatedAt`.

### 2.7. DTO — `internal/dto/auth.go`

Đã hoàn chỉnh cho luồng auth:
- `RegisterRequest` — `email` (required, email format), `password` (required, min=8), `full_name`
- `LoginRequest` — `email`, `password`
- `RefreshTokenRequest` — `refresh_token`
- `AuthResponse` — `access_token`, `refresh_token`, `token_type`, `expires_in`, `message`
- `MeResponse` — `user_id`, `email`, `role`

**Thiếu:** DTO cho các domain radar, compare, graph, chat chưa được tạo.

### 2.8. Service layer

| File | Trạng thái |
|---|---|
| `auth_service.go` | Có `BuildLoginResponse()` nhưng dùng hardcode `"demo-user-id"`, không query DB, không kiểm tra password |
| `ai_client.go` | Struct + constructor có `http.Client` với timeout 60s, chưa có method gọi Python |
| `radar_service.go` | Struct rỗng |
| `compare_service.go` | Struct rỗng |
| `graph_service.go` | Struct rỗng |
| `chat_service.go` | Struct rỗng |

### 2.9. Handler layer

| Handler | Trạng thái |
|---|---|
| `auth_handler.go` | Register: validate DTO, trả scaffold JSON (không save DB). Login: gọi `BuildLoginResponse()`, trả JWT thật. Refresh: validate DTO, trả scaffold. Logout: trả scaffold. Me: đọc từ JWT context, **hoạt động đúng**. |
| `radar_handler.go` | Toàn bộ method trả `501 Not Implemented` |
| `compare_handler.go` | Toàn bộ method trả `501 Not Implemented` |
| `graph_handler.go` | Toàn bộ method trả `501 Not Implemented` |
| `chat_handler.go` | Toàn bộ method trả `501 Not Implemented` |

### 2.10. Repository layer

Tất cả 6 repository (`UserRepository`, `ChatSessionRepository`, `ChatMessageRepository`, `RadarRepository`, `CompareRepository`, `GraphRepository`) chỉ có struct và constructor, **chưa có method nào**.

### 2.11. SSE helper — `internal/sse/stream.go`

Đã hoàn chỉnh. `SetHeaders()` set đúng 4 header cần thiết cho SSE: `Content-Type: text/event-stream`, `Cache-Control: no-cache`, `Connection: keep-alive`, `X-Accel-Buffering: no`.

### 2.12. Migration — `migrations/0001_init.sql`

Đã hoàn chỉnh, tạo đúng 3 bảng theo `client_database_docs.md`:
- `users` với `pgcrypto` extension
- `chat_session` với FK → `users.id ON DELETE CASCADE`
- `chat_message` với FK → `chat_session.id ON DELETE CASCADE`, CHECK constraint cho `role`

### 2.13. Dependencies — `go.mod`

Go 1.23. Các thư viện chính:
- `gin v1.10.0` — HTTP framework
- `golang-jwt/jwt v5.2.2` — JWT
- `pgx/v5 v5.7.2` — PostgreSQL driver
- `godotenv v1.5.1` — env loader

---

## 3. python-api — Chi tiết từng thành phần

### 3.1. Entrypoint — `app/main.py`

Scaffold. FastAPI app với:
- `GET /health` — trả `{status, service, environment}`
- `GET /internal/health` — trả `{status, postgres_configured}`
- Mount `llm_router` và `ocr_router`

### 3.2. Config — `app/core/config.py`

Dùng `pydantic-settings`. Các biến:

| Biến | Default |
|---|---|
| `APP_NAME` | `TechPulse AI Service` |
| `APP_ENV` | `development` |
| `PORT` | `8001` |
| `POSTGRES_CONNECTION_STRING` | `None` (optional) |

### 3.3. Routers

| File | Endpoint | Trạng thái |
|---|---|---|
| `routers/llm.py` | `GET /internal/ai/llm/health` | Chỉ trả health check |
| `routers/ocr.py` | `GET /internal/ai/ocr/health` | Chỉ trả health check |

**Thiếu hoàn toàn:**
- `POST /internal/ai/llm-summary`
- `POST /internal/ai/chat-stream`
- `POST /internal/ai/ocr`

### 3.4. Services — `app/services/inference.py`

Chỉ có hàm `warmup_models()` trả `{"status": "not_loaded"}`. Chưa có model loading hay inference logic.

### 3.5. Dependencies — `requirements.txt`

- `fastapi 0.116.1`
- `uvicorn[standard] 0.35.0`
- `pydantic 2.11.7`
- `pydantic-settings 2.10.1`
- `python-dotenv 1.1.1`

**Lưu ý:** Chưa có thư viện LLM (openai, anthropic, google-generativeai, transformers, ...) hay OCR (pytesseract, easyocr, ...).

---

## 4. Những gì hoạt động được ngay hôm nay

| Tính năng | Endpoint | Ghi chú |
|---|---|---|
| Health check | `GET /health`, `GET /api/v1/health` | OK |
| Login (scaffold) | `POST /api/v1/auth/login` | Trả JWT thật, nhưng không check DB, hardcode `user_id = "demo-user-id"` |
| Me | `GET /api/v1/auth/me` | Đọc từ JWT context, hoạt động đúng nếu có valid token |
| JWT validation | Tất cả route có `RequireAuth()` | Từ chối request không có / sai token |
| Python health | `GET /health`, `GET /internal/health` | OK |

---

## 5. Danh sách việc cần làm tiếp theo (theo mức độ ưu tiên)

### P0 — Auth domain (unblock toàn bộ luồng)
- [ ] `UserRepository`: implement `Create`, `FindByEmail`, `FindByID`
- [ ] `AuthService`: hash password (`bcrypt`), query DB thật, tạo refresh token riêng
- [ ] `AuthHandler.Register`: save user vào DB
- [ ] Quyết định cơ chế lưu refresh token (DB hay stateless)

### P1 — Chat domain
- [ ] Bổ sung field thiếu vào domain `ChatSession` và `ChatMessage`
- [ ] `ChatSessionRepository`: `Create`, `FindByID`, `FindByUserID`
- [ ] `ChatMessageRepository`: `Create`, `FindBySessionID`
- [ ] `ChatService`: orchestrate tạo session, lưu message
- [ ] `ChatHandler`: implement các endpoint, wiring với DB và Python AI
- [ ] Python `POST /internal/ai/chat-stream`: implement LLM generation + streaming

### P2 — Radar / Compare / Graph domain
- [ ] Xác định schema bảng analytics (technology_stats, sentiment_data, graph_relations)
- [ ] Viết migration bổ sung
- [ ] Implement repository + service + handler cho từng domain
- [ ] Python `POST /internal/ai/llm-summary`: implement summarization

### P3 — Chất lượng
- [ ] Inject `db` từ router xuống handler/service/repository (hiện chưa được wire)
- [ ] Bổ sung field còn thiếu trong `domain/chat.go`
- [ ] Tạo DTO cho radar, compare, graph, chat request/response
- [ ] Thêm LLM/OCR library vào `requirements.txt`
- [ ] Structured logging, request ID
- [ ] Rate limiting cho chat API
