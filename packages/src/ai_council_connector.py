"""
AI Council Connector Module
Provides a direct integration between the tool system and AI Council components
"""

import logging
import json
from typing import Dict, List, Any, Optional, Callable, Union
import threading
import time
from datetime import datetime

logger = logging.getLogger(__name__)

class AICouncilConnector:
    """
    Connects tools with the AI Council system for orchestration and memory sharing.
    
    Provides:
    1. Registration of tools as AI Council capabilities
    2. Shared context management between tools and specialists
    3. Tool execution from AI Council requests
    """
    
    def __init__(self, ai_council=None):
        """
        Initialize the AI Council connector.
        
        Args:
            ai_council: The AI Council instance (optional, can be connected later)
        """
        self.ai_council = ai_council
        self.local_context = threading.local()
        self.capability_handlers = {}
        self.memory_cache = {}
        self.cache_expiration = {}
        self.cache_ttl = 3600  # 1 hour in seconds
    
    def connect(self, ai_council: Any) -> None:
        """
        Connect to the AI Council instance.
        
        Args:
            ai_council: The AI Council instance
        """
        self.ai_council = ai_council
        logger.info("Connected to AI Council")
    
    def register_capability(self, 
                           capability_id: str, 
                           description: str, 
                           handler_fn: Callable,
                           parameters: Optional[Dict[str, Any]] = None,
                           required_permissions: Optional[List[str]] = None) -> None:
        """
        Register a capability with the AI Council.
        
        Args:
            capability_id: Unique ID for the capability
            description: Description of the capability
            handler_fn: Function to handle capability execution
            parameters: Parameter schema for the capability
            required_permissions: Permissions required to use the capability
        """
        if not self.ai_council:
            logger.warning(f"Cannot register capability {capability_id}: AI Council not connected")
            # Store locally to register later when connected
            self.capability_handlers[capability_id] = {
                "handler": handler_fn,
                "description": description,
                "parameters": parameters or {},
                "required_permissions": required_permissions or []
            }
            return
        
        try:
            # Register with AI Council if it has the appropriate method
            if hasattr(self.ai_council, "register_capability"):
                self.ai_council.register_capability(
                    capability_id=capability_id,
                    capability_info={
                        "description": description,
                        "parameters": parameters or {},
                        "required_permissions": required_permissions or [],
                    },
                    handler_fn=handler_fn
                )
                logger.info(f"Registered capability with AI Council: {capability_id}")
            else:
                # Fall back to local registration
                self.capability_handlers[capability_id] = {
                    "handler": handler_fn,
                    "description": description,
                    "parameters": parameters or {},
                    "required_permissions": required_permissions or []
                }
                logger.warning(f"AI Council lacks register_capability method, stored locally: {capability_id}")
        except Exception as e:
            logger.error(f"Error registering capability {capability_id}: {str(e)}")
    
    def get_shared_context(self, context_key: Optional[str] = None) -> Any:
        """
        Get shared context from AI Council.
        
        Args:
            context_key: Specific context key to retrieve (optional)
            
        Returns:
            Shared context data
        """
        if not self.ai_council:
            logger.warning("Cannot get shared context: AI Council not connected")
            return self._get_local_context(context_key)
        
        try:
            # Get from AI Council if it has shared context
            if hasattr(self.ai_council, "shared_context"):
                if context_key:
                    return self.ai_council.shared_context.get(context_key)
                else:
                    # Get all context
                    return self.ai_council.shared_context.get_all()
            else:
                # Fall back to local context
                return self._get_local_context(context_key)
                
        except Exception as e:
            logger.error(f"Error getting shared context: {str(e)}")
            return self._get_local_context(context_key)
    
    def _get_local_context(self, context_key: Optional[str] = None) -> Any:
        """Get context from thread-local storage."""
        if not hasattr(self.local_context, "context"):
            self.local_context.context = {}
            
        if context_key:
            return self.local_context.context.get(context_key)
        else:
            return self.local_context.context
    
    def set_shared_context(self, context_key: str, context_value: Any) -> bool:
        """
        Set shared context for AI Council.
        
        Args:
            context_key: Context key to set
            context_value: Value to set
            
        Returns:
            Whether the context was successfully set
        """
        if not self.ai_council:
            logger.warning("Cannot set shared context: AI Council not connected")
            return self._set_local_context(context_key, context_value)
        
        try:
            # Set in AI Council if it has shared context
            if hasattr(self.ai_council, "shared_context"):
                self.ai_council.shared_context.set(context_key, context_value)
                
                # Also update local context for redundancy
                self._set_local_context(context_key, context_value)
                return True
            else:
                # Fall back to local context
                return self._set_local_context(context_key, context_value)
                
        except Exception as e:
            logger.error(f"Error setting shared context: {str(e)}")
            return self._set_local_context(context_key, context_value)
    
    def _set_local_context(self, context_key: str, context_value: Any) -> bool:
        """Set context in thread-local storage."""
        if not hasattr(self.local_context, "context"):
            self.local_context.context = {}
            
        self.local_context.context[context_key] = context_value
        return True
    
    def share_memory(self, 
                    memory_key: str, 
                    memory_value: Any,
                    memory_type: str = "tool_execution",
                    importance: float = 0.5) -> bool:
        """
        Share memory with AI Council.
        
        Args:
            memory_key: Key for the memory
            memory_value: Memory value to share
            memory_type: Type of memory
            importance: Importance of the memory (0-1)
            
        Returns:
            Whether the memory was successfully shared
        """
        if not self.ai_council:
            logger.warning(f"Cannot share memory {memory_key}: AI Council not connected")
            return self._cache_memory(memory_key, memory_value, memory_type, importance)
        
        try:
            # Structure memory data
            memory_data = {
                "key": memory_key,
                "value": memory_value,
                "type": memory_type,
                "importance": importance,
                "timestamp": datetime.now().isoformat()
            }
            
            # Share with AI Council memory manager if available
            if hasattr(self.ai_council, "memory_manager"):
                self.ai_council.memory_manager.store(
                    key=memory_key,
                    value=memory_value,
                    metadata={
                        "type": memory_type,
                        "importance": importance
                    }
                )
                return True
                
            # Otherwise try to use shared context
            elif hasattr(self.ai_council, "shared_context"):
                context_key = f"memory:{memory_type}:{memory_key}"
                self.ai_council.shared_context.set(context_key, memory_data)
                return True
                
            else:
                # Fall back to local memory cache
                return self._cache_memory(memory_key, memory_value, memory_type, importance)
                
        except Exception as e:
            logger.error(f"Error sharing memory: {str(e)}")
            return self._cache_memory(memory_key, memory_value, memory_type, importance)
    
    def _cache_memory(self, key: str, value: Any, memory_type: str, importance: float) -> bool:
        """Cache memory locally if AI Council is not available."""
        cache_key = f"{memory_type}:{key}"
        self.memory_cache[cache_key] = {
            "value": value,
            "importance": importance,
            "timestamp": datetime.now().isoformat()
        }
        
        # Set expiration time
        self.cache_expiration[cache_key] = time.time() + self.cache_ttl
        
        # Clean up expired cache entries
        self._cleanup_cache()
        
        return True
    
    def _cleanup_cache(self) -> None:
        """Clean up expired cache entries."""
        now = time.time()
        expired_keys = [k for k, exp_time in self.cache_expiration.items() if exp_time < now]
        
        for key in expired_keys:
            if key in self.memory_cache:
                del self.memory_cache[key]
            if key in self.cache_expiration:
                del self.cache_expiration[key]
    
    def retrieve_memory(self, memory_key: str, memory_type: str = "tool_execution") -> Any:
        """
        Retrieve memory from AI Council.
        
        Args:
            memory_key: Key for the memory to retrieve
            memory_type: Type of memory
            
        Returns:
            Retrieved memory value or None if not found
        """
        if not self.ai_council:
            logger.warning(f"Cannot retrieve memory {memory_key}: AI Council not connected")
            return self._retrieve_cached_memory(memory_key, memory_type)
        
        try:
            # Try to get from AI Council memory manager if available
            if hasattr(self.ai_council, "memory_manager"):
                result = self.ai_council.memory_manager.retrieve(memory_key)
                if result:
                    return result.get("value")
                    
            # Otherwise try to use shared context
            elif hasattr(self.ai_council, "shared_context"):
                context_key = f"memory:{memory_type}:{memory_key}"
                result = self.ai_council.shared_context.get(context_key)
                if result:
                    return result.get("value")
                    
            # Fall back to local memory cache
            return self._retrieve_cached_memory(memory_key, memory_type)
                
        except Exception as e:
            logger.error(f"Error retrieving memory: {str(e)}")
            return self._retrieve_cached_memory(memory_key, memory_type)
    
    def _retrieve_cached_memory(self, key: str, memory_type: str) -> Any:
        """Retrieve memory from local cache."""
        cache_key = f"{memory_type}:{key}"
        
        # Check if the key exists and is not expired
        if cache_key in self.memory_cache:
            # Check expiration
            if cache_key in self.cache_expiration and time.time() < self.cache_expiration[cache_key]:
                return self.memory_cache[cache_key].get("value")
                
        return None
    
    def execute_capability(self, capability_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a registered capability.
        
        Args:
            capability_id: ID of the capability to execute
            params: Parameters for capability execution
            
        Returns:
            Capability execution result
        """
        # Check locally registered handlers first
        if capability_id in self.capability_handlers:
            try:
                handler = self.capability_handlers[capability_id]["handler"]
                result = handler(params)
                return {
                    "success": True,
                    "result": result,
                    "error": None
                }
            except Exception as e:
                logger.error(f"Error executing locally registered capability {capability_id}: {str(e)}")
                return {
                    "success": False,
                    "result": None,
                    "error": str(e)
                }
        
        # If not found locally and AI Council is connected, try there
        if self.ai_council and hasattr(self.ai_council, "execute_capability"):
            try:
                return self.ai_council.execute_capability(capability_id, params)
            except Exception as e:
                logger.error(f"Error executing AI Council capability {capability_id}: {str(e)}")
                return {
                    "success": False,
                    "result": None,
                    "error": str(e)
                }
                
        # Not found
        logger.warning(f"Capability not found: {capability_id}")
        return {
            "success": False,
            "result": None,
            "error": f"Capability not found: {capability_id}"
        }
