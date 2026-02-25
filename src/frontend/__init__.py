"""
📦 Module: frontend
===================

🎯 Mục đích:
    Web Application (Client-side) của TechPulse VN, xây dựng trên Next.js 15
    (App Router, TypeScript, Tailwind CSS). Cung cấp giao diện người dùng
    cho Chatbot AI, Dashboard xu hướng, và Knowledge Graph visualization.

📋 Chức năng chính:
    1. Chatbot Interface (app/chat/):
       - Giao diện chat AI mượt mà với Streaming Response (SSE)
       - Hiển thị câu trả lời Markdown, code block, bảng biểu
       - Lịch sử hội thoại

    2. Dashboard (app/dashboard/):
       - Biểu đồ xu hướng công nghệ theo thời gian
       - Top skills, top companies, salary insights
       - Sentiment analysis visualization

    3. Knowledge Graph Viewer (app/graph/):
       - Sử dụng react-force-graph hiển thị mạng lưới tri thức
       - Interactive: zoom, click node để xem chi tiết
       - Filter theo loại node (Technology, Company, Job, Skill)

    4. Search Page (app/search/):
       - Tìm kiếm tự nhiên (semantic search)
       - Gợi ý kết quả thông minh
       - Bộ lọc nâng cao (theo nguồn, thời gian, sentiment)

    5. Shared Components (components/):
       - UI Components tái sử dụng (Button, Card, Modal, Chart)
       - Layout components (Sidebar, Navbar, Footer)

🛠️ Tech Stack:
    - Next.js 15 (App Router + Server Components)
    - TypeScript
    - Tailwind CSS
    - react-force-graph (Knowledge Graph)
    - Recharts / Chart.js (Dashboard)

🚀 Deploy: Vercel (Free Tier, auto-deploy từ GitHub)

🔧 Cách chạy:
    - cd frontend && pnpm install && pnpm dev
    - Hoặc: make dev-frontend

👤 Owner: Frontend Developer (FE)
"""
