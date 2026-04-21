# Report 1

## Những phần đã triển khai

### 1. Setup backend microservices
- Tách kiến trúc theo hướng:
  - Golang: public API, business logic, PostgreSQL
  - Python: AI service nội bộ
- Đã chuẩn hóa lại tài liệu kiến trúc backend.

### 2. Khởi tạo project chạy được
- Dựng khung cho Golang API service
- Dựng khung cho Python AI service
- Thêm Dockerfile và docker-compose để chạy 2 service
- Kết nối env với PostgreSQL connection string

### 3. Kết nối database
- Đã setup phần đọc biến môi trường từ file env
- Đã kiểm tra kết nối PostgreSQL thành công
- Health check của Go service trả về trạng thái database connected

### 4. Routing API scaffold
- Đã mount toàn bộ route rỗng theo tài liệu API:
  - radar
  - compare
  - graph
  - auth
  - chat
- Các route hiện trả scaffold response, chưa có business logic thật

### 5. Auth scaffold + JWT middleware
- Đã tạo auth DTO cho:
  - register
  - login
  - refresh
  - me
- Đã thêm JWT middleware để bảo vệ route
- Đã bảo vệ các route cần auth như:
  - auth/me
  - auth/logout
  - chat/*
- Đã test flow login nhận token và gọi `me` thành công

## Trạng thái hiện tại
Backend đã có nền tảng để tiếp tục triển khai logic thật cho auth, chat và các module nghiệp vụ khác.
