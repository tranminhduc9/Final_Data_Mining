"""
📦 Module: ai-rag-core
=======================

🎯 Mục đích:
    Lõi trí tuệ nhân tạo của TechPulse VN — triển khai Graph RAG
    (Retrieval-Augmented Generation kết hợp Knowledge Graph).
    Kết hợp Vector Search (ngữ nghĩa) và Graph Traversal (Cypher)
    để cung cấp ngữ cảnh chính xác cho LLM, giảm thiểu hallucination.

📋 Chức năng chính:
    1. RAG Engine (rag/):
       - GraphRAGRetriever: Retriever chính, kết hợp 2 nguồn:
         • Vector Search: Tìm kiếm theo embedding similarity (cosine)
         • Graph Traversal: Truy vết quan hệ giữa entities qua Cypher queries
       - ContextBuilder: Tổng hợp kết quả từ cả 2 nguồn thành context string
       - ResponseGenerator: Gọi LLM (Gemini 1.5 Pro) với context để sinh câu trả lời
       - StreamingHandler: Xử lý Server-Sent Events cho streaming response

    2. Prompt Engineering (prompts/):
       - System Prompts: Định nghĩa persona, rules cho chatbot
       - Chain-of-Thought (CoT): Prompt suy luận từng bước
       - ReAct Prompts: Reasoning + Acting pattern
       - Few-shot Examples: Ví dụ mẫu cho các loại câu hỏi

    3. Chains & Agents (chains/):
       - LangChain chains cho các luồng xử lý phức tạp
       - DSPy modules cho prompt optimization tự động
       - Query Router: Phân loại câu hỏi → chọn strategy phù hợp
         (factual → Graph, opinion → Vector, complex → Hybrid)

    4. Embeddings (embeddings/):
       - Embedding generator (Gemini Embedding API)
       - Batch embedding cho dữ liệu mới từ Data Pipeline
       - Vector index management (Neo4j Vector Index)

🛠️ Tech Stack:
    - LangChain (orchestration framework)
    - DSPy (prompt optimization)
    - Google Gemini 1.5 Pro (LLM + Embedding)
    - Neo4j Python Driver (graph queries)

🔧 Cách chạy:
    - Test RAG:    python -m ai-rag-core.rag.test_retriever
    - Benchmark:   python -m ai-rag-core.rag.benchmark

👤 Owner: AI Engineer (RAG Core)
"""
