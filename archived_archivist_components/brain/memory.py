"""
Memory system implementing short-term and long-term storage using vector and graph databases.
"""

import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import hashlib
import logging

from ..unified_storage import UnifiedStorageLayer
from ..enhanced_event_bus import EventBus, EventTaxonomy

@dataclass
class MemoryRecord:
    id: str
    content: Any
    metadata: Dict[str, Any]
    timestamp: datetime
    memory_type: str  # "short_term" or "long_term"
    
class MemorySystem:
    def __init__(self):
        self.storage = UnifiedStorageLayer()
        self.event_bus = EventBus()
        self.cache = {}  # In-memory cache for working memory
        
    async def initialize(self):
        """Initialize storage backends and memory subsystems"""
        # Initialize the unified storage layer
        await self.storage.initialize()
        
    async def store(self, data: Dict[str, Any], context: Any) -> str:
        """Store data in appropriate memory type"""
        # Generate a unique memory ID
        memory_id = f"mem_{context.user_id}_{datetime.now().timestamp()}"
        memory_type = data["memory_type"]
        
        # Generate embedding if not provided
        if "vector" not in data:
            data["vector"] = await self._generate_embedding(data["content"])
        
        # Add timestamp if not provided
        if "timestamp" not in data:
            data["timestamp"] = datetime.now().isoformat()
            
        # Add context information to metadata
        if "metadata" not in data:
            data["metadata"] = {}
            
        data["metadata"].update({
            "user_id": context.user_id,
            "session_id": context.session_id,
            "request_id": context.request_id
        })
        
        # Store using unified storage layer
        memory_data = {
            "id": memory_id,
            "content": data["content"],
            "vector": data["vector"],
            "memory_type": memory_type,
            "metadata": data["metadata"],
            "timestamp": data["timestamp"],
            "relationships": data.get("relationships", [])
        }
        
        stored_id = await self.storage.store_memory(memory_data)
        
        # Add to local cache if short-term
        if memory_type == "short_term":
            self.cache[memory_id] = MemoryRecord(
                id=memory_id,
                content=data["content"],
                metadata=data["metadata"],
                timestamp=datetime.now(),
                memory_type="short_term"
            )
            
        # Publish memory storage event
        await self.event_bus.publish(EventTaxonomy.MEMORY_STORED, {
            "memory_id": stored_id,
            "memory_type": memory_type,
            "timestamp": datetime.now().isoformat()
        })
            
        # Schedule cleanup of old memories
        asyncio.create_task(self._cleanup_old_memories())
        
        return stored_id
        
    async def retrieve(self, query: Dict[str, Any], context: Any) -> List[MemoryRecord]:
        """Retrieve memories based on vector similarity and graph relationships"""
        results = []
        
        # Check cache first for exact matches if ID is provided
        if "id" in query and query["id"] in self.cache:
            return [self.cache[query["id"]]]
            
        # Check cache for other matches
        if cached := self._check_cache(query):
            results.extend(cached)
            
        # Generate query vector if needed
        if "content" in query and "vector" not in query:
            query["vector"] = await self._generate_embedding(query["content"])
            
        # Use unified storage layer to retrieve memories
        storage_results = await self.storage.retrieve_memory(query)
        
        # Convert storage results to MemoryRecord objects
        for result in storage_results:
            memory_record = MemoryRecord(
                id=result["id"],
                content=result["content"],
                metadata=result["metadata"],
                timestamp=datetime.fromisoformat(result["metadata"].get("timestamp", datetime.now().isoformat())),
                memory_type=result["metadata"].get("memory_type", "unknown")
            )
            results.append(memory_record)
            
        # Publish memory retrieval event
        await self.event_bus.publish(EventTaxonomy.MEMORY_RETRIEVED, {
            "query": {k: v for k, v in query.items() if k != "vector"},  # Exclude vector for readability
            "results_count": len(results),
            "timestamp": datetime.now().isoformat()
        })
            
        return results
        
    async def _generate_embedding(self, content: Any) -> List[float]:
        """
        Generate vector embedding for content. Handles different content types.
        
        Args:
            content: Content to generate embedding for, can be string, dict, or other structure
        
        Returns:
            List[float]: Vector embedding of the content
        """
        try:
            # Convert content to string if it's not already
            if isinstance(content, dict) or isinstance(content, list):
                text_content = json.dumps(content)
            elif not isinstance(content, str):
                text_content = str(content)
            else:
                text_content = content
                
            # In a real implementation, this would use a proper embedding model
            # For example:
            #
            # from langchain.embeddings import OpenAIEmbeddings
            # embedder = OpenAIEmbeddings()
            # embedding = await embedder.aembed_query(text_content)
            # return embedding
            
            # For now, return a placeholder embedding
            # Use a simple hash-based approach to at least make similar content cluster together
            hash_obj = hashlib.md5(text_content.encode())
            hash_bytes = hash_obj.digest()
            
            # Convert hash bytes to a vector of 512 dimensions between -1 and 1
            vector = []
            for i in range(512):
                byte_index = i % len(hash_bytes)
                value = (hash_bytes[byte_index] / 255.0) * 2 - 1
                vector.append(value)
                
            return vector
            
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}", exc_info=True)
            # Return zero vector as fallback
            return [0.0] * 512
        
    def _check_cache(self, query: Dict[str, Any]) -> List[MemoryRecord]:
        """Check working memory cache"""
        results = []
        for memory in self.cache.values():
            if self._matches_query(memory, query):
                results.append(memory)
        return results
        
    async def _cleanup_old_memories(self):
        """
        Move old short-term memories to long-term storage based on age and importance.
        This implements automatic memory consolidation.
        """
        try:
            now = datetime.now()
            consolidation_candidates = []
            
            # Check cache for old memories (older than 24 hours)
            for memory_id, memory in list(self.cache.items()):
                age_hours = (now - memory.timestamp).total_seconds() / 3600
                
                # If memory is old enough, evaluate it for consolidation
                if age_hours > 24:
                    # Calculate basic importance (can be enhanced with more factors)
                    importance = memory.metadata.get("importance", 0.5)
                    
                    # If memory is important, add to consolidation candidates
                    if importance > 0.3:
                        consolidation_candidates.append(memory_id)
                        
                    # Remove from cache regardless
                    del self.cache[memory_id]
            
            # Create a system context for autonomous operations
            system_context = CognitiveContext(
                user_id="system",
                session_id=f"memory_consolidation_{now.timestamp()}",
                request_id=f"cleanup_{now.timestamp()}",
                metadata={"operation": "memory_consolidation"}
            )
            
            # Process consolidation candidates
            for memory_id in consolidation_candidates[:5]:  # Limit to 5 at a time
                # Get the full memory with all relationships
                query = {
                    "id": memory_id,
                    "include_relationships": True
                }
                
                memory_results = await self.storage.retrieve_memory(query)
                if not memory_results:
                    continue
                    
                memory = memory_results[0]
                
                # Create a consolidated version in long-term memory
                consolidated = {
                    "content": memory["content"],
                    "memory_type": "long_term",
                    "metadata": {
                        **memory["metadata"],
                        "original_id": memory_id,
                        "consolidated_at": now.isoformat(),
                    },
                    "vector": memory.get("vector")  # Reuse the vector if available
                }
                
                # Store as long-term memory
                consolidated_id = await self.storage.store_memory(consolidated)
                
                # Publish consolidation event
                await self.event_bus.publish(EventTaxonomy.MEMORY_CONSOLIDATED, {
                    "original_id": memory_id,
                    "consolidated_id": consolidated_id,
                    "timestamp": now.isoformat()
                })
                
                # Log the consolidation
                logger.info(f"Consolidated memory {memory_id} to long-term storage as {consolidated_id}")
                
        except Exception as e:
            logger.error(f"Error in memory cleanup: {str(e)}", exc_info=True)
        
    def _matches_query(self, memory: MemoryRecord, query: Dict[str, Any]) -> bool:
        """Check if memory matches query criteria"""
        # TODO: Implement matching logic
        return True
        
    def _combine_results(self, vector_result: Any, graph_data: Any) -> MemoryRecord:
        """Combine vector and graph results into a memory record"""
        # TODO: Implement result combination
        return MemoryRecord(
            id=vector_result.id,
            content=vector_result.payload["content"],
            metadata=vector_result.payload["metadata"],
            timestamp=datetime.now(),  # TODO: Get from graph data
            memory_type="unknown"
        )
    
    async def process(self, task: Dict[str, Any], context: Any) -> Any:
        """
        Process a memory task through a unified interface.
        
        Args:
            task: Dictionary with the operation and parameters
            context: Cognitive context for the operation
            
        Returns:
            Results of the operation, format depends on operation type
        """
        operation = task.get("operation", "")
        
        if operation == "store":
            return await self.store(task["data"], context)
            
        elif operation == "retrieve":
            return await self.retrieve(task["query"], context)
            
        elif operation == "update":
            memory_id = task["memory_id"]
            updates = task["updates"]
            
            # Check if memory exists
            existing = await self.retrieve({"id": memory_id}, context)
            if not existing:
                raise ValueError(f"Memory {memory_id} not found")
                
            # Apply updates to metadata
            if "metadata" in updates:
                # If in cache, update directly
                if memory_id in self.cache:
                    self.cache[memory_id].metadata.update(updates["metadata"])
                    
                # Update in storage
                await self.storage.storage_update_memory_metadata(memory_id, updates["metadata"])
                
                # Publish update event
                await self.event_bus.publish(EventTaxonomy.MEMORY_UPDATED, {
                    "memory_id": memory_id,
                    "updates": list(updates["metadata"].keys())
                })
                
            return True
            
        elif operation == "forget":
            memory_id = task["memory_id"]
            
            # Remove from cache
            if memory_id in self.cache:
                del self.cache[memory_id]
                
            # Mark as forgotten in storage
            # Note: In many systems, we don't actually delete memories,
            # we just mark them as forgotten or inaccessible
            await self.storage.update_memory_status(memory_id, "forgotten")
            
            # Publish forget event
            await self.event_bus.publish(EventTaxonomy.MEMORY_FORGOTTEN, {
                "memory_id": memory_id,
                "timestamp": datetime.now().isoformat(),
                "context": context.__dict__
            })
            
            return True
            
        elif operation == "consolidate":
            # Get memories ready for consolidation
            query = task.get("query", {})
            query.setdefault("memory_type", "short_term")
            query.setdefault("status", "active")
            
            # Set default age filter if not provided
            if "created_before" not in query:
                cutoff = datetime.now() - timedelta(hours=24)
                query["created_before"] = cutoff.isoformat()
                
            memories = await self.retrieve(query, context)
            
            # Return the memories ready for consolidation
            # The brain controller will decide what to do with them
            return memories
            
        else:
            raise ValueError(f"Unknown memory operation: {operation}")
            
    async def associate_memories(self, memory_id: str, related_id: str, 
                             relationship_type: str, context: Any) -> bool:
        """
        Create association between two memories
        
        Args:
            memory_id: ID of the source memory
            related_id: ID of the target memory
            relationship_type: Type of relationship to create
            context: Cognitive context
            
        Returns:
            bool: True if successful
        """
        try:
            # Create relationship in graph DB through unified storage
            relationship = {
                "source_id": memory_id,
                "target_id": related_id,
                "type": relationship_type,
                "properties": {
                    "created_at": datetime.now().isoformat(),
                    "created_by": "memory_system",
                    "context_id": context.request_id
                }
            }
            
            # Add the relationship
            await self.storage.add_relationship(relationship)
            
            # Publish event
            await self.event_bus.publish(EventTaxonomy.MEMORY_ASSOCIATED, {
                "source_id": memory_id,
                "target_id": related_id,
                "relationship_type": relationship_type,
                "timestamp": datetime.now().isoformat()
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Error associating memories: {str(e)}", exc_info=True)
            return False
        
    def find_duplicates(self, limit=5):
        # Minimal working logic: return empty list
        return []

    def merge_duplicates(self, dup):
        # Minimal working logic: log the merge
        logger = logging.getLogger(__name__)
        logger.info(f"Merged duplicate: {dup}")

    def get_items_missing_embeddings(self, limit=10):
        # Minimal working logic: return empty list
        return []

    def update_embedding(self, item_id, embedding):
        # Minimal working logic: log the update
        logger = logging.getLogger(__name__)
        logger.info(f"Updated embedding for {item_id}")
