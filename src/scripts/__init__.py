"""
📦 Module: scripts
===================

🎯 Mục đích:
    Chứa các utility scripts dùng chung cho toàn dự án — database management,
    data seeding, migration, health checks, và các automation tools.

📋 Chức năng chính:
    1. seed_database.py    — Database Seeding:
       - Tạo initial data cho Neo4j (sample technologies, companies, jobs)
       - Tạo constraints và indexes
       - Hữu ích cho development và testing
    2. migrate.py          — Database Migration:
       - Schema migration scripts cho Neo4j
       - Version tracking cho migrations
       - Rollback support
    3. health_check.py     — Health Check Script:
       - Kiểm tra kết nối Neo4j
       - Kiểm tra Gemini API availability
       - Kiểm tra crawler endpoints
       - Dùng trong CI/CD pipeline
    4. generate_types.py   — TypeScript Type Generation:
       - Generate TypeScript types từ OpenAPI spec
       - Đồng bộ types giữa backend và frontend
    5. export_data.py      — Data Export:
       - Export data từ Neo4j ra CSV/JSON
       - Backup utility

🔧 Cách chạy:
    - make seed      → python scripts/seed_database.py
    - make migrate   → python scripts/migrate.py
    - make health    → python scripts/health_check.py

👤 Owner: DB / DevOps + Leader / PM
"""
