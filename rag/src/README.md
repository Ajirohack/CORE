# RAG System with Multiple LLM Integrations

This RAG (Retrieval Augmented Generation) system provides powerful semantic search and question answering capabilities using various LLM providers.

## Features

- **Document Processing**: Convert various document formats to vectorized chunks
- **Vector Storage**: Store document embeddings in FAISS, Qdrant, or in-memory storage
- **Semantic Search**: Find relevant documents based on meaning rather than keywords
- **Hybrid Search**: Combine dense vector search with sparse BM25 retrieval for improved results
- **Memory Management**: Context-aware memory system with short-term and long-term retention
- **Knowledge Graph Integration**: Entity extraction and relationship mapping to enhance retrieval
- **LLM Integration**: Generate answers with context using multiple LLM providers:
  - OpenAI (gpt-4-turbo, etc.)
  - Anthropic Claude
  - Ollama (self-hosted models)
  - OpenRouter (unified API for multiple LLM providers)
  - Groq (high-performance inference)
  - Open Web UI (OpenAI-compatible interface for Ollama)

## Getting Started

### 1. Setup Environment

First, ensure you have installed all required dependencies:

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file with your preferred configuration:

```bash
# Core RAG Configuration
RAG_EMBEDDING_TYPE=huggingface  # For local development without API keys
RAG_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
RAG_VECTOR_STORE_TYPE=faiss
RAG_COLLECTION_NAME=space_documents
RAG_CHUNK_SIZE=1000
RAG_CHUNK_OVERLAP=200

# LLM Provider Configuration - Uncomment and configure your preferred provider
LLM_PROVIDER=openai  # Options: openai, anthropic, ollama, openrouter, groq, openwebui

# OpenAI Configuration
# OPENAI_API_KEY=your_openai_key_here
# OPENAI_MODEL=gpt-4-turbo

# Anthropic Configuration
# ANTHROPIC_API_KEY=your_anthropic_key_here
# ANTHROPIC_MODEL=claude-3-haiku-20240307

# Ollama Configuration (local models)
# LLM_PROVIDER=ollama
# OLLAMA_BASE_URL=http://localhost:11434
# OLLAMA_MODEL=llama3

# OpenRouter Configuration
# OPENROUTER_API_KEY=your_openrouter_key_here
# OPENROUTER_MODEL=openai/gpt-4-turbo

# Groq Configuration
# GROQ_API_KEY=your_groq_key_here
# GROQ_MODEL=llama3-70b-8192

# Open Web UI Configuration
# OPENWEBUI_BASE_URL=http://localhost:8000
# OPENWEBUI_MODEL=default
```

### 3. Initialize the RAG System

Process your documents and build the vector database:

```bash
python -m core.rag_system.initialize_rag --env development
```

### 4. Search and Query

Use the RAG system to search for information or answer questions:

```bash
# Search only (no LLM required)
python -m core.rag_system.examples.rag_example --query "What are the components of the RAG system?" --search-only

# Generate answer with an LLM
python -m core.rag_system.examples.rag_example --query "What are the components of the RAG system?" --llm-provider openai
```

## LLM Provider Integration

### OpenAI

To use OpenAI's models (like GPT-4), set the following environment variables:

```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4-turbo  # or any other available model
```

### Anthropic Claude

To use Claude models:

```bash
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_key_here
ANTHROPIC_MODEL=claude-3-haiku-20240307
```

### Ollama (Self-hosted)

To use locally hosted models with Ollama:

1. Install Ollama from [ollama.ai](https://ollama.ai)
2. Pull your desired model: `ollama pull llama3`
3. Configure the RAG system:

```bash
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
```

### OpenRouter

To access multiple LLM providers through a unified API:

1. Sign up at [OpenRouter](https://openrouter.ai/)
2. Configure the RAG system:

```bash
LLM_PROVIDER=openrouter
OPENROUTER_API_KEY=your_key_here
OPENROUTER_MODEL=openai/gpt-4-turbo  # or any other supported model
```

### Groq

For high-performance inference with Groq:

1. Sign up at [Groq](https://console.groq.com/)
2. Configure:

```bash
LLM_PROVIDER=groq
GROQ_API_KEY=your_key_here
GROQ_MODEL=llama3-70b-8192
```

### Open Web UI

To use Open Web UI's OpenAI-compatible API:

1. Set up Open Web UI with Ollama
2. Configure:

```bash
LLM_PROVIDER=openwebui
OPENWEBUI_BASE_URL=http://localhost:8000
OPENWEBUI_MODEL=default  # or the specific model you've configured
```

## Using the RAG System in Your Code

### Basic Search

```python
from core.rag_system.rag_system import RAGSystem
from config.rag_config import get_config

# Initialize the system
config = get_config("development")
rag = RAGSystem(config=config)

# Search for documents
results = rag.search("What are the key features?", k=5)

# Display results
for i, result in enumerate(results):
    print(f"Result {i+1}: {result['content'][:100]}...")
```

### Question Answering with LLM

```python
from core.rag_system.rag_system import RAGSystem
from config.rag_config import get_config

# Initialize the system
config = get_config("development")
rag = RAGSystem(config=config)

# Answer a question
answer = rag.answer_question(
    "How does the vector database work?",
    llm_provider="openai",  # Or any other supported provider
    temperature=0.0
)

print(f"Answer: {answer['answer']}")
print("Sources:")
for source in answer['sources']:
    print(f"- {source}")
```

## Advanced Configuration

For advanced configuration options, refer to the settings in `config/rag_config.py`. You can customize:

- Embedding models and dimensions
- Vector store settings
- Document processing parameters
- LLM provider-specific settings

## Benchmarking and Performance Evaluation

The RAG system includes a benchmarking utility to measure document processing, search, and answer generation performance.

### Running Benchmarks

To run performance benchmarks and generate a report:

```bash
python -m core.rag_system.benchmarks.run_benchmarks --num_docs 100 --words_per_doc 200
```

This will:

- Generate synthetic documents
- Measure document processing and search throughput
- Save results and generate a performance report with plots in `./benchmark_results`

### Benchmark Output

- JSON results file with timing and memory usage
- PNG plot summarizing throughput, duration, and memory usage

## Troubleshooting

If you encounter issues:

1. **API Key Errors**: Ensure your API keys are correct and properly formatted
2. **Import Errors**: Install any missing dependencies with `pip install`
3. **Connection Issues**: Check that local services (Ollama, Open Web UI) are running
4. **Memory Issues**: For large documents, try reducing chunk size or batch size

## Implementation Notes

- Token-aware context management is enforced for all LLM providers
- Structured metadata is used for all document and source tracking
- Centralized configuration is managed via Pydantic models in `config/rag_config.py`
- All LLM and embedding API calls use robust retry mechanisms
- Comprehensive unit and integration tests are provided in `tests/rag_system/`
- See `core/rag_system/utils/benchmark.py` for benchmarking details

## Core Completion Tasks (May 2025) - In Progress

- [x] Implement hybrid search (dense + sparse retrieval) - Implementation started May 10, 2025
- [x] Add memory and context management for advanced RAG - Implementation started May 10, 2025
- [x] Integrate knowledge graph capabilities for enhanced retrieval - Implementation started May 10, 2025

> See `/docs/implementation-checklist.md` for overall project progress tracking. Implementation details for each feature can be found in their respective module directories.

## Advanced Features Implementation

### Hybrid Search (Dense + Sparse Retrieval)

The hybrid search implementation combines the power of dense vector retrieval with sparse BM25 retrieval for more comprehensive search results. This approach leverages:

- **Dense Retrieval**: Semantic understanding via embeddings
- **Sparse Retrieval**: Keyword matching via BM25 or similar algorithms
- **Fusion Techniques**: RRF (Reciprocal Rank Fusion) for combining results

Implementation files:

- `core/rag_system/retrieval/hybrid_retriever.py` - Core hybrid search logic
- `core/rag_system/retrieval/sparse_retrieval.py` - BM25 implementation

### Memory and Context Management

Advanced context management enables conversational RAG with:

- **Short-term Memory**: Tracking recent interactions
- **Long-term Memory**: Storing important user information
- **Context Window Management**: Token-aware context truncation and selection

Implementation files:

- `core/rag_system/memory/conversation_memory.py` - Memory management
- `core/rag_system/memory/context_manager.py` - Context window handling

### Knowledge Graph Integration

Knowledge graph capabilities enhance retrieval with:

- **Entity Recognition**: Identifying key entities in documents
- **Relationship Extraction**: Understanding connections between entities
- **Graph-based Retrieval**: Using graph structure for improved search

Implementation files:

- `core/rag_system/knowledge_graph/entity_extractor.py` - Entity recognition
- `core/rag_system/knowledge_graph/graph_builder.py` - Knowledge graph construction
- `core/rag_system/knowledge_graph/graph_retriever.py` - Graph-based search

## Implementation Roadmap

1. Complete basic implementations of each advanced feature (May 15, 2025)
2. Integrate with existing RAG system components (May 20, 2025)
3. Test and benchmark performance improvements (May 25, 2025)
4. Finalize documentation and examples (May 30, 2025)
