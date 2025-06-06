"""
Memory and Context Orchestrator Module

Provides a unified interface for memory and context sharing between SpaceNew components:
- Tools/Packages system
- RAG system
- AI Council

This module serves as a central orchestrator for memory and context management, enabling
seamless information flow between components.
"""

import logging
import json
import time
import threading
from typing import Dict, List, Any, Optional, Callable, Union, Set
from datetime import datetime
from enum import Enum
import uuid

logger = logging.getLogger(__name__)

class MemoryImportance(Enum):
    """Importance levels for memory entries"""
    LOW = 0.2
    MEDIUM = 0.5
    HIGH = 0.8
    CRITICAL = 1.0

class MemoryType(Enum):
    """Types of memory in the system"""
    FACTUAL = "factual"
    CONVERSATIONAL = "conversational"
    TOOL_EXECUTION = "tool_execution"
    USER_PREFERENCE = "user_preference"
    SYSTEM_STATE = "system_state"

class ContextScope(Enum):
    """Scopes for context sharing"""
    REQUEST = "request"       # Single request scope
    SESSION = "session"       # User session scope
    USER = "user"             # Persistent user scope
    GLOBAL = "global"         # Global system scope

class MemoryContextOrchestrator:
    """
    Orchestrates memory and context sharing between SpaceNew systems.
    
    Provides:
    1. Unified memory interfaces for short-term and long-term memory
    2. Context sharing with appropriate scoping
    3. Pub/sub mechanism for context updates
    4. Integration with RAG system and AI Council
    """
    
    def __init__(self):
        """Initialize the memory and context orchestrator."""
        self.rag_connector = None
        self.ai_council_connector = None
        
        # Memory stores
        self.short_term_memory: Dict[str, Dict[str, Any]] = {}
        self.short_term_expiration: Dict[str, float] = {}
        self.short_term_ttl = 3600  # 1 hour in seconds
        
        # Context stores (thread-safe)
        self.request_context = threading.local()
        self.session_context: Dict[str, Dict[str, Any]] = {}
        self.user_context: Dict[str, Dict[str, Any]] = {}
        self.global_context: Dict[str, Any] = {}
        
        # Subscription system
        self.subscribers: Dict[str, Set[Callable]] = {}
        
        # Metadata
        self.memory_metadata: Dict[str, Dict[str, Any]] = {}
    
    def connect_rag(self, rag_connector: Any) -> None:
        """
        Connect to the RAG system via its connector.
        
        Args:
            rag_connector: RAG system connector
        """
        self.rag_connector = rag_connector
        logger.info("Connected RAG system to memory orchestrator")
    
    def connect_ai_council(self, ai_council_connector: Any) -> None:
        """
        Connect to the AI Council via its connector.
        
        Args:
            ai_council_connector: AI Council connector
        """
        self.ai_council_connector = ai_council_connector
        logger.info("Connected AI Council to memory orchestrator")
    
    # Memory Management Functions
    
    def add_to_short_term_memory(self, 
                               memory_data: Union[str, Dict[str, Any]], 
                               metadata: Optional[Dict[str, Any]] = None,
                               memory_type: Optional[Union[str, MemoryType]] = None) -> str:
        """
        Add an entry to short-term memory.
        
        Args:
            memory_data: Memory data to store
            metadata: Additional metadata
            memory_type: Type of memory
            
        Returns:
            Memory ID
        """
        if metadata is None:
            metadata = {}
            
        # Convert MemoryType enum to string if needed
        if isinstance(memory_type, MemoryType):
            memory_type = memory_type.value
        
        # Generate memory ID
        memory_id = str(uuid.uuid4())
        
        # Structure the memory entry
        timestamp = time.time()
        memory_entry = {
            "data": memory_data,
            "timestamp": timestamp,
            "type": memory_type or MemoryType.FACTUAL.value,
            "metadata": metadata
        }
        
        # Store in short-term memory
        self.short_term_memory[memory_id] = memory_entry
        self.short_term_expiration[memory_id] = timestamp + self.short_term_ttl
        self.memory_metadata[memory_id] = metadata
        
        # Clean up expired entries
        self._cleanup_short_term_memory()
        
        return memory_id
    
    def add_to_long_term_memory(self, 
                              memory_data: Union[str, Dict[str, Any]], 
                              metadata: Optional[Dict[str, Any]] = None,
                              importance: float = MemoryImportance.MEDIUM.value,
                              memory_type: Optional[Union[str, MemoryType]] = None) -> bool:
        """
        Add an entry to long-term memory.
        
        Args:
            memory_data: Memory data to store
            metadata: Additional metadata
            importance: Importance of the memory (0-1)
            memory_type: Type of memory
            
        Returns:
            Whether the memory was successfully added
        """
        if metadata is None:
            metadata = {}
            
        # Convert MemoryType enum to string if needed
        if isinstance(memory_type, MemoryType):
            memory_type = memory_type.value
            
        if memory_type:
            metadata["type"] = memory_type
            
        metadata["importance"] = importance
        metadata["timestamp"] = datetime.now().isoformat()
        
        # First store in short-term memory
        self.add_to_short_term_memory(memory_data, metadata, memory_type)
        
        # Then store in long-term memory via RAG system if available
        if self.rag_connector:
            try:
                return self.rag_connector.add_to_memory(memory_data, metadata, importance)
            except Exception as e:
                logger.error(f"Error adding to long-term memory via RAG: {str(e)}")
                return False
                
        # Also store in AI Council if available and important enough
        if self.ai_council_connector and importance >= MemoryImportance.HIGH.value:
            try:
                memory_key = f"memory:{memory_type or 'unknown'}:{str(uuid.uuid4())}"
                return self.ai_council_connector.share_memory(
                    memory_key=memory_key,
                    memory_value=memory_data,
                    memory_type=memory_type or MemoryType.FACTUAL.value,
                    importance=importance
                )
            except Exception as e:
                logger.error(f"Error adding to AI Council memory: {str(e)}")
                
        return False
    
    def get_from_short_term_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a memory entry from short-term memory.
        
        Args:
            memory_id: Memory entry ID
            
        Returns:
            Memory entry or None if not found
        """
        # Clean up expired entries first
        self._cleanup_short_term_memory()
        
        # Check if memory exists and has not expired
        if memory_id in self.short_term_memory:
            if memory_id in self.short_term_expiration and time.time() < self.short_term_expiration[memory_id]:
                return self.short_term_memory[memory_id]
                
        return None
    
    def query_short_term_memory(self, 
                              query: Optional[str] = None,
                              memory_type: Optional[Union[str, MemoryType]] = None,
                              metadata_filter: Optional[Dict[str, Any]] = None,
                              max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Query short-term memory for entries matching criteria.
        
        Args:
            query: Optional text query
            memory_type: Filter by memory type
            metadata_filter: Additional metadata filters
            max_results: Maximum number of results
            
        Returns:
            List of matching memory entries
        """
        # Clean up expired entries first
        self._cleanup_short_term_memory()
        
        # Convert MemoryType enum to string if needed
        if isinstance(memory_type, MemoryType):
            memory_type = memory_type.value
            
        # Filter entries
        results = []
        
        for memory_id, entry in self.short_term_memory.items():
            # Skip expired entries
            if memory_id not in self.short_term_expiration or time.time() >= self.short_term_expiration[memory_id]:
                continue
                
            # Filter by type if specified
            if memory_type and entry.get("type") != memory_type:
                continue
                
            # Filter by metadata if specified
            if metadata_filter:
                entry_metadata = entry.get("metadata", {})
                if not all(entry_metadata.get(k) == v for k, v in metadata_filter.items()):
                    continue
            
            # Filter by query if specified
            if query:
                # Simple string matching for now
                entry_data = entry.get("data")
                if isinstance(entry_data, str):
                    if query.lower() not in entry_data.lower():
                        continue
                elif isinstance(entry_data, dict):
                    # Search in string values of the dict
                    found = False
                    for v in entry_data.values():
                        if isinstance(v, str) and query.lower() in v.lower():
                            found = True
                            break
                    if not found:
                        continue
            
            # Add to results
            results.append(entry)
            
            # Stop if we've reached max results
            if len(results) >= max_results:
                break
                
        # Sort by recency
        results.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        
        return results
    
    def query_long_term_memory(self, 
                             query: str,
                             memory_type: Optional[Union[str, MemoryType]] = None,
                             metadata_filter: Optional[Dict[str, Any]] = None,
                             max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Query long-term memory for entries matching criteria.
        
        Args:
            query: Text query
            memory_type: Filter by memory type
            metadata_filter: Additional metadata filters
            max_results: Maximum number of results
            
        Returns:
            List of matching memory entries
        """
        # Convert MemoryType enum to string if needed
        if isinstance(memory_type, MemoryType):
            memory_type = memory_type.value
            
        # Prepare filter
        filters = {}
        if memory_type:
            filters["type"] = memory_type
            
        if metadata_filter:
            filters.update(metadata_filter)
            
        # Query via RAG system if available
        if self.rag_connector:
            try:
                return self.rag_connector.retrieve_knowledge(
                    query=query, 
                    max_results=max_results,
                    min_relevance=0.7
                )
            except Exception as e:
                logger.error(f"Error querying long-term memory via RAG: {str(e)}")
                
        # Fall back to querying short-term memory
        return self.query_short_term_memory(
            query=query,
            memory_type=memory_type,
            metadata_filter=metadata_filter,
            max_results=max_results
        )
    
    def _cleanup_short_term_memory(self) -> None:
        """Clean up expired entries in short-term memory."""
        now = time.time()
        expired_ids = [
            memory_id 
            for memory_id, expiration_time in self.short_term_expiration.items() 
            if expiration_time < now
        ]
        
        for memory_id in expired_ids:
            if memory_id in self.short_term_memory:
                del self.short_term_memory[memory_id]
            if memory_id in self.short_term_expiration:
                del self.short_term_expiration[memory_id]
            if memory_id in self.memory_metadata:
                del self.memory_metadata[memory_id]
    
    # Context Management Functions
    
    def set_request_context(self, key: str, value: Any) -> None:
        """
        Set a value in the current request context.
        
        Args:
            key: Context key
            value: Context value
        """
        if not hasattr(self.request_context, "context"):
            self.request_context.context = {}
            
        self.request_context.context[key] = value
        
        # Notify subscribers
        self._notify_subscribers(ContextScope.REQUEST.value, key, value)
    
    def get_request_context(self, key: str, default: Any = None) -> Any:
        """
        Get a value from the current request context.
        
        Args:
            key: Context key
            default: Default value if not found
            
        Returns:
            Context value or default
        """
        if not hasattr(self.request_context, "context"):
            return default
            
        return self.request_context.context.get(key, default)
    
    def set_session_context(self, session_id: str, key: str, value: Any) -> None:
        """
        Set a value in the session context.
        
        Args:
            session_id: Session ID
            key: Context key
            value: Context value
        """
        if session_id not in self.session_context:
            self.session_context[session_id] = {}
            
        self.session_context[session_id][key] = value
        
        # Notify subscribers
        self._notify_subscribers(ContextScope.SESSION.value, key, value, session_id=session_id)
    
    def get_session_context(self, session_id: str, key: str, default: Any = None) -> Any:
        """
        Get a value from the session context.
        
        Args:
            session_id: Session ID
            key: Context key
            default: Default value if not found
            
        Returns:
            Context value or default
        """
        if session_id not in self.session_context:
            return default
            
        return self.session_context.get(session_id, {}).get(key, default)
    
    def set_user_context(self, user_id: str, key: str, value: Any) -> None:
        """
        Set a value in the user context.
        
        Args:
            user_id: User ID
            key: Context key
            value: Context value
        """
        if user_id not in self.user_context:
            self.user_context[user_id] = {}
            
        self.user_context[user_id][key] = value
        
        # Notify subscribers
        self._notify_subscribers(ContextScope.USER.value, key, value, user_id=user_id)
        
        # User context is also saved to long-term memory
        self.add_to_long_term_memory(
            memory_data={key: value},
            metadata={
                "user_id": user_id,
                "context_key": key
            },
            importance=MemoryImportance.HIGH.value,
            memory_type=MemoryType.USER_PREFERENCE
        )
    
    def get_user_context(self, user_id: str, key: str, default: Any = None) -> Any:
        """
        Get a value from the user context.
        
        Args:
            user_id: User ID
            key: Context key
            default: Default value if not found
            
        Returns:
            Context value or default
        """
        if user_id not in self.user_context:
            return default
            
        return self.user_context.get(user_id, {}).get(key, default)
    
    def set_global_context(self, key: str, value: Any) -> None:
        """
        Set a value in the global context.
        
        Args:
            key: Context key
            value: Context value
        """
        self.global_context[key] = value
        
        # Notify subscribers
        self._notify_subscribers(ContextScope.GLOBAL.value, key, value)
        
        # Global context is also saved to long-term memory
        self.add_to_long_term_memory(
            memory_data={key: value},
            metadata={"context_key": key},
            importance=MemoryImportance.HIGH.value,
            memory_type=MemoryType.SYSTEM_STATE
        )
    
    def get_global_context(self, key: str, default: Any = None) -> Any:
        """
        Get a value from the global context.
        
        Args:
            key: Context key
            default: Default value if not found
            
        Returns:
            Context value or default
        """
        return self.global_context.get(key, default)
    
    # Context Subscription Functions
    
    def subscribe(self, scope: Union[str, ContextScope], key: str, callback: Callable) -> None:
        """
        Subscribe to context updates.
        
        Args:
            scope: Context scope
            key: Context key
            callback: Callback function for updates
        """
        # Convert ContextScope enum to string if needed
        if isinstance(scope, ContextScope):
            scope = scope.value
            
        subscription_key = f"{scope}:{key}"
        
        if subscription_key not in self.subscribers:
            self.subscribers[subscription_key] = set()
            
        self.subscribers[subscription_key].add(callback)
    
    def unsubscribe(self, scope: Union[str, ContextScope], key: str, callback: Callable) -> None:
        """
        Unsubscribe from context updates.
        
        Args:
            scope: Context scope
            key: Context key
            callback: Callback function to unsubscribe
        """
        # Convert ContextScope enum to string if needed
        if isinstance(scope, ContextScope):
            scope = scope.value
            
        subscription_key = f"{scope}:{key}"
        
        if subscription_key in self.subscribers:
            if callback in self.subscribers[subscription_key]:
                self.subscribers[subscription_key].remove(callback)
    
    def _notify_subscribers(self, 
                          scope: str, 
                          key: str, 
                          value: Any, 
                          session_id: Optional[str] = None,
                          user_id: Optional[str] = None) -> None:
        """
        Notify subscribers of context updates.
        
        Args:
            scope: Context scope
            key: Context key
            value: New value
            session_id: Session ID if applicable
            user_id: User ID if applicable
        """
        subscription_key = f"{scope}:{key}"
        
        if subscription_key in self.subscribers:
            for callback in self.subscribers[subscription_key]:
                try:
                    callback(value, scope, key, session_id, user_id)
                except Exception as e:
                    logger.error(f"Error in context update callback: {str(e)}")
    
    # Context Sharing with RAG and AI Council
    
    def share_with_rag(self, 
                     data: Dict[str, Any],
                     importance: float = MemoryImportance.MEDIUM.value) -> bool:
        """
        Share context data with the RAG system.
        
        Args:
            data: Data to share
            importance: Importance of the data
            
        Returns:
            Whether the data was successfully shared
        """
        if self.rag_connector:
            try:
                return self.rag_connector.add_to_memory(data, {}, importance)
            except Exception as e:
                logger.error(f"Error sharing with RAG: {str(e)}")
                
        return False
    
    def share_with_ai_council(self, 
                            key: str,
                            data: Dict[str, Any],
                            memory_type: Optional[Union[str, MemoryType]] = None) -> bool:
        """
        Share context data with the AI Council.
        
        Args:
            key: Context key
            data: Data to share
            memory_type: Type of memory
            
        Returns:
            Whether the data was successfully shared
        """
        # Convert MemoryType enum to string if needed
        if isinstance(memory_type, MemoryType):
            memory_type = memory_type.value
            
        if self.ai_council_connector:
            try:
                return self.ai_council_connector.set_shared_context(key, data)
            except Exception as e:
                logger.error(f"Error sharing with AI Council via context: {str(e)}")
                
            try:
                return self.ai_council_connector.share_memory(
                    memory_key=key,
                    memory_value=data,
                    memory_type=memory_type or MemoryType.FACTUAL.value,
                    importance=MemoryImportance.MEDIUM.value
                )
            except Exception as e:
                logger.error(f"Error sharing with AI Council via memory: {str(e)}")
                
        return False
    
    # Utility Functions
    
    def get_consolidated_context(self, 
                               user_id: Optional[str] = None,
                               session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get consolidated context from all scopes.
        
        Args:
            user_id: User ID if applicable
            session_id: Session ID if applicable
            
        Returns:
            Consolidated context
        """
        # Start with global context
        consolidated = dict(self.global_context)
        
        # Add user context if available
        if user_id and user_id in self.user_context:
            consolidated.update(self.user_context[user_id])
            
        # Add session context if available
        if session_id and session_id in self.session_context:
            consolidated.update(self.session_context[session_id])
            
        # Add request context if available
        if hasattr(self.request_context, "context"):
            consolidated.update(self.request_context.context)
            
        return consolidated
    
    def clear_request_context(self) -> None:
        """Clear the current request context."""
        if hasattr(self.request_context, "context"):
            self.request_context.context = {}
    
    def clear_session_context(self, session_id: str) -> None:
        """Clear a session context."""
        if session_id in self.session_context:
            del self.session_context[session_id]
            
    def enrich_tool_context(self, 
                          context: Dict[str, Any],
                          user_id: Optional[str] = None,
                          session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Enrich tool execution context with memory and context data.
        
        Args:
            context: Current tool execution context
            user_id: User ID if applicable
            session_id: Session ID if applicable
            
        Returns:
            Enriched context
        """
        # Get consolidated context
        consolidated = self.get_consolidated_context(user_id, session_id)
        
        # Add to context without overwriting
        for key, value in consolidated.items():
            if key not in context:
                context[key] = value
                
        # If RAG connector is available, enrich with knowledge
        if self.rag_connector:
            context = self.rag_connector.enrich_context(context)
            
        return context
        
    def share_memory_with_ai_council(self, memory_key: str, memory_value: Any, 
                                    memory_type: MemoryType = None, 
                                    importance: float = 0.5) -> bool:
        """
        Share memory with AI Council.
        
        Args:
            memory_key: Key for the memory
            memory_value: Value for the memory
            memory_type: Type of memory
            importance: Importance score (0.0-1.0)
            
        Returns:
            Success flag
        """
        if self.ai_council_connector:
            return self.ai_council_connector.share_memory(
                memory_key=memory_key,
                memory_value=memory_value,
                memory_type=memory_type,
                importance=importance
            )
        return False
