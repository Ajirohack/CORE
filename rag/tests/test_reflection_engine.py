import pytest
import asyncio
from src.core.reflection_engine import ReflectionEngine, RetrievalResult
from src.storage.cache_store import init_cache_store

# Patch get_retriever to return a mock retriever
class MockRetriever:
    async def retrieve(self, query, top_k=5, cache_key=None):
        # Return mock results with a score and content
        return [
            {"document_id": "doc1", "chunk_index": 0, "score": 0.5, "content": f"Content for {query}"},
            {"document_id": "doc1", "chunk_index": 1, "score": 0.6, "content": f"Extra info for {query}"}
        ]

def mock_get_retriever():
    return MockRetriever()

# Patch the ReflectionEngine to use the mock retriever
ReflectionEngine.get_retriever = staticmethod(mock_get_retriever)

@pytest.mark.asyncio
async def test_reflect_with_gaps(monkeypatch):
    init_cache_store()
    # Patch get_retriever globally in the module
    monkeypatch.setattr("src.retrieval.retriever.get_retriever", mock_get_retriever)
    engine = ReflectionEngine()
    query = "Explain quantum entanglement in simple terms"
    # Provide initial results with low score to trigger reflection
    initial_results = [
        {"document_id": "doc1", "chunk_index": 0, "score": 0.3, "content": "Partial answer."}
    ]
    result = await engine.reflect(query, initial_results)
    assert isinstance(result, RetrievalResult)
    assert result.has_reflected is True
    assert isinstance(result.reflection_queries, list)
    assert isinstance(result.reflection_results, list)
    assert result.has_sufficient_info is True
    assert isinstance(result.ranked_chunks, list)

@pytest.mark.asyncio
async def test_reflect_sufficient_info(monkeypatch):
    init_cache_store()
    monkeypatch.setattr("src.retrieval.retriever.get_retriever", mock_get_retriever)
    engine = ReflectionEngine()
    query = "What is the capital of France?"
    # Provide initial results with high score to skip reflection
    initial_results = [
        {"document_id": "doc2", "chunk_index": 0, "score": 0.9, "content": "Paris is the capital of France."}
    ]
    result = await engine.reflect(query, initial_results)
    assert isinstance(result, RetrievalResult)
    assert result.has_reflected is True
    assert result.has_sufficient_info is True
    assert isinstance(result.ranked_chunks, list)
