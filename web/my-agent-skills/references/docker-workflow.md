# Quy trình khởi chạy dự án TechPulse VN

## Mô hình phát triển (Development Model)

| Layer | Công nghệ | Cách chạy |
|-------|-----------|-----------|
| **Frontend** | React 19 + Vite | `npm run dev` trong thư mục `web/` → `http://localhost:5173` |
| **Backend** | FastAPI (Python) | `docker compose up -d` từ thư mục gốc `Final_Data_Mining/` → `http://localhost:8000` |
| **Database** | Neo4j AuraDB | Cloud-hosted — kết nối qua biến môi trường trong file `.env` |
| **Production** | Docker + Nginx | Build với `Dockerfile` + `docker-compose.yml` trong `web/` |

## ⚠️ Lưu ý cho AI Agent khi viết code:

1. **Kết nối API:** Frontend (`localhost:5173`) gọi Backend qua `http://localhost:8000`. Cấu hình base URL trong các file service tại `web/src/services/`.
2. **Biến môi trường:** Thông tin kết nối Neo4j AuraDB (URI, username, password) và Gemini API Key lưu trong file `.env` ở thư mục gốc. Tuyệt đối không hardcode secrets vào code.
3. **Backend hot reload:** Thêm flag `--reload` vào lệnh `uvicorn` khi phát triển để tự động reload khi có thay đổi file.
4. **Neo4j:** Không tự ý xóa hoặc thay đổi Neo4j schema. Mọi thay đổi schema/migration phải thực hiện qua `src/database/`.
5. **Docker (production):** `web/Dockerfile` chỉ dùng để build image cho frontend production (Nginx serving). Không cần Docker để chạy dev.