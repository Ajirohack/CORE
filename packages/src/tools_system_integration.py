"""
Tools System Integration Module

Integrates the core tools system with other SpaceNew components:
- RAG system
- AI Council
- Memory/Context management

This module provides a unified interface for the tools system, making it easy to
connect tools with other components of the SpaceNew architecture.
"""

import logging
from typing import Dict, List, Any, Optional, Callable, Type, Union

from .tools_system import ToolsSystem, ToolAccessLevel
from .tool_registry import ToolRegistry
from .tool_executor import ToolExecutor
from .schemas import ToolManifest, ToolExecutionRequest, ToolExecutionResponse

from .tool_integration import ToolIntegration
from .ai_council_connector import AICouncilConnector
from .rag_connector import RAGConnector
from .memory_context_orchestrator import MemoryContextOrchestrator, MemoryType, ContextScope

logger = logging.getLogger(__name__)

class IntegratedToolsSystem:
    """
    Integrated tools system with connections to other SpaceNew components.
    
    Provides:
    1. Core tool registration and execution
    2. Integration with RAG system
    3. Integration with AI Council
    4. Memory and context sharing
    """
    
    def __init__(self, 
               tool_registry: Optional[ToolRegistry] = None,
               tool_executor: Optional[ToolExecutor] = None):
        """
        Initialize the integrated tools system.
        
        Args:
            tool_registry: Optional existing tool registry
            tool_executor: Optional existing tool executor
        """
        # Create core tools system
        self.tools_system = ToolsSystem()
        
        # Create integration components
        self.tool_integration = ToolIntegration(self.tools_system)
        self.ai_council_connector = AICouncilConnector()
        self.rag_connector = RAGConnector()
        self.memory_context_orchestrator = MemoryContextOrchestrator()
        
        # Connect components
        self.memory_context_orchestrator.connect_rag(self.rag_connector)
        self.memory_context_orchestrator.connect_ai_council(self.ai_council_connector)
    
    def register_tool(self, manifest: ToolManifest, implementation: Callable) -> str:
        """
        Register a tool with the system.
        
        Args:
            manifest: Tool manifest
            implementation: Tool implementation function
            
        Returns:
            Tool ID
        """
        # Register with core system
        tool_id = self.tools_system.register_tool(manifest, implementation)
        
        # Register with RAG system if connected
        if self.rag_connector and hasattr(self.rag_connector, 'rag_system'):
            self.rag_connector.register_with_rag(
                tool_id=tool_id,
                tool_description=manifest.description,
                tool_parameters=manifest.parameters
            )
        
        # Register with AI Council if connected
        if self.ai_council_connector and hasattr(self.ai_council_connector, 'ai_council'):
            self.ai_council_connector.register_capability(
                capability_id=f"tool:{tool_id}",
                description=manifest.description,
                parameters=manifest.parameters,
                required_permissions=manifest.required_permissions,
                handler_fn=lambda params: self.execute_tool(
                    ToolExecutionRequest(
                        tool_id=tool_id,
                        parameters=params,
                        request_id="",
                        mode="standard",
                        user_id=""
                    )
                )
            )
        
        logger.info(f"Registered tool {tool_id} with integrated tools system")
        return tool_id
    
    def execute_tool(self, request: ToolExecutionRequest) -> ToolExecutionResponse:
        """
        Execute a tool with full context enrichment and memory sharing.
        
        Args:
            request: Tool execution request
            
        Returns:
            Tool execution response
        """
        # Get user and session IDs from request
        user_id = request.user_id
        session_id = request.metadata.get('session_id') if request.metadata else None
        
        # Enrich context
        enriched_context = {}
        
        if request.metadata:
            enriched_context.update(request.metadata)
            
        enriched_context = self.memory_context_orchestrator.enrich_tool_context(
            context=enriched_context,
            user_id=user_id,
            session_id=session_id
        )
        
        # Update parameters with enriched context
        parameters = request.parameters.copy()
        parameters["__context"] = enriched_context
        
        # Execute the tool using the core system's method signature
        result = self.tools_system.execute_tool(
            tool_id=request.tool_id,
            parameters=parameters,
            mode=request.mode,
            user_id=request.user_id,
            request_id=request.request_id
        )
        
        # Add result to short-term memory
        memory_data = {
            "tool_id": request.tool_id,
            "parameters": request.parameters,
            "result": result.result,
            "success": result.success,
            "error": result.error
        }
        
        memory_metadata = {
            "user_id": user_id,
            "session_id": session_id,
            "request_id": request.request_id,
            "mode": request.mode
        }
        
        # Store successful results in memory
        if result.success:
            self.memory_context_orchestrator.add_to_short_term_memory(
                memory_data=memory_data,
                metadata=memory_metadata,
                memory_type=MemoryType.TOOL_EXECUTION
            )
            
            # Store important results in long-term memory
            importance = result.metadata.get('importance', 0.5) if result.metadata else 0.5
            if importance >= 0.7:
                self.memory_context_orchestrator.add_to_long_term_memory(
                    memory_data=memory_data,
                    metadata=memory_metadata,
                    importance=importance,
                    memory_type=MemoryType.TOOL_EXECUTION
                )
            
            # Share with AI Council if connected
            if self.ai_council_connector and hasattr(self.ai_council_connector, 'ai_council'):
                memory_key = f"tool_execution:{request.tool_id}:{request.request_id}"
                self.ai_council_connector.share_memory(
                    memory_key=memory_key,
                    memory_value=memory_data,
                    memory_type=MemoryType.TOOL_EXECUTION.value,
                    importance=importance
                )
        
        return result
    
    def connect_rag_system(self, rag_system: Any) -> None:
        """
        Connect the RAG system for integration.
        
        Args:
            rag_system: RAG system instance
        """
        self.rag_connector.connect(rag_system)
        self.tool_integration.connect_rag_system(rag_system)
        logger.info("Connected RAG system to integrated tools system")
    
    def connect_ai_council(self, ai_council: Any) -> None:
        """
        Connect the AI Council for integration.
        
        Args:
            ai_council: AI Council instance
        """
        self.ai_council_connector.connect(ai_council)
        self.tool_integration.connect_ai_council(ai_council)
        logger.info("Connected AI Council to integrated tools system")
    
    # Delegate to core tools system methods
    
    def list_tools(self) -> Dict[str, Any]:
        """
        List all registered tools.
        
        Returns:
            Dictionary of registered tools
        """
        return self.tools_system.list_tools()
    
    def get_tool(self, tool_id: str) -> Optional[Any]:
        """
        Get a tool by ID.
        
        Args:
            tool_id: Tool ID
            
        Returns:
            Tool instance or None if not found
        """
        return self.tools_system.get_tool(tool_id)
    
    def disable_tool(self, tool_id: str) -> bool:
        """
        Disable a tool.
        
        Args:
            tool_id: Tool ID
            
        Returns:
            Whether the tool was disabled
        """
        return self.tools_system.disable_tool(tool_id)
    
    def enable_tool(self, tool_id: str) -> bool:
        """
        Enable a tool.
        
        Args:
            tool_id: Tool ID
            
        Returns:
            Whether the tool was enabled
        """
        return self.tools_system.enable_tool(tool_id)
    
    def get_tools_for_user(self, 
                         user_id: str,
                         access_level: Union[int, ToolAccessLevel] = ToolAccessLevel.STANDARD) -> Dict[str, Any]:
        """
        Get tools available for a user based on access level.
        
        Args:
            user_id: User ID
            access_level: Access level for tools
            
        Returns:
            Dictionary of available tools
        """
        return self.tools_system.get_tools_for_user(user_id, access_level)
    
    # Context management convenience methods
    
    def set_user_preference(self, user_id: str, key: str, value: Any) -> None:
        """
        Set a user preference in context.
        
        Args:
            user_id: User ID
            key: Preference key
            value: Preference value
        """
        self.memory_context_orchestrator.set_user_context(user_id, key, value)
    
    def get_user_preference(self, user_id: str, key: str, default: Any = None) -> Any:
        """
        Get a user preference from context.
        
        Args:
            user_id: User ID
            key: Preference key
            default: Default value if not found
            
        Returns:
            Preference value or default
        """
        return self.memory_context_orchestrator.get_user_context(user_id, key, default)
    
    def set_session_data(self, session_id: str, key: str, value: Any) -> None:
        """
        Set session data in context.
        
        Args:
            session_id: Session ID
            key: Data key
            value: Data value
        """
        self.memory_context_orchestrator.set_session_context(session_id, key, value)
    
    def get_session_data(self, session_id: str, key: str, default: Any = None) -> Any:
        """
        Get session data from context.
        
        Args:
            session_id: Session ID
            key: Data key
            default: Default value if not found
            
        Returns:
            Session data or default
        """
        return self.memory_context_orchestrator.get_session_context(session_id, key, default)
