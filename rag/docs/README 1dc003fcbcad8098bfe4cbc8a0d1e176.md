# README

---

# Superior RAG System

A comprehensive Retrieval-Augmented Generation (RAG) system that combines multiple retrieval strategies with sophisticated memory management and recursive reflection.

## Features

- **Advanced Retrieval Mechanisms**
    - Hybrid fusion of vector, keyword, and graph-based retrieval
    - Recursive retrieval with reflection capabilities
    - Multi-strategy query transformation
- **Cognitive Memory Framework**
    - Working memory for active session context
    - Short-term memory for recent interactions
    - Long-term memory for persistent knowledge
    - Memory decay and consolidation mechanisms
- **Document Processing Pipeline**
    - Adaptive chunking based on document structure
    - Entity extraction and relationship mapping
    - Multi-granularity embeddings
- **Context Optimization**
    - Smart context compression for token efficiency
    - Information density analysis
    - Context prioritization based on relevance
- **Comprehensive Admin Controls**
    - Monitoring and analytics
    - Configuration management
    - User and session tracking

## System Architecture

The system is organized into seven layers:

1. **User Interface Layer** - Access points for users, developers, and administrators
2. **API Gateway Layer** - Authentication, rate limiting, and request routing
3. **Core Processing Layer** - Query and document processing, reflection, memory integration
4. **Retrieval Engine Layer** - Multiple retrieval strategies and fusion
5. **Memory Framework Layer** - Different types of memory management
6. **Storage Layer** - Various databases optimized for different data types
7. **Integration Layer** - Connections with external systems

## Technologies Used

- **Python** - Core programming language
- **FastAPI** - Web framework for API
- **Qdrant** - Vector database for embedding storage
- **PostgreSQL** - Relational database with pgvector extension
- **Neo4j** - Graph database for entity relationships
- **Redis** - In-memory database for caching and working memory
- **Docker** - Containerization and orchestration

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.10+
- 8GB+ RAM recommended
- Access to an LLM provider (OpenAI, Anthropic, etc.)

### Setup

1. Clone the repository:
    
    ```bash
    git clone <https://github.com/yourusername/superior-rag.git>
    cd superior-rag
    
    ```
    
2. Create a `.env` file based on the provided example:
    
    ```bash
    cp .env.example .env
    
    ```
    
3. Edit the `.env` file to include your LLM API key and other settings.
4. Build and start the services:
    
    ```bash
    docker-compose -f docker/docker-compose.yml up -d
    
    ```
    
5. Run database migrations:
    
    ```bash
    ./scripts/setup.sh
    
    ```
    

### Initial Configuration

1. Initialize the vector database collections:
    
    ```bash
    python -m scripts.init_vector_db
    
    ```
    
2. Install the required Python packages:
    
    ```bash
    pip install -r requirements.txt
    
    ```
    
3. Download the required models:
    
    ```bash
    python -m spacy download en_core_web_sm
    
    ```
    

## Usage

### Starting the API

Start the API server locally with:

```bash
uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload

```

### Basic Query API Example

```python
import requests

# Send a query
response = requests.post(
    "<http://localhost:8000/api/query>",
    headers={"X-API-Key": "your-api-key"},
    json={
        "query": "What is the capital of France?",
        "user_id": "user123",
        "session_id": "session456"
    }
)

# Print the response
print(response.json())

```

### Document Ingestion Example

```python
import requests

# Upload a document
with open("document.pdf", "rb") as f:
    response = requests.post(
        "<http://localhost:8000/api/documents/upload>",
        headers={"X-API-Key": "your-api-key"},
        files={"file": f},
        data={"metadata": '{"source": "example", "author": "John Doe"}'}
    )

# Print the document ID
print(response.json()["document_id"])

```

## API Reference

### Query Endpoints

- `POST /api/query` - Submit a query and get a response
- `GET /api/query/history/{session_id}` - Get query history for a session

### Document Endpoints

- `POST /api/documents/upload` - Upload a document
- `GET /api/documents/{document_id}` - Get document metadata
- `DELETE /api/documents/{document_id}` - Delete a document

### Admin Endpoints

- `GET /api/admin/stats` - Get system statistics
- `GET /api/admin/users/{user_id}` - Get user information
- `GET /api/admin/sessions/{session_id}` - Get session information

## Development

### Project Structure

```
superior-rag/
├── docker/            - Docker configuration files
├── src/               - Source code
│   ├── api/           - API endpoints and middleware
│   ├── core/          - Core processing modules
│   ├── retrieval/     - Retrieval mechanisms
│   ├── memory/        - Memory management
│   ├── storage/       - Database interfaces
│   ├── integration/   - External integrations
│   └── utils/         - Utility functions
├── ui/                - User interfaces
├── scripts/           - Helper scripts
├── tests/             - Test suite
├── config/            - Configuration files
└── docs/              - Documentation

```

### Running Tests

Run the test suite with:

```bash
pytest tests/

```

## Troubleshooting

### Common Issues

- **Vector Database Connection Errors**: Check that Qdrant is running and accessible on the configured port.
- **Memory Errors**: Ensure Redis is running and properly configured for working memory.
- **LLM API Errors**: Verify your API key and check the API provider's status.

### Logs

Logs are available at `logs/superior_rag.log` by default. You can change the log location in the configuration file.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

This project builds upon ideas and techniques from several excellent RAG projects:

- [LlamaIndex](https://github.com/jerryjliu/llama_index)
- [LangChain](https://github.com/langchain-ai/langchain)
- [RAGatouille](https://github.com/bclavie/ragatouille)
- [Haystack](https://github.com/deepset-ai/haystack)