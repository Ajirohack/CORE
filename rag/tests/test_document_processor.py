import pytest
import asyncio
from src.core.document_processor import DocumentProcessor

@pytest.mark.asyncio
async def test_create_fixed_chunks():
    processor = DocumentProcessor()
    text = "This is a test document. It has several sentences. Here is another one. And another."
    chunk_size = 30
    chunk_overlap = 10
    chunks = await processor._create_fixed_chunks(text, chunk_size, chunk_overlap)
    assert isinstance(chunks, list)
    assert all('text' in chunk for chunk in chunks)
    assert all('start_char' in chunk and 'end_char' in chunk for chunk in chunks)
    # Ensure chunks overlap
    if len(chunks) > 1:
        assert chunks[1]['start_char'] < chunks[0]['end_char']

@pytest.mark.asyncio
async def test_create_adaptive_chunks():
    processor = DocumentProcessor()
    text = """
    Paragraph one.

    Paragraph two is a bit longer and should be chunked with the first if small enough.

    Paragraph three is here.
    """
    chunk_size = 50
    chunk_overlap = 10
    chunks = await processor._create_adaptive_chunks(text, chunk_size, chunk_overlap)
    assert isinstance(chunks, list)
    assert all('text' in chunk for chunk in chunks)
    assert all('start_char' in chunk and 'end_char' in chunk for chunk in chunks)
    # Should create at least one chunk
    assert len(chunks) >= 1

@pytest.mark.asyncio
async def test_extract_entities():
    processor = DocumentProcessor()
    text = "Apple was founded by Steve Jobs in California."
    entities = await processor._extract_entities(text)
    assert isinstance(entities, list)
    # Should find at least one entity (ORG, PERSON, GPE)
    labels = {e['label'] for e in entities}
    assert 'ORG' in labels or 'PERSON' in labels or 'GPE' in labels

@pytest.mark.asyncio
async def test_process_document():
    processor = DocumentProcessor()
    text = "Test document for process_document. This should be chunked and processed."
    filename = "test.txt"
    document_id = await processor.process_document(text, filename)
    assert isinstance(document_id, str)
    assert len(document_id) > 0
