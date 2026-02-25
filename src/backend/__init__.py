"""
📦 Module: backend
===================

🎯 Mục đích:
    Backend API server chính của TechPulse VN, xây dựng trên FastAPI (Python 3.11+),
    tuân thủ Clean Architecture. Cung cấp RESTful API chuẩn Swagger cho Frontend
    và các dịch vụ bên ngoài.

📋 Chức năng chính:
    1. API Layer (app/api/):
       - Chat API: Endpoint Chatbot Graph RAG (SSE Streaming Response)
       - Search API: Tìm kiếm xu hướng công nghệ, việc làm, công ty
       - Health API: Health check cho monitoring & CI/CD
       - Auth API: Xác thực người dùng (JWT)

    2. Core Layer (app/core/):
       - Config: Quản lý biến môi trường (.env) tập trung
       - Security: JWT token, hashing, CORS policy
       - Dependencies: Dependency Injection (Neo4j driver, Gemini client)

    3. Service Layer (app/services/):
       - ChatService: Xử lý logic chatbot, gọi AI RAG Core
       - SearchService: Xử lý logic tìm kiếm (Vector + Graph)
       - AnalyticsService: Thống kê xu hướng, sentiment aggregation

    4. Model Layer (app/models/):
       - Pydantic schemas cho Request/Response validation
       - DTO (Data Transfer Objects) cho communication giữa layers

    5. Middleware Layer (app/middleware/):
       - Rate Limiting: Chống spam API
       - Error Handling: Global exception handler, structured error responses
       - Logging: Request/Response logging

🛠️ Tech Stack:
    - FastAPI + Uvicorn (ASGI server)
    - Pydantic v2 (validation)
    - SSE (Server-Sent Events) cho Streaming Response
    - python-jose (JWT)

🚀 Deploy: Render Free Tier (US-East) — Có chiến lược chống Cold Start

🔧 Cách chạy:
    - cd backend && uvicorn app.main:app --reload --port 8000
    - Hoặc: make dev-backend

👤 Owner: Backend Developer (BE)
"""
