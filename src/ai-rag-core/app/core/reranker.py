from functools import lru_cache

from sentence_transformers import CrossEncoder

from app.config import get_settings


@lru_cache(maxsize=1)
def get_reranker() -> CrossEncoder:
    """Load CrossEncoder một lần duy nhất, cache lại cho các lần gọi sau."""
    settings = get_settings()
    return CrossEncoder(settings.reranker_model)


def rerank(query: str, candidates: list[dict], top_k: int = 5) -> list[dict]:
    """
    Nhận query + danh sách candidate article từ vector search,
    trả về top_k article được rerank lại theo relevance score thực sự.

    candidates: list[dict] với keys: id, title, content, source, published_date, sentiment_score, score
    Trả về: list[dict] tương tự, thêm key `rerank_score`, sắp xếp giảm dần.
    """
    if not candidates:
        return []

    model = get_reranker()

    # CrossEncoder nhận cặp (query, passage) — dùng title + content làm passage
    pairs = [
        (query, _build_passage(c))
        for c in candidates
    ]

    scores = model.predict(pairs)

    for candidate, score in zip(candidates, scores):
        candidate["rerank_score"] = float(score)

    reranked = sorted(candidates, key=lambda x: x["rerank_score"], reverse=True)
    return reranked[:top_k]


def _build_passage(candidate: dict, max_chars: int = 1000) -> str:
    """Ghép title + content thành passage để cho reranker chấm điểm."""
    title   = (candidate.get("title") or "").strip()
    content = (candidate.get("content") or "").strip()
    passage = f"{title} {content}".strip()
    return passage[:max_chars]
