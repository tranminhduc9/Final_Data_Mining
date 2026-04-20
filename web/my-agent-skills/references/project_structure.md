# Cấu trúc Dự án (Project Structure)

Dự án này là **TechPulse VN** — nền tảng Graph RAG phân tích xu hướng công nghệ IT (Neo4j + FastAPI + React/Vite + Expo + Gemini 1.5 Pro). Dưới đây là sơ đồ thư mục và hướng dẫn định vị code dành cho AI Agent.

## 🌳 Sơ đồ cây (Directory Tree)

```
Final_Data_Mining/                  # Thư mục gốc của dự án
├── src/                            # Source code Python (backend monorepo)
│   ├── backend/                    # FastAPI server — Clean Architecture
│   │   └── __init__.py             # API routes, Services, Models, Middleware
│   ├── data-pipeline/              # Thu thập & xử lý dữ liệu (Crawlers, ETL, NLP)
│   ├── ai-rag-core/                # Lõi AI — Graph RAG Engine (Chains, Embeddings, Prompts)
│   ├── database/                   # Neo4j Schema, Cypher queries, Migrations, Seeds
│   ├── shared/                     # Utils, Types, Constants, Exceptions dùng chung
│   ├── scripts/                    # Utility scripts (seed, migrate, health check)
│   └── docs/                       # Tài liệu kỹ thuật nội bộ (API, Architecture)
│
├── web/                            # Frontend Web — React 19 + Vite (chạy npm run dev)
│   ├── src/                        # THƯ MỤC LÀM VIỆC CHÍNH CỦA WEB FRONTEND
│   │   ├── components/             # [Thêm file ở đây] UI Component dùng chung
│   │   ├── pages/                  # [Thêm file ở đây] Các màn hình / view chính
│   │   ├── services/               # [Thêm file ở đây] Gọi API bằng fetch native
│   │   ├── styles/                 # CSS thuần cho từng trang / component
│   │   ├── data/                   # Dữ liệu tĩnh / mock data
│   │   ├── App.jsx                 # Cấu hình Router chính
│   │   └── main.jsx                # Entry point React
│   ├── public/                     # Static assets (favicon, robots.txt…)
│   ├── my-agent-skills/            # ← Thư mục kỹ năng và hướng dẫn cho AI Agent (file này!)
│   ├── package.json                # Thư viện: React, Vite, D3, Recharts, react-force-graph-2d…
│   ├── vite.config.js              # Cấu hình Vite
│   └── Dockerfile / nginx.conf     # Cấu hình production container
│
├── app/                            # Mobile App — React Native + Expo (chạy expo start)
│   ├── app/                        # THƯ MỤC LÀM VIỆC CHÍNH CỦA MOBILE APP
│   │   ├── (tabs)/                 # Màn hình tab navigation
│   │   │   ├── index.tsx           # Tab Trang chủ / Dashboard
│   │   │   ├── chat.tsx            # Tab Chatbot (Graph RAG)
│   │   │   ├── compare.tsx         # Tab So sánh công nghệ
│   │   │   └── graph.tsx           # Tab Knowledge Graph visualisation
│   │   └── _layout.tsx             # Layout gốc của app
│   ├── components/                 # UI Component dùng chung cho mobile
│   ├── services/                   # Gọi API bằng fetch (chatMock.js…)
│   ├── constants/                  # Hằng số, màu sắc, config
│   ├── hooks/                      # Custom React hooks
│   ├── assets/                     # Hình ảnh, font, icon
│   ├── data/                       # Dữ liệu tĩnh / mock data
│   └── package.json                # Thư viện: expo, react-native, expo-router…
│
├── docs/                           # Tài liệu dự án root-level
├── tests/                          # Integration, E2E, Performance tests
└── README.md
```

## 📍 Hướng dẫn điều hướng cho AI (Navigation Rules)

1. **Khi được yêu cầu "Tạo tính năng Web UI mới":**
   - Luồng: `web/src/services/` (API call) → `web/src/pages/` (màn hình) → `web/src/components/` (component) → `web/src/styles/` (CSS).
   - Đăng ký route mới trong `web/src/App.jsx`.

2. **Khi được yêu cầu "Tạo tính năng Mobile mới":**
   - Luồng: `app/services/` (API call) → `app/app/(tabs)/` (tab screen) → `app/components/` (component).
   - Đăng ký tab mới trong `app/app/(tabs)/_layout.tsx`.

3. **Khi được yêu cầu "Tạo tính năng Backend mới":**
   - Làm việc trong `src/backend/` theo Clean Architecture.
   - Luồng chuẩn: `models/` (schema) → `services/` (business logic) → `api/` (routes/endpoints).

4. **Khi được yêu cầu "Thêm dữ liệu hoặc crawler":**
   - Làm việc trong `src/data-pipeline/` (crawler, ETL, NLP).
   - Kết quả đưa vào `src/database/` (Neo4j Cypher/schema).

5. **Khi được yêu cầu "Cải thiện AI / RAG":**
   - Làm việc trong `src/ai-rag-core/` (Graph RAG chains, Gemini prompts, Vector search).

6. **Quản lý Package:**
   - Python: dùng `uv add <package>` (không dùng `pip` hay `conda`).
   - Web (React/Vite): dùng `npm install <package>` trong thư mục `web/`.
   - Mobile (Expo): dùng `npx expo install <package>` trong thư mục `app/`.

