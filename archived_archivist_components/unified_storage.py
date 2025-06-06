"""
Enhanced storage layer providing unified interfaces for multiple database types.
Implements cross-database relationship management, automatic indexing, and query optimization.
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, List, Optional, Union
from abc import ABC, abstractmethod
from datetime import datetime
from prometheus_client import Counter, Histogram

from core.storage.adapters.qdrant_adapter import QdrantAdapter
from core.storage.adapters.neo4j_adapter import Neo4jAdapter
from core.storage.adapters.postgres_adapter import PostgresAdapter
from core.storage.adapters.redis_adapter import RedisAdapter
from core.storage.adapters.supabase_adapter import SupabaseAdapter

logger = logging.getLogger(__name__)

# Prometheus metrics
STORAGE_OPS = Counter('archivist_storage_ops', 'Number of storage operations', ['operation'])
STORAGE_ERRORS = Counter('archivist_storage_errors', 'Number of storage errors', ['operation'])
STORAGE_OP_DURATION = Histogram('archivist_storage_op_duration_seconds', 'Duration of storage operations', ['operation'])

class StorageAdapter(ABC):
    """Abstract base class for database adapters"""
    
    @abstractmethod
    async def initialize(self):
        """Initialize the storage connection"""
        pass
    
    @abstractmethod
    async def close(self):
        """Close the storage connection"""
        pass
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get a value by key"""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, **kwargs) -> bool:
        """Set a value by key"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        """Delete a value by key"""
        pass

class VectorStorageAdapter(StorageAdapter):
    """Base class for vector database adapters"""
    
    @abstractmethod
    async def create_collection(self, name: str, dimension: int = 512, **kwargs) -> bool:
        """Create a vector collection"""
        pass
    
    @abstractmethod
    async def upsert_vector(self, collection: str, id: str, vector: List[float], payload: Dict[str, Any] = None) -> bool:
        """Insert or update a vector in a collection"""
        pass
    
    @abstractmethod
    async def search_vector(self, collection: str, query_vector: List[float], top_k: int = 5, 
                           filter_query: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Search for similar vectors"""
        pass
    
    @abstractmethod
    async def delete_vectors(self, collection: str, ids: List[str] = None, 
                            filter_query: Dict[str, Any] = None) -> int:
        """Delete vectors matching criteria"""
        pass

class GraphStorageAdapter(StorageAdapter):
    """Base class for graph database adapters"""
    
    @abstractmethod
    async def add_node(self, label: Union[str, List[str]], properties: Dict[str, Any]) -> str:
        """Add a node to the graph"""
        pass
    
    @abstractmethod
    async def add_relationship(self, start_node: str, end_node: str, 
                             relationship_type: str, properties: Dict[str, Any] = None) -> bool:
        """Add a relationship between nodes"""
        pass
    
    @abstractmethod
    async def query(self, query_string: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Execute a graph query"""
        pass
    
    @abstractmethod
    async def delete_node(self, node_id: str) -> bool:
        """Delete a node by ID"""
        pass
    
    @abstractmethod
    async def delete_relationship(self, relationship_id: str) -> bool:
        """Delete a relationship by ID"""
        pass

class RelationalStorageAdapter(StorageAdapter):
    """Base class for relational database adapters"""
    
    @abstractmethod
    async def query(self, query_string: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Execute a SQL query"""
        pass
    
    @abstractmethod
    async def execute(self, query_string: str, params: Dict[str, Any] = None) -> int:
        """Execute a SQL command, returning affected rows"""
        pass
    
    @abstractmethod
    async def create_table(self, table_name: str, schema: Dict[str, str]) -> bool:
        """Create a table with the given schema"""
        pass

class CacheAdapter(StorageAdapter):
    """Base class for cache adapters"""
    
    @abstractmethod
    async def set_with_expiry(self, key: str, value: Any, expiry_seconds: int) -> bool:
        """Set value with expiration time"""
        pass
    
    @abstractmethod
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment a numeric value"""
        pass
    
    @abstractmethod
    async def decrement(self, key: str, amount: int = 1) -> int:
        """Decrement a numeric value"""
        pass
    
    @abstractmethod
    async def flush(self) -> bool:
        """Clear all values from cache"""
        pass


class UnifiedStorageLayer:
    """
    Unified storage layer that provides a consistent interface to multiple storage systems,
    manages cross-database relationships, and implements automatic indexing.
    """
    
    def __init__(self):
        self.qdrant = QdrantAdapter()
        self.neo4j = Neo4jAdapter()
        self.postgres = PostgresAdapter(dsn="postgresql://user:password@localhost/db")
        self.redis = RedisAdapter()
        self.supabase = SupabaseAdapter(url="https://example.supabase.co", key="public-anon-key")
        
        # Initialize metrics
        self.metrics = {
            'store_memory_calls': 0,
            'retrieve_memory_calls': 0,
            'add_relationship_calls': 0,
            'update_embedding_calls': 0,
            'errors': 0
        }
        self.last_error = None
        self.last_operation = None
        self.last_operation_time = None

    @property
    def health(self):
        return {
            'metrics': self.metrics,
            'last_error': self.last_error,
            'last_operation': self.last_operation,
            'last_operation_time': self.last_operation_time
        }

    async def initialize(self):
        """Initialize all storage adapters"""
        try:
            await self.qdrant.initialize()
            await self.neo4j.initialize()
            await self.postgres.connect()
            await self.redis.connect()
            await self.supabase.connect()
            logger.info("UnifiedStorageLayer initialized all adapters.")
        except Exception as e:
            logger.error(f"UnifiedStorageLayer initialization error: {e}")

    async def close(self):
        """Close all storage connections"""
        await self.qdrant.close()
        await self.neo4j.close()
        await self.postgres.close()
        await self.redis.close()
        await self.supabase.close()
        logger.info("UnifiedStorageLayer closed all adapters.")

    async def store_memory(self, memory_data):
        """
        Store a memory across appropriate storage systems with automatic indexing
        """
        op = 'store_memory'
        STORAGE_OPS.labels(operation=op).inc()
        self.metrics['store_memory_calls'] += 1
        self.last_operation = 'store_memory'
        self.last_operation_time = time.time()
        try:
            # Generate a unique ID if not provided
            memory_id = memory_data.get("id", f"mem_{datetime.now().timestamp()}")
            memory_data["id"] = memory_id
            memory_type = memory_data.get("memory_type", "short_term")
            
            # 1. Store in vector DB for semantic search
            if "vector" in memory_data:
                vector = memory_data["vector"]
            else:
                # In real implementation, generate embedding from content
                vector = [0.0] * 512  # Placeholder
            
            await self.qdrant.upsert_vector(
                collection=memory_type,
                id=memory_id,
                vector=vector,
                payload={
                    "content": memory_data.get("content"),
                    "metadata": memory_data.get("metadata", {})
                }
            )
            # Store vector in Qdrant
            await self.qdrant.store_vectors(
                collection=memory_data["memory_type"],
                vectors=[memory_data["vector"]],
                payloads=[memory_data]
            )
            self.metrics['vector_ops'] += 1
            
            # 2. Store in graph DB for relationships
            node_id = await self.neo4j.add_node(
                label=["Memory", memory_type.capitalize()],
                properties={
                    "id": memory_id,
                    "timestamp": memory_data.get("timestamp", datetime.now().isoformat()),
                    "source": memory_data.get("source", "unknown")
                }
            )
            self.metrics['graph_ops'] += 1
            
            # 3. Create relationships if specified
            if "relationships" in memory_data:
                for relationship in memory_data["relationships"]:
                    await self.neo4j.add_relationship(
                        start_node=node_id,
                        end_node=relationship["target_id"],
                        relationship_type=relationship["type"],
                        properties=relationship.get("properties", {})
                    )
                    self.metrics['graph_ops'] += 1
            
            # 4. Add to cache for quick access if it's short-term memory
            if memory_type == "short_term":
                await self.cache.set_with_expiry(
                    key=f"memory:{memory_id}",
                    value=memory_data,
                    expiry_seconds=3600  # Cache for 1 hour
                )
            
            logger.info(f"Stored memory {memory_id} in Qdrant and Neo4j.")
            return memory_id
            
        except Exception as e:
            logger.error(f"store_memory error: {e}")
            STORAGE_ERRORS.labels(operation=op).inc()
            self.metrics['errors'] += 1
            self.last_error = str(e)
            return ""
    
    async def retrieve_memory(self, query):
        """
        Retrieve memories using unified query interface
        """
        op = 'retrieve_memory'
        STORAGE_OPS.labels(operation=op).inc()
        self.metrics['retrieve_memory_calls'] += 1
        self.last_operation = 'retrieve_memory'
        self.last_operation_time = time.time()
        try:
            results = []
            memory_type = query.get("memory_type", "all")
            
            # 1. Check cache first for exact match if ID is provided
            if "id" in query:
                cached = await self.cache.get(f"memory:{query['id']}")
                if cached:
                    return [cached]
            
            # 2. Vector search for semantic similarity
            if "content" in query:
                # In real implementation, generate embedding from content
                vector = [0.0] * 512  # Placeholder
                
                # Search in appropriate collection(s)
                collections = [memory_type] if memory_type != "all" else ["short_term", "long_term"]
                for collection in collections:
                    vector_results = await self.qdrant.search_vector(
                        collection=collection,
                        query_vector=vector,
                        top_k=query.get("limit", 5)
                    )
                    self.metrics['vector_ops'] += 1
                    
                    # Process vector search results
                    for result in vector_results:
                        # 3. Enrich with graph relationships
                        graph_data = await self.neo4j.query(f"""
                        MATCH (m:Memory {{id: '{result['id']}'}})
                        OPTIONAL MATCH (m)-[r]->(related)
                        RETURN m, collect({{type: type(r), target: related.id, properties: properties(r)}}) as relationships
                        """)
                        
                        # Combine data from different storage systems
                        memory_data = {
                            "id": result["id"],
                            "content": result["payload"]["content"],
                            "metadata": result["payload"]["metadata"],
                            "similarity": result["score"]
                        }
                        
                        # Add relationship data if available
                        if graph_data and len(graph_data) > 0:
                            memory_data["relationships"] = graph_data[0].get("relationships", [])
                        
                        results.append(memory_data)
            
            # 4. If graph query specified, use graph DB
            elif "graph_query" in query:
                graph_results = await self.neo4j.query(query["graph_query"])
                
                # Process and format graph results
                for result in graph_results:
                    if "m" in result and result["m"].get("id"):
                        memory_id = result["m"]["id"]
                        
                        # Get vector data
                        vector_data = await self.qdrant.get(f"{memory_type}:{memory_id}")
                        if vector_data:
                            memory_data = {
                                "id": memory_id,
                                "content": vector_data["payload"]["content"],
                                "metadata": vector_data["payload"]["metadata"],
                                "relationships": result.get("relationships", [])
                            }
                            results.append(memory_data)
            
            logger.info(f"Retrieved {len(results)} memories from Qdrant.")
            return results
            
        except Exception as e:
            logger.error(f"retrieve_memory error: {e}")
            STORAGE_ERRORS.labels(operation=op).inc()
            self.metrics['errors'] += 1
            self.last_error = str(e)
            return []
    
    async def store_knowledge(self, knowledge_data: Dict[str, Any]) -> str:
        """
        Store knowledge node with automatic cross-referencing
        """
        try:
            # Generate ID if not provided
            knowledge_id = knowledge_data.get("id", f"k_{datetime.now().timestamp()}")
            knowledge_data["id"] = knowledge_id
            
            # 1. Store in vector DB for semantic search
            if "vector" in knowledge_data:
                vector = knowledge_data["vector"]
            else:
                # In real implementation, generate embedding from content
                vector = [0.0] * 512  # Placeholder
            
            await self.qdrant.upsert_vector(
                collection="knowledge",
                id=knowledge_id,
                vector=vector,
                payload={
                    "content": knowledge_data.get("content"),
                    "metadata": knowledge_data.get("metadata", {})
                }
            )
            self.metrics['vector_ops'] += 1
            
            # 2. Store in graph DB with proper labels
            node_id = await self.neo4j.add_node(
                label=["Knowledge", knowledge_data.get("knowledge_type", "Concept")],
                properties={
                    "id": knowledge_id,
                    "name": knowledge_data.get("name", ""),
                    "source": knowledge_data.get("source", "unknown"),
                    "confidence": knowledge_data.get("confidence", 1.0),
                    "created_at": knowledge_data.get("created_at", datetime.now().isoformat())
                }
            )
            self.metrics['graph_ops'] += 1
            
            # 3. Create relationships
            if "relationships" in knowledge_data:
                for relationship in knowledge_data["relationships"]:
                    await self.neo4j.add_relationship(
                        start_node=node_id,
                        end_node=relationship["target_id"],
                        relationship_type=relationship["type"],
                        properties=relationship.get("properties", {})
                    )
                    self.metrics['graph_ops'] += 1
            
            # 4. Store structured attributes in relational DB if needed
            if "attributes" in knowledge_data:
                for key, value in knowledge_data["attributes"].items():
                    await self.relational_db.set(f"knowledge_attribute:{knowledge_id}_{key}", {
                        "knowledge_id": knowledge_id,
                        "key": key,
                        "value": value,
                        "type": type(value).__name__
                    })
            
            return knowledge_id
            
        except Exception as e:
            logger.error(f"Error storing knowledge: {str(e)}")
            self.metrics['errors'] += 1
            return ""
    
    async def _setup_storage_schema(self):
        """Set up initial schema for storage systems"""
        # Set up vector collections
        await self.qdrant.create_collection("short_term")
        await self.qdrant.create_collection("long_term")
        await self.qdrant.create_collection("knowledge")
        
        # Set up relational tables
        await self.relational_db.create_table(
            "knowledge_attribute",
            {
                "id": "SERIAL PRIMARY KEY",
                "knowledge_id": "TEXT NOT NULL",
                "key": "TEXT NOT NULL",
                "value": "TEXT",
                "type": "TEXT"
            }
        )
        
        # Set up graph constraints and indices
        await self.neo4j.query("""
        CREATE CONSTRAINT memory_id IF NOT EXISTS 
        FOR (m:Memory) REQUIRE m.id IS UNIQUE
        """)
        
        await self.neo4j.query("""
        CREATE CONSTRAINT knowledge_id IF NOT EXISTS 
        FOR (k:Knowledge) REQUIRE k.id IS UNIQUE
        """)
        
        logger.info("Storage schema initialized")
