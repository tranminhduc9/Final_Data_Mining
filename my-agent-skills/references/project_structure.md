# Cấu trúc Dự án TechPulse VN

Dự án được tổ chức theo mô hình Modular Monorepo, với toàn bộ source code nằm trong thư mục `src/`.

## 🌳 Sơ đồ cây (Directory Tree)

```text
TechPulse-VN/
├── 📂 src/                          # SOURCE CODE CHÍNH
│   ├── 📂 frontend/                 # Phân hệ Frontend
│   │   ├── 📂 web/                  # Next.js 15 Web Dashboard
│   │   └── 📂 app/                  # Expo Mobile App
│   │
│   ├── 📂 backend/                  # [Blueprint] FastAPI Server
│   ├── 📂 ai-rag-core/              # [Blueprint] Graph RAG Engine
│   ├── 📂 data-pipeline/            # [Blueprint] Crawlers & ETL
│   ├── 📂 database/                 # [Blueprint] Neo4j Schema & Migrations
│   ├── 📂 shared/                   # Code & Types dùng chung
│   ├── 📂 scripts/                  # Automation scripts
│   └── 📂 docs/                     # Tài liệu kỹ thuật hệ thống
│
├── 📂 my-agent-skills/              # Kỹ năng và hướng dẫn cho AI Agent
├── 📂 tests/                        # Hệ thống kiểm thử
├── 📂 docs/                         # Tài liệu dự án cấp cao (Root level)
└── README.md                        # Tổng quan dự án
```

## 📍 Hướng dẫn điều hướng cho AI (Navigation Rules)

1. **Phát triển Web Dashboard:**
   - Hoạt động tại: `src/frontend/web/`.
   - Sử dụng Next.js 15 App Router.
   - Cài đặt thư viện: Chạy `npm install` tại đúng thư mục `src/frontend/web/`.

2. **Phát triển Mobile App:**
   - Hoạt động tại: `src/frontend/app/`.
   - Sử dụng Expo & React Native.
   - Các màn hình chính nằm trong `src/frontend/app/app/`.

3. **Hiểu biết về hệ thống:**
   - Các folder đánh dấu `[Blueprint]` hiện chỉ chứa file `__init__.py` mô tả kiến trúc.
   - Luôn đọc `__init__.py` trong từng folder để hiểu nhiệm vụ của module đó trước khi hỗ trợ.