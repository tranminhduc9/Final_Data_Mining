# Quy trình làm việc với Docker

Trong giai đoạn hiện tại, Docker chủ yếu được sử dụng để đóng gói và triển khai phân hệ **Web Dashboard**.

## 🏗️ Cấu hình Docker hiện có

1. **Web Dashboard Docker:**
   - **Vị trí**: `src/frontend/web/Dockerfile`
   - **Cơ chế**: Build project Next.js và phục vụ thông qua Nginx.
   - **Compose**: `src/frontend/web/docker-compose.yml`

2. **Các thành phần khác**:
   - Hiện chưa có Dockerfile cho các module Backend/AI vì đang ở giai đoạn thiết kế.

## ⚠️ Lưu ý cho AI Agent:

1. **Phát triển Local**: Luôn ưu tiên dùng `npm run dev` tại `src/frontend/web` hoặc `src/frontend/app` để tận dụng Hot-Reload. Chỉ dùng Docker khi cần kiểm tra việc đóng gói (build production).
2. **Path Context**: Khi chạy lệnh Docker, hãy đảm bảo `cd` vào đúng thư mục chứa `Dockerfile`.
3. **Môi trường**: Kiểm tra các biến môi trường trong `.env` của từng phân hệ trước khi khởi chạy Docker.