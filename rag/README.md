# Superior RAG System

A comprehensive Retrieval-Augmented Generation (RAG) system with multi-modal storage, advanced retrieval techniques, and contextual memory.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Development](#development)
- [License](#license)

## Overview

The Superior RAG system is designed to overcome the limitations of traditional RAG systems by incorporating multiple storage mechanisms, advanced retrieval strategies, and memory capabilities. It provides a robust framework for document ingestion, efficient retrieval, and accurate response generation.

## Architecture

The system consists of the following core components:

### Storage Layer

- **Vector Store**: Uses Qdrant to store and retrieve document chunk embeddings for semantic search
- **Relational Store**: Uses PostgreSQL for structured metadata, user data, and system state
- **Graph Store**: Uses Neo4j to represent relationships between documents, entities, and concepts
- **Cache Store**: Uses Redis for caching retrieved documents, query transformations, and working memory

### Core Components

- **Document Processor**: Handles document ingestion, chunking, and embedding generation
- **Retriever**: Implements multi-strategy retrieval with fusion capabilities
- **Memory Manager**: Manages working, short-term, and long-term memory
- **API Server**: Provides RESTful endpoints for interacting with the system

### System Flow

1. **Document Ingestion**: Documents are processed, chunked, and stored in all relevant data stores
2. **Query Processing**: User queries are transformed based on context and memory
3. **Multi-Strategy Retrieval**: Documents are retrieved using vector, keyword, and graph-based methods
4. **Result Fusion**: Results from different retrieval methods are fused for optimal relevance
5. **Response Generation**: An LLM generates responses based on retrieved context
6. **Memory Update**: The system updates its memory based on the interaction

## Features

- **Multi-Strategy Retrieval**: Combines vector search, keyword search, and graph-based retrieval
- **Score Fusion**: Merges results from multiple strategies with configurable weights
- **Hierarchical Memory**: Maintains working, short-term, and long-term memory
- **Self-Reflection**: Evaluates retrieval quality and tries alternative approaches if needed
- **Query Transformation**: Rewrites queries based on context and conversation history
- **Adaptive Retrieval**: Adjusts retrieval parameters based on feedback and retrieval quality
- **Extensible Storage**: Supports multiple storage backends with a unified interface
- **Document Processing**: Handles various document formats with intelligent chunking
- **Entity Extraction**: Identifies entities in documents and builds a knowledge graph

## Installation

### Prerequisites

- Python 3.9+
- PostgreSQL 14+ with pgvector extension
- Qdrant Server
- Neo4j Server
- Redis Server

### Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/superior-rag.git
   cd superior-rag
   ```

2. Create a virtual environment (recommended):

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Run the setup script:

   ```bash
   ./scripts/setup.sh
   ```

4. Configure environment variables (copy from example and modify):

   ```bash
   cp .env.example .env
   # Edit .env with your database credentials and API keys
   ```

## Usage

### Starting the Server

```bash
./scripts/start.sh
```

This will start the API server on `http://localhost:8000` by default.

For more options:

```bash
./scripts/start.sh --help
```

### API Endpoints

- `POST /query`: Submit a query to the RAG system
- `POST /documents`: Upload a document for processing
- `GET /documents/{id}`: Retrieve document metadata
- `GET /health`: Check system health status

### Example Query

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key" \
  -d '{"query": "What is RAG?", "max_results": 5}'
```

## Configuration

The system uses a hierarchical configuration system with defaults in `config/default.yaml` and environment-specific overrides in `config/{environment}.yaml`.

Key configuration sections:

- **API settings**: Server host, port, and CORS settings
- **Authentication**: API key and JWT settings
- **Database connections**: Connection details for all storage backends
- **Retrieval settings**: Strategy weights, thresholds, and parameters
- **Document processing**: Chunk size, overlap, and supported formats
- **Memory settings**: TTL and size limits for different memory types
- **LLM settings**: Model selection and parameters

## API Reference

### Query Endpoint

`POST /query`

**Request Body:**

```json
{
  "query": "Your question here",
  "conversation_id": "optional-conversation-id",
  "max_results": 5,
  "include_sources": true
}
```

**Response:**

```json
{
  "answer": "Generated answer to the question",
  "sources": [
    {
      "document_id": 123,
      "document_title": "Document Title",
      "content": "Relevant content snippet",
      "score": 0.95
    }
  ],
  "processing_time": 0.45,
  "context_tokens": 2048
}
```

### Document Upload Endpoint

`POST /documents`

**Request:**

- Multipart form data with file upload

**Response:**

```json
{
  "document_id": 123,
  "title": "Uploaded Document Title",
  "chunks": 15,
  "status": "processed"
}
```

## Development

### Project Structure

```
superior-rag/
├── config/              # Configuration files
├── data/                # Data storage (models, uploads)
├── docker/              # Docker configuration
├── logs/                # Log files
├── scripts/             # Utility scripts
├── src/                 # Source code
│   ├── api/             # API endpoints
│   ├── core/            # Core functionality
│   ├── integration/     # External integrations
│   ├── memory/          # Memory management
│   ├── retrieval/       # Retrieval strategies
│   ├── storage/         # Storage interfaces
│   └── utils/           # Utility functions
└── tests/               # Test suite
```

### Running Tests

```bash
pytest tests/
```

### Docker Deployment

```bash
docker-compose -f docker/docker-compose.yml up
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Citation

If you use this system in your research or project, please cite:

```
@software{superior_rag_2025,
  author = {Your Name},
  title = {Superior RAG: A Comprehensive Retrieval-Augmented Generation System},
  year = {2025},
  url = {https://github.com/yourusername/superior-rag}
}
```
