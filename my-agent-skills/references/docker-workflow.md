# Quy trình làm việc với Docker

Dự án này là dự án thuần Frontend. Thư mục `web/` có cung cấp cấu hình `Dockerfile` và `docker-compose.yml` để build và chạy ứng dụng web qua Nginx (dành cho môi trường staging/production). Không hề có container cho Backend hay Database cục bộ.

## ⚠️ Lưu ý cho AI Agent khi sử dụng Docker:
1. **Mục đích sử dụng:** Docker trong dự án này chỉ nhằm mục đích dựng static files và phục vụ bằng Web Server tĩnh (Nginx) cho thư mục `/web`.
2. **Quá trình Development:** Khi phát triển, tuyệt đối khuyên người dùng hoặc trực tiếp dùng `npm run dev` ở thư mục local thay vì dùng Docker để giữ được tính năng Hot-Reloading của Vite.
3. **Tuyệt đối bỏ qua Backend:** Không đề xuất các cấu hình port database hay cài đặt backend Python trong container.