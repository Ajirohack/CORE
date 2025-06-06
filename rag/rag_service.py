"""
RAG service implementation.
Provides comprehensive Retrieval-Augmented Generation capabilities with multi-modal storage.
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional, Union
import hashlib
from datetime import datetime
import uuid
from pathlib import Path

try:
    from ..base_service import BaseService, ServiceRequest, ServiceResponse
except ImportError:
    # For when running as a script
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from base_service import BaseService, ServiceRequest, ServiceResponse

logger = logging.getLogger(__name__)

class RAGService(BaseService):
    """
    Service for Retrieval-Augmented Generation with multi-modal storage,
    advanced retrieval techniques, and contextual memory.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("rag", "1.0.0", config)
        self.vector_store = None
        self.graph_store = None
        self.relational_store = None
        self.cache_store = None
        self.embedding_model = None
        self.documents = {}
        self.collections = {}
        
    def get_description(self) -> str:
        return "Comprehensive RAG system with multi-modal storage, advanced retrieval, and contextual memory"
    
    def get_capabilities(self) -> List[str]:
        return [
            "document_ingestion",
            "semantic_search",
            "hybrid_retrieval",
            "knowledge_graphs",
            "contextual_memory",
            "query_enhancement"
        ]
    
    def get_endpoints(self) -> Dict[str, str]:
        return {
            "ingest_document": "/rag/ingest",
            "search": "/rag/search",
            "query": "/rag/query",
            "get_document": "/rag/documents/{doc_id}",
            "list_collections": "/rag/collections",
            "create_collection": "/rag/collections/create"
        }
    
    async def initialize(self) -> bool:
        """Initialize the RAG service"""
        try:
            # Initialize storage backends
            await self._initialize_storage()
            
            # Initialize embedding model
            await self._initialize_embedding_model()
            
            # Load existing collections
            await self._load_collections()
            
            self.logger.info("RAG service initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize RAG service: {e}")
            return False
    
    async def process_request(self, request: ServiceRequest) -> ServiceResponse:
        """Process incoming service request"""
        try:
            action = request.action
            payload = request.payload
            
            if action == "ingest_document":
                result = await self._ingest_document(payload)
            elif action == "search":
                result = await self._search(payload)
            elif action == "query":
                result = await self._query(payload)
            elif action == "get_document":
                result = await self._get_document(payload.get("doc_id"))
            elif action == "list_collections":
                result = await self._list_collections()
            elif action == "create_collection":
                result = await self._create_collection(payload)
            elif action == "delete_document":
                result = await self._delete_document(payload.get("doc_id"))
            else:
                return ServiceResponse(
                    request_id=request.request_id,
                    service_id=self.service_id,
                    status="error",
                    error=f"Unknown action: {action}"
                )
            
            return ServiceResponse(
                request_id=request.request_id,
                service_id=self.service_id,
                status="success",
                data=result
            )
            
        except Exception as e:
            self.logger.error(f"Error processing request {request.request_id}: {e}")
            return ServiceResponse(
                request_id=request.request_id,
                service_id=self.service_id,
                status="error",
                error=str(e)
            )
    
    async def shutdown(self):
        """Cleanup on service shutdown"""
        # Close storage connections
        if self.vector_store:
            await self.vector_store.close()
        if self.graph_store:
            await self.graph_store.close()
        if self.relational_store:
            await self.relational_store.close()
        if self.cache_store:
            await self.cache_store.close()
        
        self.logger.info("RAG service shutdown complete")
    
    async def _initialize_storage(self):
        """Initialize storage backends"""
        # Mock storage initialization - in production these would be real clients
        self.vector_store = MockVectorStore()
        self.graph_store = MockGraphStore()
        self.relational_store = MockRelationalStore()
        self.cache_store = MockCacheStore()
        
        await self.vector_store.initialize()
        await self.graph_store.initialize()
        await self.relational_store.initialize()
        await self.cache_store.initialize()
        
        self.logger.info("Storage backends initialized")
    
    async def _initialize_embedding_model(self):
        """Initialize embedding model"""
        # Mock embedding model - in production this would be a real model
        self.embedding_model = MockEmbeddingModel()
        await self.embedding_model.initialize()
        
        self.logger.info("Embedding model initialized")
    
    async def _load_collections(self):
        """Load existing document collections"""
        # Mock collection loading
        self.collections = {
            "default": {
                "id": "default",
                "name": "Default Collection",
                "description": "Default document collection",
                "document_count": 0,
                "created_at": datetime.utcnow().isoformat()
            }
        }
        
        self.logger.info(f"Loaded {len(self.collections)} collections")
    
    async def _ingest_document(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Ingest a document into the RAG system"""
        document_id = payload.get("document_id", str(uuid.uuid4()))
        content = payload.get("content", "")
        metadata = payload.get("metadata", {})
        collection_id = payload.get("collection_id", "default")
        
        if not content:
            raise ValueError("Document content is required")
        
        # Create document object
        document = {
            "id": document_id,
            "content": content,
            "metadata": metadata,
            "collection_id": collection_id,
            "ingested_at": datetime.utcnow().isoformat(),
            "chunks": [],
            "embeddings": []
        }
        
        # Chunk the document
        chunks = await self._chunk_document(content)
        document["chunks"] = chunks
        
        # Generate embeddings
        embeddings = await self._generate_embeddings(chunks)
        document["embeddings"] = embeddings
        
        # Store in vector database
        await self._store_vectors(document_id, chunks, embeddings, metadata)
        
        # Store in graph database
        await self._store_graph_entities(document_id, content, metadata)
        
        # Store metadata in relational database
        await self._store_metadata(document_id, metadata, collection_id)
        
        # Cache the document
        await self._cache_document(document)
        
        # Update document registry
        self.documents[document_id] = document
        
        # Update collection count
        if collection_id in self.collections:
            self.collections[collection_id]["document_count"] += 1
        
        return {
            "document_id": document_id,
            "status": "ingested",
            "chunks_created": len(chunks),
            "embeddings_generated": len(embeddings),
            "collection_id": collection_id
        }
    
    async def _search(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Perform semantic search"""
        query = payload.get("query", "")
        collection_id = payload.get("collection_id")
        top_k = payload.get("top_k", 5)
        search_type = payload.get("search_type", "semantic")  # semantic, hybrid, graph
        
        if not query:
            raise ValueError("Search query is required")
        
        results = []
        
        if search_type == "semantic":
            results = await self._semantic_search(query, collection_id, top_k)
        elif search_type == "hybrid":
            results = await self._hybrid_search(query, collection_id, top_k)
        elif search_type == "graph":
            results = await self._graph_search(query, collection_id, top_k)
        else:
            raise ValueError(f"Unknown search type: {search_type}")
        
        return {
            "query": query,
            "search_type": search_type,
            "results": results,
            "total_results": len(results)
        }
    
    async def _query(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process a full RAG query with context generation"""
        query = payload.get("query", "")
        collection_id = payload.get("collection_id")
        context_length = payload.get("context_length", 1000)
        
        if not query:
            raise ValueError("Query is required")
        
        # Enhanced query processing
        enhanced_query = await self._enhance_query(query)
        
        # Retrieve relevant context
        search_results = await self._search({
            "query": enhanced_query,
            "collection_id": collection_id,
            "top_k": 10,
            "search_type": "hybrid"
        })
        
        # Generate context
        context = await self._generate_context(search_results["results"], context_length)
        
        # Store query for learning
        await self._store_query_context(query, context, search_results)
        
        return {
            "query": query,
            "enhanced_query": enhanced_query,
            "context": context,
            "sources": search_results["results"],
            "context_length": len(context)
        }
    
    async def _chunk_document(self, content: str) -> List[Dict[str, Any]]:
        """Split document into chunks"""
        # Simple chunking - in production this would be more sophisticated
        chunk_size = 500
        overlap = 50
        
        chunks = []
        words = content.split()
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk_words = words[i:i + chunk_size]
            chunk_text = " ".join(chunk_words)
            
            chunk = {
                "id": f"chunk_{i}",
                "text": chunk_text,
                "start_index": i,
                "end_index": min(i + chunk_size, len(words)),
                "token_count": len(chunk_words)
            }
            chunks.append(chunk)
        
        return chunks
    
    async def _generate_embeddings(self, chunks: List[Dict[str, Any]]) -> List[List[float]]:
        """Generate embeddings for document chunks"""
        embeddings = []
        
        for chunk in chunks:
            embedding = await self.embedding_model.embed(chunk["text"])
            embeddings.append(embedding)
        
        return embeddings
    
    async def _semantic_search(self, query: str, collection_id: Optional[str], top_k: int) -> List[Dict[str, Any]]:
        """Perform semantic vector search"""
        # Generate query embedding
        query_embedding = await self.embedding_model.embed(query)
        
        # Search vector store
        results = await self.vector_store.search(query_embedding, top_k, collection_id)
        
        return results
    
    async def _hybrid_search(self, query: str, collection_id: Optional[str], top_k: int) -> List[Dict[str, Any]]:
        """Perform hybrid search combining semantic and keyword search"""
        # Semantic search
        semantic_results = await self._semantic_search(query, collection_id, top_k)
        
        # Keyword search (mock implementation)
        keyword_results = await self._keyword_search(query, collection_id, top_k)
        
        # Combine and re-rank results
        combined_results = await self._combine_search_results(semantic_results, keyword_results, top_k)
        
        return combined_results
    
    async def _graph_search(self, query: str, collection_id: Optional[str], top_k: int) -> List[Dict[str, Any]]:
        """Perform graph-based search"""
        # Extract entities from query
        entities = await self._extract_entities(query)
        
        # Search graph store
        results = await self.graph_store.search_entities(entities, top_k, collection_id)
        
        return results
    
    async def _keyword_search(self, query: str, collection_id: Optional[str], top_k: int) -> List[Dict[str, Any]]:
        """Perform keyword-based search"""
        # Mock keyword search
        results = []
        query_words = set(query.lower().split())
        
        for doc_id, doc in self.documents.items():
            if collection_id and doc.get("collection_id") != collection_id:
                continue
            
            for chunk in doc.get("chunks", []):
                chunk_words = set(chunk["text"].lower().split())
                overlap = len(query_words.intersection(chunk_words))
                
                if overlap > 0:
                    results.append({
                        "document_id": doc_id,
                        "chunk_id": chunk["id"],
                        "text": chunk["text"],
                        "score": overlap / len(query_words),
                        "match_type": "keyword"
                    })
        
        # Sort by score and return top_k
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]
    
    async def _enhance_query(self, query: str) -> str:
        """Enhance query with synonyms and context"""
        # Mock query enhancement
        return f"enhanced: {query}"
    
    async def _generate_context(self, search_results: List[Dict[str, Any]], max_length: int) -> str:
        """Generate context from search results"""
        context_parts = []
        current_length = 0
        
        for result in search_results:
            text = result.get("text", "")
            if current_length + len(text) <= max_length:
                context_parts.append(text)
                current_length += len(text)
            else:
                # Add partial text to reach max_length
                remaining = max_length - current_length
                if remaining > 0:
                    context_parts.append(text[:remaining])
                break
        
        return "\n\n".join(context_parts)
    
    async def _store_vectors(self, doc_id: str, chunks: List[Dict[str, Any]], embeddings: List[List[float]], metadata: Dict[str, Any]):
        """Store vectors in vector database"""
        await self.vector_store.store(doc_id, chunks, embeddings, metadata)
    
    async def _store_graph_entities(self, doc_id: str, content: str, metadata: Dict[str, Any]):
        """Store entities and relationships in graph database"""
        entities = await self._extract_entities(content)
        await self.graph_store.store_entities(doc_id, entities, metadata)
    
    async def _store_metadata(self, doc_id: str, metadata: Dict[str, Any], collection_id: str):
        """Store document metadata in relational database"""
        await self.relational_store.store_metadata(doc_id, metadata, collection_id)
    
    async def _cache_document(self, document: Dict[str, Any]):
        """Cache document for fast retrieval"""
        await self.cache_store.set(f"doc:{document['id']}", document)
    
    async def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities from text"""
        # Mock entity extraction
        words = text.split()
        entities = []
        
        for i, word in enumerate(words):
            if word.isupper() or word.istitle():
                entities.append({
                    "text": word,
                    "type": "ENTITY",
                    "start": i,
                    "end": i + 1
                })
        
        return entities
    
    async def _combine_search_results(self, semantic_results: List[Dict[str, Any]], keyword_results: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
        """Combine and re-rank search results"""
        # Simple combination - in production this would be more sophisticated
        all_results = semantic_results + keyword_results
        
        # Remove duplicates and re-rank
        seen = set()
        combined = []
        
        for result in all_results:
            key = (result.get("document_id"), result.get("chunk_id"))
            if key not in seen:
                seen.add(key)
                combined.append(result)
        
        # Sort by score
        combined.sort(key=lambda x: x.get("score", 0), reverse=True)
        return combined[:top_k]
    
    async def _store_query_context(self, query: str, context: str, search_results: Dict[str, Any]):
        """Store query and context for learning"""
        query_record = {
            "query": query,
            "context": context,
            "results_count": len(search_results.get("results", [])),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.cache_store.set(f"query:{hashlib.md5(query.encode()).hexdigest()}", query_record)
    
    async def _get_document(self, doc_id: str) -> Dict[str, Any]:
        """Get document by ID"""
        if doc_id not in self.documents:
            raise ValueError(f"Document {doc_id} not found")
        
        return self.documents[doc_id]
    
    async def _list_collections(self) -> Dict[str, Any]:
        """List all collections"""
        return {
            "collections": list(self.collections.values()),
            "total_count": len(self.collections)
        }
    
    async def _create_collection(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new collection"""
        collection_id = payload.get("collection_id", str(uuid.uuid4()))
        name = payload.get("name", f"Collection {collection_id}")
        description = payload.get("description", "")
        
        if collection_id in self.collections:
            raise ValueError(f"Collection {collection_id} already exists")
        
        collection = {
            "id": collection_id,
            "name": name,
            "description": description,
            "document_count": 0,
            "created_at": datetime.utcnow().isoformat()
        }
        
        self.collections[collection_id] = collection
        
        return {
            "collection_id": collection_id,
            "status": "created"
        }
    
    async def _delete_document(self, doc_id: str) -> Dict[str, Any]:
        """Delete a document"""
        if doc_id not in self.documents:
            raise ValueError(f"Document {doc_id} not found")
        
        # Remove from storage backends
        await self.vector_store.delete(doc_id)
        await self.graph_store.delete(doc_id)
        await self.relational_store.delete(doc_id)
        await self.cache_store.delete(f"doc:{doc_id}")
        
        # Remove from memory
        del self.documents[doc_id]
        
        return {
            "document_id": doc_id,
            "status": "deleted"
        }


# Mock storage implementations
class MockVectorStore:
    def __init__(self):
        self.vectors = {}
    
    async def initialize(self):
        pass
    
    async def store(self, doc_id: str, chunks: List[Dict[str, Any]], embeddings: List[List[float]], metadata: Dict[str, Any]):
        self.vectors[doc_id] = {
            "chunks": chunks,
            "embeddings": embeddings,
            "metadata": metadata
        }
    
    async def search(self, query_embedding: List[float], top_k: int, collection_id: Optional[str] = None) -> List[Dict[str, Any]]:
        # Mock search returning dummy results
        results = []
        for i, (doc_id, data) in enumerate(self.vectors.items()):
            if i >= top_k:
                break
            for j, chunk in enumerate(data["chunks"]):
                results.append({
                    "document_id": doc_id,
                    "chunk_id": chunk["id"],
                    "text": chunk["text"],
                    "score": 0.9 - (i * 0.1),
                    "match_type": "semantic"
                })
        return results[:top_k]
    
    async def delete(self, doc_id: str):
        if doc_id in self.vectors:
            del self.vectors[doc_id]
    
    async def close(self):
        pass


class MockGraphStore:
    def __init__(self):
        self.entities = {}
    
    async def initialize(self):
        pass
    
    async def store_entities(self, doc_id: str, entities: List[Dict[str, Any]], metadata: Dict[str, Any]):
        self.entities[doc_id] = {
            "entities": entities,
            "metadata": metadata
        }
    
    async def search_entities(self, entities: List[Dict[str, Any]], top_k: int, collection_id: Optional[str] = None) -> List[Dict[str, Any]]:
        return []
    
    async def delete(self, doc_id: str):
        if doc_id in self.entities:
            del self.entities[doc_id]
    
    async def close(self):
        pass


class MockRelationalStore:
    def __init__(self):
        self.metadata = {}
    
    async def initialize(self):
        pass
    
    async def store_metadata(self, doc_id: str, metadata: Dict[str, Any], collection_id: str):
        self.metadata[doc_id] = {
            "metadata": metadata,
            "collection_id": collection_id
        }
    
    async def delete(self, doc_id: str):
        if doc_id in self.metadata:
            del self.metadata[doc_id]
    
    async def close(self):
        pass


class MockCacheStore:
    def __init__(self):
        self.cache = {}
    
    async def initialize(self):
        pass
    
    async def set(self, key: str, value: Any):
        self.cache[key] = value
    
    async def get(self, key: str) -> Any:
        return self.cache.get(key)
    
    async def delete(self, key: str):
        if key in self.cache:
            del self.cache[key]
    
    async def close(self):
        pass


class MockEmbeddingModel:
    async def initialize(self):
        pass
    
    async def embed(self, text: str) -> List[float]:
        # Generate mock embedding vector
        import hashlib
        hash_val = int(hashlib.md5(text.encode()).hexdigest(), 16)
        # Generate 384-dimensional mock embedding
        embedding = [(hash_val >> i) % 100 / 100.0 for i in range(384)]
        return embedding
