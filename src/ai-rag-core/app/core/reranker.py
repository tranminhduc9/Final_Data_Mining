from functools import lru_cache
from typing import Any

from app.config import get_settings


@lru_cache(maxsize=1)
def get_reranker() -> Any:
    """Load CrossEncoder một lần duy nhất, cache lại cho các lần gọi sau."""
    from sentence_transformers import CrossEncoder

    settings = get_settings()
    return CrossEncoder(settings.reranker_model)


RERANK_SCORE_THRESHOLD = 0.40


def rerank(query: str, candidates: list[dict], top_k: int = 5) -> list[dict]:
    """
    Nhận query + danh sách candidate article từ vector search,
    trả về top_k article được rerank lại theo relevance score thực sự.

    Chỉ giữ lại các article có rerank_score >= RERANK_SCORE_THRESHOLD (0.40)
    để tránh đưa bài không liên quan vào prompt.

    candidates: list[dict] với keys: id, title, content, source, published_date, sentiment_score, score
    Trả về: list[dict] tương tự, thêm key `rerank_score`, sắp xếp giảm dần.
    """
    if not candidates:
        return []

    model = get_reranker()

    pairs = [
        (query, _build_passage(c))
        for c in candidates
    ]

    scores = model.predict(pairs)

    for candidate, score in zip(candidates, scores):
        candidate["rerank_score"] = float(score)

    reranked = sorted(candidates, key=lambda x: x["rerank_score"], reverse=True)

    filtered = [a for a in reranked if a["rerank_score"] >= RERANK_SCORE_THRESHOLD]
    return filtered[:top_k]


def _build_passage(candidate: dict, max_chars: int = 1000) -> str:
    """Ghép title + content thành passage để cho reranker chấm điểm."""
    title   = (candidate.get("title") or "").strip()
    content = (candidate.get("content") or "").strip()
    passage = f"{title} {content}".strip()
    return passage[:max_chars]
