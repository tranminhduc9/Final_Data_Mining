"""
📦 Module: shared
===================

🎯 Mục đích:
    Chứa code, types, constants và utilities dùng chung giữa các module
    Python trong monorepo (backend, data-pipeline, ai-rag-core, database).
    Đảm bảo DRY (Don't Repeat Yourself) và consistency toàn dự án.

📋 Chức năng chính:
    1. Utils (utils/):
       - logger.py: Cấu hình logging thống nhất (format, level, output)
       - text_utils.py: Hàm xử lý text dùng chung (normalize Vietnamese,
         remove HTML, truncate, slugify)
       - date_utils.py: Xử lý datetime, timezone (UTC ↔ Asia/Ho_Chi_Minh)
       - validators.py: Validation functions dùng chung

    2. Types (types/):
       - Pydantic BaseModels dùng chung giữa các module
       - Enums: SentimentType, NodeType, SourcePlatform, JobLevel
       - Type aliases cho Neo4j responses

    3. Constants (constants/):
       - Neo4j labels, relationship types (đồng bộ với database/schemas/)
       - API error codes, HTTP status mappings
       - Config defaults (timeout, retry count, batch size)
       - Platform URLs, regex patterns

    4. Exceptions (exceptions/):
       - Custom exception classes dùng chung
       - Neo4jConnectionError, GeminiAPIError, CrawlerBlockedError
       - Structured error response format

🔧 Cách sử dụng:
    from shared.utils.logger import get_logger
    from shared.types.enums import SentimentType
    from shared.constants.neo4j import NODE_LABELS

👤 Owner: Leader / PM + All members (contribute shared code)
"""
