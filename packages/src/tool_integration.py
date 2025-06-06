"""
Tool Integration Module
Provides integration between the tool system and other core SpaceNew components
including the RAG system and AI Council.
"""

import logging
import json
from typing import Dict, List, Any, Optional, Callable, Type, Union
import inspect

# Import from tool system
from .tools_system import ToolsSystem
from .schemas import ToolExecutionRequest, ToolExecutionResponse

# RAG system would normally be imported here
# from core.rag_system.rag_system import RAGSystem

logger = logging.getLogger(__name__)

class ToolIntegration:
    """
    Integrates the tool system with other core components like RAG and AI Council.
    
    Provides:
    1. Tool discovery and execution from the RAG system
    2. Tool registration with AI Council
    3. Memory and context sharing between tools and other systems
    """
    
    def __init__(self, tools_system: ToolsSystem):
        """
        Initialize the tool integration.
        
        Args:
            tools_system: The core tools system
        """
        self.tools_system = tools_system
        self.rag_system = None
        self.ai_council = None
        self.registered_handlers = {}
        
    def connect_rag_system(self, rag_system: Any) -> None:
        """
        Connect to the RAG system for knowledge access.
        
        Args:
            rag_system: The RAG system instance
        """
        self.rag_system = rag_system
        logger.info("Connected RAG system to tools")
        
        # Register handlers for RAG-to-Tool interactions
        if hasattr(rag_system, 'register_tool_handler'):
            rag_system.register_tool_handler(
                handler_name="execute_tool",
                handler_fn=self.handle_rag_tool_request
            )
            
    def connect_ai_council(self, ai_council: Any) -> None:
        """
        Connect to the AI Council for agent orchestration.
        
        Args:
            ai_council: The AI Council instance
        """
        self.ai_council = ai_council
        logger.info("Connected AI Council to tools")
        
        # Register tools with AI Council
        if hasattr(ai_council, 'register_capability'):
            # Register each tool as a capability
            for tool_id, tool in self.tools_system.list_tools().items():
                ai_council.register_capability(
                    capability_id=f"tool:{tool_id}",
                    capability_info={
                        "name": tool.manifest.name,
                        "description": tool.manifest.description,
                        "parameters": tool.manifest.parameters,
                        "required_permissions": tool.manifest.required_permissions,
                        "type": "tool"
                    },
                    handler_fn=lambda params, tool_id=tool_id: self.handle_council_tool_request(tool_id, params)
                )
    
    def handle_rag_tool_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle tool execution requests from RAG system.
        
        Args:
            request: Tool execution request from RAG
            
        Returns:
            Tool execution result
        """
        logger.info(f"Handling RAG tool request: {request.get('tool_id')}")
        
        try:
            # Convert to tool execution request
            tool_request = ToolExecutionRequest(
                tool_id=request.get("tool_id"),
                parameters=request.get("parameters", {}),
                request_id=request.get("request_id", ""),
                mode=request.get("mode", "standard"),
                user_id=request.get("user_id", "")
            )
            
            # Execute the tool
            result = self.tools_system.execute_tool(tool_request)
            
            # Return the result
            return {
                "success": result.success,
                "result": result.result,
                "error": result.error
            }
            
        except Exception as e:
            logger.error(f"Error handling RAG tool request: {str(e)}")
            return {
                "success": False,
                "result": None,
                "error": f"Tool execution error: {str(e)}"
            }
    
    def handle_council_tool_request(self, tool_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle tool execution requests from AI Council.
        
        Args:
            tool_id: ID of the tool to execute
            params: Parameters for tool execution
            
        Returns:
            Tool execution result
        """
        logger.info(f"Handling AI Council tool request: {tool_id}")
        
        try:
            # Get AI Council context from thread-local storage or params
            context = params.pop("_context", {}) if isinstance(params, dict) else {}
            
            # Create tool execution request
            tool_request = ToolExecutionRequest(
                tool_id=tool_id,
                parameters=params,
                request_id=context.get("request_id", ""),
                mode=context.get("mode", "standard"),
                user_id=context.get("user_id", "")
            )
            
            # Execute the tool
            result = self.tools_system.execute_tool(tool_request)
            
            # Return the result
            return {
                "success": result.success,
                "result": result.result,
                "error": result.error,
                "metadata": result.metadata
            }
            
        except Exception as e:
            logger.error(f"Error handling AI Council tool request: {str(e)}")
            return {
                "success": False,
                "result": None,
                "error": f"Tool execution error: {str(e)}",
                "metadata": {}
            }
    
    def register_context_provider(self, provider_name: str, provider_fn: Callable) -> None:
        """
        Register a function that provides context data to tools.
        
        Args:
            provider_name: Name of the context provider
            provider_fn: Function that returns context data
        """
        self.registered_handlers[provider_name] = provider_fn
        logger.info(f"Registered context provider: {provider_name}")
    
    def get_context(self, context_type: str, **kwargs) -> Dict[str, Any]:
        """
        Get context data from registered providers.
        
        Args:
            context_type: Type of context to retrieve
            **kwargs: Additional parameters for context retrieval
            
        Returns:
            Context data
        """
        provider = self.registered_handlers.get(context_type)
        if provider:
            try:
                return provider(**kwargs)
            except Exception as e:
                logger.error(f"Error getting context from {context_type}: {str(e)}")
                return {}
        else:
            logger.warning(f"No context provider registered for {context_type}")
            return {}
    
    def register_rag_tools(self) -> None:
        """
        Register RAG-specific tools with the tool system.
        """
        if not self.rag_system:
            logger.warning("Cannot register RAG tools: RAG system not connected")
            return
            
        # RAG tools would be registered here
        # Example:
        # self.tools_system.register_tool(...)
    
    def register_ai_council_tools(self) -> None:
        """
        Register AI Council-specific tools with the tool system.
        """
        if not self.ai_council:
            logger.warning("Cannot register AI Council tools: AI Council not connected")
            return
            
        # AI Council tools would be registered here
        # Example:
        # self.tools_system.register_tool(...)

    def share_memory_with_rag(self, memory_data: Dict[str, Any]) -> bool:
        """
        Share tool execution memory/context with the RAG system.
        
        Args:
            memory_data: Memory data to share
            
        Returns:
            Whether the memory was successfully shared
        """
        if not self.rag_system:
            logger.warning("Cannot share memory with RAG: RAG system not connected")
            return False
            
        try:
            # Check if RAG system has a memory orchestrator
            if hasattr(self.rag_system, 'memory_orchestrator'):
                # Add to short-term memory
                importance = memory_data.get("importance", 0.5)
                
                if importance >= 0.7:
                    # Important memories go to long-term
                    self.rag_system.memory_orchestrator.add_to_long_term_memory(memory_data, importance)
                else:
                    # Less important memories go to short-term
                    self.rag_system.memory_orchestrator.add_to_short_term_memory(memory_data)
                    
                return True
            else:
                logger.warning("RAG system does not have memory orchestrator")
                return False
                
        except Exception as e:
            logger.error(f"Error sharing memory with RAG: {str(e)}")
            return False
    
    def share_memory_with_ai_council(self, memory_data: Dict[str, Any]) -> bool:
        """
        Share tool execution memory/context with the AI Council.
        
        Args:
            memory_data: Memory data to share
            
        Returns:
            Whether the memory was successfully shared
        """
        if not self.ai_council:
            logger.warning("Cannot share memory with AI Council: AI Council not connected")
            return False
            
        try:
            # Check if AI Council has a shared context
            if hasattr(self.ai_council, 'shared_context'):
                context_key = f"tool_memory:{memory_data.get('tool_id', 'unknown')}"
                
                # Add to shared context
                self.ai_council.shared_context.set(context_key, memory_data)
                return True
            else:
                logger.warning("AI Council does not have shared context")
                return False
                
        except Exception as e:
            logger.error(f"Error sharing memory with AI Council: {str(e)}")
            return False
