# Quy chuẩn viết code (Coding Convention)

## 1. Backend (FastAPI - Python)
- **Vị trí code:** Làm việc trong `src/backend/` theo mô hình Clean Architecture: `api/` (routes), `services/` (business logic), `models/` (data schema).
- **Database:** Neo4j AuraDB — sử dụng Cypher queries. Schema và migrations nằm trong `src/database/`.
- **AI / RAG:** Logic RAG (Graph RAG, Vector Search, Gemini Prompts) nằm trong `src/ai-rag-core/`.
- **Data Pipeline:** Crawlers, ETL, NLP nằm trong `src/data-pipeline/`.
- **Quản lý package:** Chỉ sử dụng `uv add <package>`, tuyệt đối không dùng `pip` trực tiếp hoặc `conda`.

## 2. Frontend (React 19 + Vite)
- **Vị trí code:** Làm việc trong `web/src/`. Chạy dev server bằng `npm run dev` trong thư mục `web/`.
- **Component:** Bắt buộc viết Functional Component và sử dụng Hooks.
- **Styling:** Sử dụng CSS thuần (file riêng trong `web/src/styles/`), không sử dụng Tailwind CSS.
- **Giao tiếp API:** Phải tạo các file service riêng trong `web/src/services/` để gọi API bằng `fetch` native (dự án không dùng axios). Không gọi API trực tiếp trong UI Component.
- **Router:** Đăng ký tất cả routes trong `web/src/App.jsx` (dùng `react-router-dom`).
- **Thư viện visualisation:** D3.js, Recharts, react-force-graph-2d đã được cài sẵn — dùng cho biểu đồ và Knowledge Graph.
- **Quản lý package:** Dùng `npm install <package>` trong thư mục `web/`.