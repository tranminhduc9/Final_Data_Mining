import json
import re

from langchain_google_genai import ChatGoogleGenerativeAI

from app.config import get_settings
from app.db.neo4j_client import run_query


async def _extract_entities(query: str) -> dict:
    """
    Dùng Gemini trích xuất (1 call duy nhất):
      - technologies: tên tech / framework / kỹ năng IT
      - job_titles:   từ khoá vị trí công việc (nếu câu hỏi hỏi về nghề/lương)

    Trả về dict, ví dụ:
      {"technologies": ["Python"], "job_titles": ["kỹ sư phần mềm"]}
    """
    settings = get_settings()
    llm = ChatGoogleGenerativeAI(
        model=settings.llm_model,
        google_api_key=settings.gemini_api_key,
        temperature=0,
    )

    prompt = (
        "Phân tích câu hỏi sau và trích xuất 2 loại thông tin:\n"
        "1. technologies: tên công nghệ, ngôn ngữ lập trình, framework, kỹ năng IT\n"
        "2. job_titles: từ khoá vị trí công việc IT (developer, engineer, analyst...)\n\n"
        "Chỉ trả về JSON object, không giải thích. Nếu không có thì để list rỗng.\n"
        'Ví dụ: {"technologies": ["Python", "Django"], "job_titles": ["backend developer"]}\n\n'
        f"Câu hỏi: {query}"
    )

    response = await llm.ainvoke(prompt)
    text = response.content.strip()

    match = re.search(r"\{.*?\}", text, re.DOTALL)
    if match:
        try:
            result = json.loads(match.group())
            return {
                "technologies": [e for e in result.get("technologies", []) if isinstance(e, str)],
                "job_titles":   [e for e in result.get("job_titles", []) if isinstance(e, str)],
            }
        except json.JSONDecodeError:
            pass
    return {"technologies": [], "job_titles": []}


async def graph_search(query: str) -> dict:
    """
    Trích entity từ query (1 Gemini call) → graph traversal trên Job / Company / Technology.

    Trả về dict:
    {
        "entities":     list[str],   # tech/skill trích được
        "job_titles":   list[str],   # job title keywords trích được
        "jobs":         list[dict],  # job tìm được (theo tech + theo title)
        "companies":    list[dict],  # công ty dùng các tech này
        "related_tech": list[dict],  # tech liên quan qua RELATED_TO
    }
    """
    extracted = await _extract_entities(query)
    tech_entities = extracted["technologies"]
    job_title_kws  = extracted["job_titles"]

    if not tech_entities and not job_title_kws:
        return {"entities": [], "job_titles": [], "jobs": [], "companies": [], "related_tech": []}

    names_lower  = [e.lower() for e in tech_entities]
    titles_lower = [t.lower() for t in job_title_kws]

    # --- Job theo tech/skill (REQUIRES relationship) ---
    jobs_by_tech = await run_query(
        """
        MATCH (j:Job)-[:REQUIRES]->(t)
        WHERE (t:Technology OR t:Skill) AND toLower(t.name) IN $names
        OPTIONAL MATCH (j)-[:HIRES_FOR]->(c:Company)
        WITH DISTINCT j, t, c
        RETURN
            j.title        AS title,
            j.level        AS level,
            j.salary_min   AS salary_min,
            j.salary_max   AS salary_max,
            j.posted_date  AS posted_date,
            t.name         AS technology,
            c.name         AS company,
            c.location     AS location
        ORDER BY j.posted_date DESC
        LIMIT 20
        """,
        {"names": names_lower},
    ) if names_lower else []

    # --- Job theo title keyword (CONTAINS matching) ---
    jobs_by_title = await run_query(
        """
        UNWIND $keywords AS kw
        MATCH (j:Job)
        WHERE toLower(j.title) CONTAINS kw
        OPTIONAL MATCH (j)-[:HIRES_FOR]->(c:Company)
        OPTIONAL MATCH (j)-[:REQUIRES]->(t:Technology)
        WITH DISTINCT j, c, collect(DISTINCT t.name)[..3] AS techs
        RETURN
            j.title        AS title,
            j.level        AS level,
            j.salary_min   AS salary_min,
            j.salary_max   AS salary_max,
            j.posted_date  AS posted_date,
            techs          AS technology,
            c.name         AS company,
            c.location     AS location
        ORDER BY j.posted_date DESC
        LIMIT 20
        """,
        {"keywords": titles_lower},
    ) if titles_lower else []

    # Gộp 2 nguồn, loại trùng theo title
    seen = set()
    jobs = []
    for j in jobs_by_tech + jobs_by_title:
        key = j.get("title", "")
        if key not in seen:
            seen.add(key)
            jobs.append(j)

    # Công ty đang dùng các tech này
    companies = await run_query(
        """
        MATCH (c:Company)-[:USES]->(t:Technology)
        WHERE toLower(t.name) IN $names
        RETURN DISTINCT
            c.name      AS name,
            c.industry  AS industry,
            c.location  AS location,
            c.size      AS size,
            c.rating    AS rating,
            t.name      AS technology
        LIMIT 15
        """,
        {"names": names_lower},
    )

    # Tech liên quan (RELATED_TO — 2 chiều)
    related = await run_query(
        """
        MATCH (t:Technology)-[:RELATED_TO]-(t2:Technology)
        WHERE toLower(t.name) IN $names
        RETURN DISTINCT t.name AS from_tech, t2.name AS related_tech
        LIMIT 20
        """,
        {"names": names_lower},
    )

    return {
        "entities":   tech_entities,
        "job_titles": job_title_kws,
        "jobs":       jobs,
        "companies":  companies,
        "related_tech": related,
    }
