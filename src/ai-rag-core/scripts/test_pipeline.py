"""
Test nhanh pipeline.answer() end-to-end trên local Neo4j.

Cách chạy:
    cd src/ai-rag-core
    set -a && source ../../.env && set +a
    USE_LOCAL_NEO4J=true python3 -m scripts.test_pipeline
"""

import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.pipeline import answer
from app.db.neo4j_client import close_driver

TEST_QUERIES = [
    "Lương kỹ sư phần mềm ở Việt Nam hiện tại ra sao?",
]


async def main():
    print("=" * 60)
    print("TEST PIPELINE RAG — local Neo4j")
    print("=" * 60)

    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"\n[Câu {i}] {query}")
        print("-" * 60)

        t0 = time.time()
        result = await answer(query)
        elapsed = time.time() - t0

        print(f"Thời gian: {elapsed:.2f}s")
        entities   = result.get("entities", [])
        job_titles = result.get("job_titles", [])
        if entities:
            print(f"Tech entities: {entities}")
        if job_titles:
            print(f"Job titles:    {job_titles}")

        print(f"\nCâu trả lời:\n{result['answer']}")

        print(f"\nNguồn ({len(result['sources'])} bài):")
        for j, src in enumerate(result["sources"], 1):
            score = src.get("rerank_score", 0)
            title = src.get("title", "N/A")
            date  = str(src.get("published_date", ""))[:10]
            print(f"  [{j}] (score={score:.3f}) {title} — {date}")

        print("=" * 60)

    await close_driver()


if __name__ == "__main__":
    asyncio.run(main())
