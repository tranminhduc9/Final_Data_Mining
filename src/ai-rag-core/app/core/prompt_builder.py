from pathlib import Path

_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"


def _load(filename: str) -> str:
    return (_PROMPTS_DIR / filename).read_text(encoding="utf-8").strip()


def build_messages(
    query: str,
    articles: list[dict],
    graph_data: dict | None = None,
    user_block: str = "",
) -> list[dict]:
    """
    Ghép context từ article + graph data + user profile thành messages cho LangChain / Gemini.

    articles:   list[dict] — top-5 article sau rerank
    graph_data: dict       — kết quả từ graph_search() (jobs, companies, related_tech)
    user_block: str        — output của retriever_user.build_user_block() (rỗng nếu anonymous)
    Trả về: [{"role": "system", ...}, {"role": "user", ...}]
    """
    context_block     = _build_context_block(articles)
    job_context_block = _build_job_context_block(graph_data or {})

    rag_template = _load("rag_template.txt")
    user_content = rag_template.format(
        context=context_block,
        job_context=job_context_block,
        user_block=user_block,
        query=query,
    )

    return [
        {"role": "system", "content": _load("system_prompt.txt")},
        {"role": "user",   "content": user_content},
    ]


def _build_context_block(articles: list[dict]) -> str:
    """Định dạng article thành block đánh số [1], [2], ... cho LLM trích dẫn."""
    if not articles:
        return "(Không có bài viết liên quan nào được tìm thấy.)"

    blocks = []
    for i, article in enumerate(articles, start=1):
        title   = article.get("title") or "Không có tiêu đề"
        content = article.get("content") or ""
        date    = article.get("published_date") or ""

        if len(content) > 800:
            content = content[:800] + "..."

        date_str = f" ({str(date)[:10]})" if date else ""
        blocks.append(f"[{i}] {title}{date_str}\n{content}")

    return "\n\n".join(blocks)


def _build_job_context_block(graph_data: dict) -> str:
    """Định dạng dữ liệu tuyển dụng từ graph_search() thành text cho prompt."""
    jobs         = graph_data.get("jobs", [])
    companies    = graph_data.get("companies", [])
    related_tech = graph_data.get("related_tech", [])

    if not jobs and not companies and not related_tech:
        return "(Không có dữ liệu tuyển dụng liên quan.)"

    parts = []

    if jobs:
        parts.append("Tin tuyển dụng:")
        for j in jobs:
            title    = j.get("title") or "N/A"
            level    = j.get("level") or ""
            tech     = j.get("technology") or ""
            company  = j.get("company") or "N/A"
            location = j.get("location") or ""
            sal_min  = j.get("salary_min")
            sal_max  = j.get("salary_max")

            salary_str = ""
            if sal_min and sal_max:
                salary_str = f", lương {sal_min:,}–{sal_max:,} USD"
            elif sal_min:
                salary_str = f", lương từ {sal_min:,} USD"

            level_str    = f" [{level}]" if level else ""
            tech_str     = f" (yêu cầu {tech})" if tech else ""
            location_str = f", {location}" if location else ""
            parts.append(
                f"  - {title}{level_str}{tech_str} tại {company}{location_str}{salary_str}"
            )

    if companies:
        parts.append("\nCông ty đang dùng:")
        for c in companies:
            name     = c.get("name") or "N/A"
            tech     = c.get("technology") or ""
            industry = c.get("industry") or ""
            location = c.get("location") or ""
            size     = c.get("size") or ""
            rating   = c.get("rating")

            meta = ", ".join(filter(None, [industry, location, size]))
            rating_str = f", rating {rating}" if rating else ""
            tech_str   = f" (dùng {tech})" if tech else ""
            parts.append(f"  - {name}{tech_str}: {meta}{rating_str}")

    if related_tech:
        techs = list({r["related_tech"] for r in related_tech})
        parts.append(f"\nCông nghệ liên quan: {', '.join(techs)}")

    return "\n".join(parts)
