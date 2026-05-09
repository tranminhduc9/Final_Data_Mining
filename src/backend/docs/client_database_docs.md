# Database cho App và Web

## Mô tả chung

Dữ liệu được lưu trong **PostgreSQL 18**. Dung lượng lưu trữ **1GB**.

## URL Connect

```
postgresql://backend_zzpq_user:xxxxxxxxx@dpg-d6vvsf75gffc73dj07cg-a.singapore-postgres.render.com/backend_zzpq
```

| Thành phần | Giá trị |
|------------|---------|
| Username   | `backend_zzpq_user` |
| Password   | `xxxxxxxxx` |
| Address    | `dpg-d6vvsf75gffc73dj07cg-a.singapore-postgres.render.com` |
| Database   | `backend_zzpq` |

Get the password from .env file.
---

## Mô tả Lược đồ

### TABLE: `users`

**Định nghĩa cột:**

| Attribute | Data Type | Constraints | Default Value | Mô tả |
|-----------|-----------|-------------|---------------|-------|
| `id` | UUID | PRIMARY KEY | `gen_random_uuid()` | Mã xác minh cho mỗi user |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL | — | Địa chỉ email người dùng (duy nhất) |
| `password_hash` | VARCHAR(255) | NOT NULL | — | Mã hóa password (hash) |
| `full_name` | VARCHAR(255) | NULLABLE | — | Tên user |
| `subscription_tier` | VARCHAR(50) | — | `'free'` | Gói đăng ký (free/premium/pro) |
| `created_at` | TIMESTAMPTZ | — | `CURRENT_TIMESTAMP` | Thời gian tạo tài khoản |

**Tính năng chính:**
- Tự động tạo `id` cho mỗi user
- Email phải độc nhất
- Gói đăng ký mặc định là `"free"`

---

### TABLE: `chat_session`

**Định nghĩa cột:**

| Attribute | Data Type | Constraints | Default Value | Mô tả |
|-----------|-----------|-------------|---------------|-------|
| `id` | UUID | PRIMARY KEY | `gen_random_uuid()` | Mã xác định cho mỗi tiến trình chat (session) |
| `user_id` | UUID | FOREIGN KEY → `users.id` | — | Tham chiếu tới user sở hữu tiến trình này |
| `title` | VARCHAR(255) | NULLABLE | — | Tên tiến trình |
| `model_used` | VARCHAR(100) | NULLABLE | — | Model AI sử dụng (VD: gemini-pro-3, ...) |
| `system_prompt` | TEXT | NULLABLE | — | System Prompt (Rule, Role, ...) |
| `created_at` | TIMESTAMPTZ | — | `CURRENT_TIMESTAMP` | Thời gian tạo |
| `updated_at` | TIMESTAMPTZ | NULLABLE | — | Lần cuối cập nhật |

**Chức năng chính:**
- Liên kết user tới bảng này thông qua khóa ngoại
- Theo dõi model nào được sử dụng
- Hỗ trợ system prompts
- Tiêu đề cho session
- Theo dõi thời gian tạo và thời gian thay đổi

---

### TABLE: `chat_message`

**Định nghĩa cột:**

| Attribute | Data Type | Constraints | Default Value | Mô tả |
|-----------|-----------|-------------|---------------|-------|
| `id` | UUID | PRIMARY KEY | `gen_random_uuid()` | ID cho mỗi tin nhắn |
| `session_id` | UUID | FOREIGN KEY → `chat_session.id` | — | Tham chiếu tới session chứa tin nhắn này |
| `role` | VARCHAR(50) | NOT NULL, CHECK constraint | — | Message role: `'user'`, `'assistant'`, hoặc `'system'` |
| `content` | TEXT | NOT NULL | — | Nội dung tin nhắn |
| `prompt_tokens` | INTEGER | — | `0` | Số lượng token của input |
| `completion_tokens` | INTEGER | — | `0` | Số lượng token output |
| `finish_reason` | VARCHAR(100) | NULLABLE | — | Lý do tin nhắn kết thúc (e.g., `'stop'`, `'length'`, `'content_filter'`) |
| `created_at` | TIMESTAMPTZ | — | `CURRENT_TIMESTAMP` | Thời gian tạo |

**Chức năng chính:**
- Tham chiếu tới session chứa tin nhắn này
- `role` field với CHECK constraint cho các giá trị hợp lệ
- Theo dõi token sử dụng để tính toán chi phí
- Hỗ trợ nhiều loại `finish_reason`
- Lưu trữ đầy đủ nội dung message

---

## Lược đồ mối quan hệ

```
users
  └── chat_session  (user_id → users.id)
        └── chat_message  (session_id → chat_session.id)
```

- `users` phải tạo trước
- `chat_session` phụ thuộc vào `users`
- `chat_message` phụ thuộc vào `chat_session`

**Cascade delete:**
1. Khi 1 user bị xóa → toàn bộ session của user đó tự động xóa
2. Khi 1 session bị xóa → toàn bộ tin nhắn của session đó tự động xóa

---

## Cải tiến sau này

Nâng cấp từ SQL sang NoSQL để mở rộng về sau. Một số cơ sở đang xem xét:

| Hệ thống | Ghi chú |
|----------|---------|
| **Cassandra** | Chạy trên nền Java → có Garbage Collection → hệ thống có thể bị đứng. Tài nguyên tốn kém, chi phí cao. |
| **ScyllaDB** | Tài liệu ít, chạy trên nền C (thường dùng với Go/Rust). Không có Garbage Collection → hiệu năng do mình kiểm soát. Tài nguyên tối ưu hơn, chi phí tổng thể tốt hơn. |
| **DynamoDB** | Chưa tìm hiểu sâu, có thể giống Cassandra ở một số điểm. |