# 🚀 TechPulse VN

**Nền tảng Intelligence Phân tích Xu hướng Công nghệ & Thị trường Tuyển dụng IT**

> Giải pháp Knowledge Hub tự động hóa, sử dụng **Graph RAG** (Neo4j + Vector Search + Gemini 1.5 Pro) để thu thập, phân tích và trả lời câu hỏi về xu hướng công nghệ, thị trường tuyển dụng IT Việt Nam.

---

## 📋 Mục lục

- [Tổng quan](#-tổng-quan)
- [Kiến trúc hệ thống](#-kiến-trúc-hệ-thống)
- [Tech Stack](#-tech-stack)
- [Cấu trúc dự án](#-cấu-trúc-dự-án)
- [Phân công nhân sự](#-phân-công-nhân-sự)
- [Hướng dẫn cài đặt](#-hướng-dẫn-cài-đặt)

---

## 🎯 Tổng quan

**Vấn đề:** Thông tin ngành IT (bài viết, tin tuyển dụng, review) đang bị phân mảnh trên nhiều nền tảng (Viblo, TopDev, Reddit). Chatbot AI truyền thống dễ bị hallucination và thiếu khả năng suy luận chéo giữa các thực thể.

**Giải pháp:** Xây dựng luồng **DataOps** khép kín:

```
Ingestion (Crawl) → Pre-processing (ETL) → AI Enrichment (NER, Sentiment) → Knowledge Graph → Graph RAG Chatbot
```



## 📁 Cấu trúc dự án

```
TechPulse-VN/
├── 📂 src/                          # Source code chính
│   ├── 📂 backend/                  # FastAPI server (Clean Architecture)
│   │   └── __init__.py              # Mô tả module: API, Services, Models, Middleware
│   │
│   ├── 📂 frontend/                 # Next.js 15 Web App
│   │   └── __init__.py              # Mô tả module: Chat, Dashboard, Graph Viewer
│   │
│   ├── 📂 data-pipeline/            # Thu thập & xử lý dữ liệu
│   │   └── __init__.py              # Mô tả module: Crawlers, ETL, NLP Processors
│   │
│   ├── 📂 ai-rag-core/              # Lõi AI — Graph RAG Engine
│   │   └── __init__.py              # Mô tả module: RAG, Prompts, Chains, Embeddings
│   │
│   ├── 📂 database/                 # Neo4j schema, queries, migrations
│   │   └── __init__.py              # Mô tả module: Schemas, Cypher, Migrations, Seeds
│   │
│   ├── 📂 shared/                   # Code/types/utils dùng chung
│   │   └── __init__.py              # Mô tả module: Utils, Types, Constants, Exceptions
│   │
│   ├── 📂 scripts/                  # Utility scripts (seed, migrate, health check)
│   │   └── __init__.py              # Mô tả module: DB management, automation tools
│   │
│   └── 📂 docs/                     # Tài liệu kỹ thuật (API, Architecture, Guides)
│       └── __init__.py              # Mô tả module: API docs, diagrams, guides
│
├── 📂 docs/                         # Tài liệu dự án root-level
│   └── __init__.py                  # Mô tả module docs
│
├── 📂 tests/                        # Integration, E2E, Performance tests
│   └── __init__.py                  # Mô tả module: Integration, E2E, Data Quality
│
├── 📂 PROMPT/                       # Prompt files cho AI (gitignored)
│
├── .gitignore
└── README.md                        # ← Bạn đang đọc file này
```

> 💡 **Mỗi module đều có file `__init__.py`** mô tả chi tiết: mục đích, chức năng chính, tech stack, cách chạy, và owner.

---

## 👥 Phân công nhân sự

| # | Vai trò | Module chính | Nhiệm vụ |
|---|---------|-------------|-----------|
| 🎯 | **Leader / PM / Architect** | Toàn bộ | Phân tích nghiệp vụ, thiết kế Graph Schema, quản lý Git Flow, review PR |
| 1 | Data Engineer | `src/data-pipeline/` | Crawler (Scrapy/Selenium), ETL, NER, Cronjob |
| 2 | DB & DevOps Engineer | `src/database/` + `src/scripts/` | Neo4j AuraDB, Cypher queries, Vector Index, Cloud setup |
| 3 | AI Engineer | `src/ai-rag-core/` | Graph RAG, Vector + Graph Search, Prompt Engineering |
| 4 | Backend Developer | `src/backend/` | FastAPI, Auth, Rate Limiting, Streaming SSE |
| 5 | Frontend Developer | `src/frontend/` | Next.js UI, Knowledge Graph viz, Chatbot UX |
| 6 | QC / Tester | `tests/` | Test Functional, API, Data Quality, Performance |

---
