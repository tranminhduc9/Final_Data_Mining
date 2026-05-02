import pytest
from unittest.mock import AsyncMock, MagicMock
from app.core.retriever_graph import graph_search, _extract_entities # type: ignore # noqa

@pytest.mark.asyncio
async def test_extract_entities_success(monkeypatch):
    """Kiểm tra trích xuất thực thể thành công từ Gemini."""
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(return_value=MagicMock(content='{"technologies": ["Python", "Neo4j"], "job_titles": ["Data Engineer"]}'))
    
    # Mock ChatGoogleGenerativeAI class
    monkeypatch.setattr("app.core.retriever_graph.ChatGoogleGenerativeAI", lambda **kwargs: mock_llm)
    
    result = await _extract_entities("Tìm việc Data Engineer lương cao với Python và Neo4j")
    
    assert result["technologies"] == ["Python", "Neo4j"]
    assert result["job_titles"] == ["Data Engineer"]

@pytest.mark.asyncio
async def test_extract_entities_malformed_json(monkeypatch):
    """Kiểm tra xử lý khi Gemini trả JSON sai định dạng."""
    mock_llm = MagicMock()
    mock_llm.ainvoke = AsyncMock(return_value=MagicMock(content='Đây không phải JSON { "tech": ["Python" }'))
    monkeypatch.setattr("app.core.retriever_graph.ChatGoogleGenerativeAI", lambda **kwargs: mock_llm)
    
    result = await _extract_entities("Query rác")
    
    assert result["technologies"] == []
    assert result["job_titles"] == []

@pytest.mark.asyncio
async def test_graph_search_orchestration(monkeypatch):
    """Kiểm tra luồng phối hợp trong graph_search (mock entity extraction & run_query)."""
    # 1. Mock _extract_entities
    mock_extract = AsyncMock(return_value={"technologies": ["Python"], "job_titles": ["Dev"]})
    monkeypatch.setattr("app.core.retriever_graph._extract_entities", mock_extract)
    
    # 2. Mock run_query
    mock_run_query = AsyncMock(return_value=[{"title": "Python Dev", "company": "ABC"}])
    monkeypatch.setattr("app.core.retriever_graph.run_query", mock_run_query)
    
    result = await graph_search("Python Dev")
    
    assert result["entities"] == ["Python"]
    assert len(result["jobs"]) > 0
    assert result["jobs"][0]["title"] == "Python Dev"
    assert mock_run_query.call_count >= 1

@pytest.mark.asyncio
async def test_graph_search_no_entities(monkeypatch):
    """Kiểm tra khi không trích xuất được thực thể nào."""
    monkeypatch.setattr("app.core.retriever_graph._extract_entities", AsyncMock(return_value={"technologies": [], "job_titles": []}))
    
    result = await graph_search("Câu hỏi bâng quơ")
    
    assert result["jobs"] == []
    assert result["companies"] == []

@pytest.mark.asyncio
async def test_graph_search_dedup_jobs(monkeypatch):
    """Kiểm tra logic loại trùng khi gộp jobs từ 2 nguồn (tech + title)."""
    # 1. Mock entity extraction
    monkeypatch.setattr("app.core.retriever_graph._extract_entities", AsyncMock(return_value={
        "technologies": ["Python"], "job_titles": ["Dev"]
    }))
    
    # 2. Mock run_query trả về jobs trùng title
    async def mock_run_query(cypher, params):
        if "MATCH (j:Job)-[:REQUIRES]->(t)" in cypher:
            return [{"title": "Python Dev", "company": "A"}]
        if "UNWIND $keywords AS kw" in cypher:
            return [{"title": "Python Dev", "company": "B"}] # Cùng title nhưng data khác
        return []
        
    monkeypatch.setattr("app.core.retriever_graph.run_query", mock_run_query)
    
    result = await graph_search("Python Dev")
    
    # Phải bị loại trùng dựa trên title
    assert len(result["jobs"]) == 1
    assert result["jobs"][0]["title"] == "Python Dev"
    # Ưu tiên nguồn đầu tiên (by tech)
    assert result["jobs"][0]["company"] == "A"
