import asyncio
from typing import AsyncIterator

from app.core.retriever import vector_search
from app.core.retriever_graph import graph_search
from app.core.retriever_user import get_user_context, build_user_block
from app.core.reranker import rerank
from app.core.prompt_builder import build_messages
from app.core.generator_stream import generate_stream


_FALLBACK_ANSWER = "Tôi không tìm thấy thông tin liên quan trong dữ liệu hiện có."


async def answer_stream(query: str, user_id: str | None = None) -> AsyncIterator[dict]:
    """
    Streaming version của pipeline.answer().
    Yield dict với 2 loại event:
      - {"event": "token", "data": <str chunk>}
      - {"event": "done",  "data": {"answer", "sources", "entities", "job_titles"}}
    """
    # 1. Chạy song song: vector search + graph traversal + user profile
    gather_tasks = [
        vector_search(query, top_k=20),
        graph_search(query),
    ]
    if user_id:
        gather_tasks.append(get_user_context(user_id))
        candidates, graph_data, user_ctx = await asyncio.gather(*gather_tasks)
    else:
        candidates, graph_data = await asyncio.gather(*gather_tasks)
        user_ctx = None

    # 2. Rerank
    top_articles = rerank(query, candidates, top_k=5) if candidates else []

    # 3. Fallback: không có data nào
    if not top_articles and not graph_data.get("jobs") and not graph_data.get("companies"):
        yield {"event": "token", "data": _FALLBACK_ANSWER}
        yield {
            "event": "done",
            "data": {
                "answer":     _FALLBACK_ANSWER,
                "sources":    [],
                "entities":   graph_data.get("entities", []),
                "job_titles": graph_data.get("job_titles", []),
            },
        }
        return

    # 4. Build prompt
    user_blk = build_user_block(user_ctx) if user_ctx else ""
    messages = build_messages(query, top_articles, graph_data, user_block=user_blk)

    # 5. Stream Gemini
    chunks: list[str] = []
    async for chunk in generate_stream(messages):
        chunks.append(chunk)
        yield {"event": "token", "data": chunk}

    full_answer = "".join(chunks)
    yield {
        "event": "done",
        "data": {
            "answer":     full_answer,
            "sources":    top_articles,
            "entities":   graph_data.get("entities", []),
            "job_titles": graph_data.get("job_titles", []),
        },
    }
