"""
RAG System Connector Module
Provides direct integration between the tool system and RAG components
for context enrichment and knowledge sharing.
"""

import logging
import json
from typing import Dict, List, Any, Optional, Callable, Union
import time
import threading
from datetime import datetime

logger = logging.getLogger(__name__)

class RAGConnector:
    """
    Connects tools with the RAG system for knowledge integration and context enrichment.
    
    Provides:
    1. Knowledge retrieval from RAG system for tool execution
    2. Feeding tool execution results back to the RAG system's memory
    3. Context-aware tool execution based on RAG knowledge
    """
    
    def __init__(self, rag_system=None):
        """
        Initialize the RAG connector.
        
        Args:
            rag_system: The RAG system instance (optional, can be connected later)
        """
        self.rag_system = rag_system
        self.local_context = threading.local()
        self.registered_retrievers = {}
        self.knowledge_cache = {}
        self.cache_expiration = {}
        self.cache_ttl = 600  # 10 minutes in seconds
    
    def connect(self, rag_system: Any) -> None:
        """
        Connect to the RAG system instance.
        
        Args:
            rag_system: The RAG system instance
        """
        self.rag_system = rag_system
        logger.info("Connected to RAG system")
    
    def register_retriever(self, 
                         retriever_id: str,
                         retriever_fn: Callable,
                         description: str) -> None:
        """
        Register a knowledge retriever function.
        
        Args:
            retriever_id: Unique ID for the retriever
            retriever_fn: Function to retrieve knowledge
            description: Description of the retriever
        """
        self.registered_retrievers[retriever_id] = {
            "function": retriever_fn,
            "description": description
        }
        logger.info(f"Registered knowledge retriever: {retriever_id}")
    
    def retrieve_knowledge(self, 
                         query: str,
                         retriever_id: Optional[str] = None,
                         max_results: int = 5,
                         min_relevance: float = 0.7) -> List[Dict[str, Any]]:
        """
        Retrieve knowledge from the RAG system.
        
        Args:
            query: Query string for knowledge retrieval
            retriever_id: Specific retriever to use (optional)
            max_results: Maximum number of results to return
            min_relevance: Minimum relevance score for results
            
        Returns:
            List of knowledge chunks
        """
        if not self.rag_system:
            logger.warning("Cannot retrieve knowledge: RAG system not connected")
            return self._retrieve_from_cache(query)
        
        try:
            # If a specific retriever is specified, use that
            if retriever_id and retriever_id in self.registered_retrievers:
                retriever_fn = self.registered_retrievers[retriever_id]["function"]
                results = retriever_fn(query, max_results=max_results)
                
            # Otherwise use the RAG system's retrieval interface
            elif hasattr(self.rag_system, "retrieve"):
                results = self.rag_system.retrieve(
                    query=query,
                    max_results=max_results,
                    min_relevance=min_relevance
                )
                
            # Or try the query interface
            elif hasattr(self.rag_system, "query"):
                results = self.rag_system.query(
                    query_text=query,
                    max_results=max_results,
                    retrieval_options={
                        "min_relevance": min_relevance
                    }
                )
            else:
                logger.warning("RAG system does not have retrieve or query method")
                return self._retrieve_from_cache(query)
            
            # Cache the results
            self._cache_results(query, results)
            
            return results
            
        except Exception as e:
            logger.error(f"Error retrieving knowledge: {str(e)}")
            return self._retrieve_from_cache(query)
    
    def _retrieve_from_cache(self, query: str) -> List[Dict[str, Any]]:
        """Get knowledge from local cache."""
        # Simple keyword matching for cache hits
        cache_hits = []
        
        # Clean up expired cache entries first
        self._cleanup_cache()
        
        # Try to find matching cached entries
        query_terms = set(query.lower().split())
        for cached_query, data in self.knowledge_cache.items():
            cached_terms = set(cached_query.lower().split())
            # If there's significant term overlap, use this cache entry
            if len(query_terms.intersection(cached_terms)) / len(query_terms) > 0.6:
                if cached_query in self.cache_expiration and time.time() < self.cache_expiration[cached_query]:
                    cache_hits.append(data)
        
        # Return most recent cache hit if any exist
        if cache_hits:
            return sorted(cache_hits, key=lambda x: x.get("timestamp", 0), reverse=True)[0].get("results", [])
        
        return []
    
    def _cache_results(self, query: str, results: List[Dict[str, Any]]) -> None:
        """Cache knowledge retrieval results."""
        self.knowledge_cache[query] = {
            "results": results,
            "timestamp": time.time()
        }
        
        # Set expiration time
        self.cache_expiration[query] = time.time() + self.cache_ttl
    
    def _cleanup_cache(self) -> None:
        """Clean up expired cache entries."""
        now = time.time()
        expired_keys = [k for k, exp_time in self.cache_expiration.items() if exp_time < now]
        
        for key in expired_keys:
            if key in self.knowledge_cache:
                del self.knowledge_cache[key]
            if key in self.cache_expiration:
                del self.cache_expiration[key]
    
    def add_to_memory(self, 
                     content: Union[str, Dict[str, Any]], 
                     metadata: Optional[Dict[str, Any]] = None,
                     importance: float = 0.5) -> bool:
        """
        Add content to the RAG system's memory.
        
        Args:
            content: Content to add to memory
            metadata: Metadata about the content
            importance: Importance of the memory (0-1)
            
        Returns:
            Whether the memory was successfully added
        """
        if not self.rag_system:
            logger.warning("Cannot add to memory: RAG system not connected")
            return False
        
        if metadata is None:
            metadata = {}
        
        try:
            # Try different interfaces that the RAG system might have
            
            # Memory orchestrator interface
            if hasattr(self.rag_system, "memory_orchestrator"):
                if importance >= 0.7:
                    self.rag_system.memory_orchestrator.add_to_long_term_memory(content, metadata, importance)
                else:
                    self.rag_system.memory_orchestrator.add_to_short_term_memory(content, metadata)
                return True
                
            # Direct memory interface
            elif hasattr(self.rag_system, "add_to_memory"):
                self.rag_system.add_to_memory(content, metadata, importance=importance)
                return True
                
            # Knowledge base interface
            elif hasattr(self.rag_system, "add_document"):
                # Convert content to document format if it's not already
                if isinstance(content, str):
                    document = {
                        "content": content,
                        "metadata": metadata,
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    document = content
                    if "metadata" not in document:
                        document["metadata"] = metadata
                
                self.rag_system.add_document(document)
                return True
                
            else:
                logger.warning("RAG system does not have a memory or document interface")
                return False
                
        except Exception as e:
            logger.error(f"Error adding to memory: {str(e)}")
            return False
    
    def enrich_context(self, 
                     context: Dict[str, Any],
                     query: Optional[str] = None) -> Dict[str, Any]:
        """
        Enrich execution context with knowledge from the RAG system.
        
        Args:
            context: Current execution context
            query: Optional query to use for knowledge retrieval
            
        Returns:
            Enriched context
        """
        if not query:
            # Try to construct a query from context
            if "tool_id" in context and "parameters" in context:
                tool_id = context["tool_id"]
                params = context["parameters"]
                
                # Create a query based on tool and parameters
                param_str = " ".join([f"{k}: {v}" for k, v in params.items() if isinstance(v, (str, int, float, bool))])
                query = f"Tool {tool_id} execution with parameters: {param_str}"
        
        if query:
            # Retrieve knowledge based on the query
            knowledge = self.retrieve_knowledge(query)
            
            # Add knowledge to context
            if knowledge:
                context["knowledge"] = knowledge
        
        return context
    
    def register_with_rag(self, 
                         tool_id: str,
                         tool_description: str,
                         tool_parameters: Dict[str, Any]) -> bool:
        """
        Register a tool with the RAG system so it can be used in RAG processes.
        
        Args:
            tool_id: ID of the tool
            tool_description: Description of the tool
            tool_parameters: Parameter schema for the tool
            
        Returns:
            Whether the tool was successfully registered
        """
        if not self.rag_system:
            logger.warning(f"Cannot register tool {tool_id}: RAG system not connected")
            return False
        
        try:
            # Check if RAG system can register tools
            if hasattr(self.rag_system, "register_tool"):
                self.rag_system.register_tool(
                    tool_id=tool_id,
                    description=tool_description,
                    parameters=tool_parameters
                )
                logger.info(f"Registered tool with RAG system: {tool_id}")
                return True
                
            # Try alternative method
            elif hasattr(self.rag_system, "add_agent_capability"):
                self.rag_system.add_agent_capability(
                    capability_id=f"tool:{tool_id}",
                    capability_info={
                        "name": tool_id,
                        "description": tool_description,
                        "parameters": tool_parameters,
                    }
                )
                logger.info(f"Registered capability with RAG system: {tool_id}")
                return True
                
            else:
                logger.warning("RAG system does not support tool registration")
                return False
                
        except Exception as e:
            logger.error(f"Error registering tool with RAG system: {str(e)}")
            return False
