"""
Tools System for the Space Project
Manages tool registration, validation, execution, and permissions
"""

import logging
import inspect
from typing import Dict, List, Any, Optional, Callable, Type, Union
import functools
import time
import json
from enum import Enum
import uuid

try:
    from .schemas import ToolManifest, ToolExecutionRequest, ToolExecutionResponse
    from .tool_registry import ToolRegistry
    from .tool_executor import ToolExecutor
    from .access_control import AccessControl
except ImportError:
    # For when running as a script
    from schemas import ToolManifest, ToolExecutionRequest, ToolExecutionResponse
    from tool_registry import ToolRegistry
    from tool_executor import ToolExecutor
    from access_control import AccessControl

# Setup logging
logger = logging.getLogger(__name__)


class ToolAccessLevel(Enum):
    """Access level for tools based on Space engine modes"""
    BASIC = 0        # Archivist mode (minimal tools)
    STANDARD = 1     # Orchestrator mode (standard tools)
    ADVANCED = 2     # Godfather mode (advanced tools)
    ADMIN = 3        # Entity mode (all tools)


class ToolCategory(Enum):
    """Categories of tools for organization"""
    WEB = "web"
    CONTENT = "content"
    DATA = "data"
    CODE = "code"
    SYSTEM = "system"
    UTILITY = "utility"
    CUSTOM = "custom"


class ToolExecutionError(Exception):
    """Exception raised when a tool execution fails"""
    pass


class Tool:
    """
    Base class for all tools in the system
    Tools provide specific capabilities to the Space system
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        func: Callable,
        access_level: ToolAccessLevel = ToolAccessLevel.STANDARD,
        category: ToolCategory = ToolCategory.UTILITY,
        version: str = "1.0",
        metadata: Dict[str, Any] = None
    ):
        """
        Initialize a tool
        
        Args:
            name: Name of the tool
            description: Description of what the tool does
            func: The function to call when the tool is executed
            access_level: Required access level to use this tool
            category: Category of the tool
            version: Tool version
            metadata: Additional metadata about the tool
        """
        self.name = name
        self.description = description
        self.func = func
        self.access_level = access_level
        self.category = category
        self.version = version
        self.metadata = metadata or {}
        self.executions = 0
        self.total_execution_time = 0
        
        # Extract parameter information from the function
        self.parameters = self._extract_parameters(func)
        logger.info(f"Tool '{name}' initialized")
    
    def _extract_parameters(self, func: Callable) -> Dict[str, Dict[str, Any]]:
        """
        Extract parameter information from a function
        
        Args:
            func: Function to extract parameters from
            
        Returns:
            Dictionary of parameter information
        """
        params = {}
        signature = inspect.signature(func)
        for name, param in signature.parameters.items():
            # Skip 'self' for methods
            if name == 'self':
                continue
                
            param_info = {
                "required": param.default == inspect.Parameter.empty,
                "type": "any"  # Default type
            }
            
            # Try to get type annotation
            if param.annotation != inspect.Parameter.empty:
                if hasattr(param.annotation, "__name__"):
                    param_info["type"] = param.annotation.__name__
                else:
                    param_info["type"] = str(param.annotation)
            
            # Set default value if available
            if param.default != inspect.Parameter.empty:
                param_info["default"] = param.default
            
            params[name] = param_info
            
        return params
    
    def execute(self, **kwargs) -> Any:
        """
        Execute the tool with the provided arguments
        
        Args:
            **kwargs: Arguments to pass to the tool function
            
        Returns:
            Result of the tool execution
        """
        start_time = time.time()
        try:
            result = self.func(**kwargs)
            execution_time = time.time() - start_time
            self.executions += 1
            self.total_execution_time += execution_time
            
            # Log execution
            logger.info(f"Tool '{self.name}' executed in {execution_time:.3f}s")
            
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Tool '{self.name}' execution failed: {str(e)}")
            raise ToolExecutionError(f"Tool execution failed: {str(e)}")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the tool to a dictionary representation
        
        Returns:
            Tool as a dictionary
        """
        return {
            "name": self.name,
            "description": self.description,
            "access_level": self.access_level.name,
            "category": self.category.value,
            "version": self.version,
            "parameters": self.parameters,
            "metadata": self.metadata,
            "stats": {
                "executions": self.executions,
                "avg_execution_time": self.total_execution_time / self.executions if self.executions > 0 else 0
            }
        }


class ToolManager:
    """
    Manages the registration, discovery, and execution of tools
    """
    
    def __init__(self):
        """Initialize the tool manager"""
        self.tools: Dict[str, Tool] = {}
        self.categories: Dict[ToolCategory, List[str]] = {
            category: [] for category in ToolCategory
        }
        logger.info("Tool Manager initialized")
    
    def register_tool(self, tool: Tool) -> None:
        """
        Register a tool with the manager
        
        Args:
            tool: Tool to register
        """
        if tool.name in self.tools:
            logger.warning(f"Tool '{tool.name}' already registered. Overwriting.")
        
        self.tools[tool.name] = tool
        
        # Add to category index
        if tool.category not in self.categories:
            self.categories[tool.category] = []
        
        self.categories[tool.category].append(tool.name)
        logger.info(f"Tool '{tool.name}' registered")
    
    def register_function_as_tool(
        self,
        func: Callable,
        name: Optional[str] = None,
        description: Optional[str] = None,
        access_level: ToolAccessLevel = ToolAccessLevel.STANDARD,
        category: ToolCategory = ToolCategory.UTILITY,
        version: str = "1.0",
        metadata: Dict[str, Any] = None
    ) -> Tool:
        """
        Register a function as a tool
        
        Args:
            func: Function to register
            name: Name for the tool (defaults to function name)
            description: Description of the tool (defaults to function docstring)
            access_level: Required access level for the tool
            category: Category of the tool
            version: Tool version
            metadata: Additional metadata
            
        Returns:
            The created Tool instance
        """
        name = name or func.__name__
        description = description or func.__doc__ or f"Tool based on {func.__name__}"
        
        tool = Tool(
            name=name,
            description=description,
            func=func,
            access_level=access_level,
            category=category,
            version=version,
            metadata=metadata
        )
        
        self.register_tool(tool)
        return tool
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """
        Get a tool by name
        
        Args:
            name: Name of the tool
            
        Returns:
            Tool if found, else None
        """
        return self.tools.get(name)
    
    def list_tools(
        self,
        access_level: Optional[ToolAccessLevel] = None,
        category: Optional[ToolCategory] = None
    ) -> List[Dict[str, Any]]:
        """
        List available tools, optionally filtered by access level or category
        
        Args:
            access_level: Filter by access level
            category: Filter by category
            
        Returns:
            List of tool dictionaries
        """
        filtered_tools = []
        
        for tool in self.tools.values():
            # Filter by access level if specified
            if access_level is not None and tool.access_level.value > access_level.value:
                continue
            
            # Filter by category if specified
            if category is not None and tool.category != category:
                continue
            
            filtered_tools.append(tool.to_dict())
        
        return filtered_tools
    
    def execute_tool(
        self,
        name: str,
        access_level: ToolAccessLevel,
        **kwargs
    ) -> Any:
        """
        Execute a tool by name with arguments
        
        Args:
            name: Name of the tool to execute
            access_level: Current access level for permission check
            **kwargs: Arguments to pass to the tool
            
        Returns:
            Result of the tool execution
        """
        tool = self.get_tool(name)
        
        if not tool:
            raise ValueError(f"Tool '{name}' not found")
        
        # Check permissions
        if access_level.value < tool.access_level.value:
            raise PermissionError(
                f"Access denied to tool '{name}'. "
                f"Required level: {tool.access_level.name}, "
                f"Current level: {access_level.name}"
            )
        
        # Validate parameters
        self._validate_parameters(tool, kwargs)
        
        # Execute the tool
        logger.info(f"Executing tool '{name}'")
        return tool.execute(**kwargs)
    
    def _validate_parameters(self, tool: Tool, params: Dict[str, Any]) -> None:
        """
        Validate parameters for a tool
        
        Args:
            tool: Tool to validate parameters for
            params: Parameters to validate
        """
        # Check for missing required parameters
        for param_name, param_info in tool.parameters.items():
            if param_info.get("required", False) and param_name not in params:
                raise ValueError(f"Missing required parameter '{param_name}' for tool '{tool.name}'")
        
        # Check for unknown parameters
        for param_name in params:
            if param_name not in tool.parameters:
                logger.warning(f"Unknown parameter '{param_name}' for tool '{tool.name}'")
    
    def tool_decorator(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        access_level: ToolAccessLevel = ToolAccessLevel.STANDARD,
        category: ToolCategory = ToolCategory.UTILITY,
        version: str = "1.0",
        metadata: Dict[str, Any] = None
    ) -> Callable:
        """
        Decorator to register a function as a tool
        
        Args:
            name: Override name for the tool (default: function name)
            description: Description for the tool (default: function docstring)
            access_level: Access level required for the tool
            category: Tool category
            version: Tool version
            metadata: Additional metadata
            
        Returns:
            Decorator function
        """
        def decorator(func):
            actual_name = name or func.__name__
            actual_description = description or func.__doc__ or f"Tool based on {func.__name__}"
            
            self.register_function_as_tool(
                func=func,
                name=actual_name,
                description=actual_description,
                access_level=access_level,
                category=category,
                version=version,
                metadata=metadata
            )
            
            # Return the original function unchanged
            return func
        
        return decorator


class ToolsSystem:
    """Main entry point for the Tools/Packages System."""
    
    def __init__(self):
        """Initialize the Tools/Packages system."""
        self.registry = ToolRegistry()
        self.access_control = AccessControl()
        self.executor = ToolExecutor(self.registry, self.access_control)
        self._register_core_tools()
    
    def _register_core_tools(self):
        """Register core tools that are always available."""
        
        # System information tool
        @self.register_tool(
            name="system_info",
            description="Get information about the tools system",
            required_permissions=["basic_tools"]
        )
        def system_info() -> Dict[str, Any]:
            """Get information about the current system configuration."""
            available_tools = len(self.registry.list_tools())
            available_modes = self.access_control.list_modes()
            
            return {
                "available_tools": available_tools,
                "available_modes": available_modes,
                "status": "operational"
            }
        
        # Echo tool for testing
        @self.register_tool(
            name="echo",
            description="Echo back the input",
            required_permissions=["basic_tools"]
        )
        def echo(message: str) -> str:
            """Echo back the input message."""
            return message
    
    def register_tool(self, 
                     name: str, 
                     description: str, 
                     required_permissions: List[str] = None, 
                     version: str = "0.1.0",
                     tags: List[str] = None):
        """Decorator to register a tool function."""
        def decorator(func):
            self.registry.register_from_function(
                func=func,
                name=name,
                description=description,
                version=version,
                required_permissions=required_permissions or [],
                tags=tags or []
            )
            return func
        return decorator
    
    def execute_tool(self, 
                    tool_id: str, 
                    parameters: Dict[str, Any],
                    mode: Optional[str] = None,
                    user_id: Optional[str] = None,
                    request_id: Optional[str] = None) -> ToolExecutionResponse:
        """Execute a tool with the given parameters."""
        # Create the request
        request = ToolExecutionRequest(
            tool_id=tool_id,
            parameters=parameters,
            mode=mode,
            user_id=user_id,
            request_id=request_id or str(uuid.uuid4())
        )
        
        # Log the request
        logger.info(f"Executing tool: {tool_id}, Request ID: {request.request_id}")
        
        # Execute the tool
        return self.executor.execute(request)
    
    def get_available_tools(self, mode: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get available tools, optionally filtered by mode permissions."""
        if not mode:
            # If no mode specified, return all tools
            tools = self.registry.list_tools()
        else:
            # Get permissions for the specified mode
            permissions = self.access_control.get_permissions(mode)
            
            # Get tools filtered by permissions
            tools = self.registry.list_tools(permissions=permissions)
        
        # Convert to simplified dict format for API response
        result = []
        for tool in tools:
            result.append({
                "id": tool.id,
                "name": tool.name,
                "description": tool.description,
                "version": tool.version,
                "parameters": {name: param.dict() for name, param in tool.parameters.items()},
                "required_permissions": tool.required_permissions,
                "tags": tool.tags
            })
        
        return result
    
    def register_external_tool(self, manifest: Dict[str, Any], implementation: Callable) -> str:
        """Register an external tool with the system."""
        # Convert dict to ToolManifest
        tool_manifest = ToolManifest(**manifest)
        
        # Register the tool
        return self.registry.register_tool(tool_manifest, implementation)
    
    def get_modes(self) -> List[Dict[str, Any]]:
        """Get all available access modes."""
        result = []
        
        for mode_name in self.access_control.list_modes():
            mode_details = self.access_control.get_mode_details(mode_name)
            if mode_details:
                result.append(mode_details)
        
        return result