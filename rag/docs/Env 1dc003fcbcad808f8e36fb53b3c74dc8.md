# Env

---

```
# Superior RAG System Environment Configuration

# Environment (development, production)
ENVIRONMENT=development

# Authentication
AUTH_SECRET_KEY=your_auth_secret_key_change_this_in_production
API_KEY=your_api_key_for_testing

# LLM Configuration
LLM_API_KEY=your_openai_api_key_here
LLM_PROVIDER=openai  # openai, anthropic, huggingface, local
LLM_MODEL=gpt-4  # or claude-2, llama-2-70b, etc.

# Vector Database (Qdrant)
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Relational Database (PostgreSQL)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=superior_rag

# Graph Database (Neo4j)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=superior_rag

# Cache (Redis)
REDIS_HOST=localhost
REDIS_PORT=6379

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE=logs/superior_rag.log

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
CORS_ALLOWED_ORIGINS=*

# Memory Configuration
WORKING_MEMORY_TTL=600  # 10 minutes
SHORT_TERM_MEMORY_TTL_DAYS=7  # 7 days

# Advanced Settings
EMBEDDING_MODEL=BAAI/bge-large-en-v1.5
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
ENABLE_REFLECTION=true
ENABLE_QUERY_TRANSFORMATION=true
```