from typing import Dict, List, Any, Optional, Callable, Type, Union
import importlib
import inspect
import json
import os
from pydantic import BaseModel
try:
    from .schemas import ToolManifest, ToolInstance, ToolParameterSchema, ToolResponseSchema, ToolParameterType
except ImportError:
    from schemas import ToolManifest, ToolInstance, ToolParameterSchema, ToolResponseSchema, ToolParameterType

class ToolRegistry:
    """Manages tool registration and discovery."""
    
    def __init__(self):
        """Initialize the tool registry."""
        self.tools: Dict[str, ToolInstance] = {}
    
    def register_tool(self, 
                     manifest: ToolManifest, 
                     implementation: Callable) -> str:
        """Register a tool with its manifest and implementation."""
        if manifest.id in self.tools:
            raise ValueError(f"Tool with ID {manifest.id} already exists")
        
        # Validate that the implementation matches the manifest
        self._validate_implementation(manifest, implementation)
        
        # Create a tool instance
        tool_instance = ToolInstance(
            manifest=manifest,
            enabled=True,
            config={}
        )
        
        # Store the tool instance and its implementation
        self.tools[manifest.id] = tool_instance
        setattr(tool_instance, "_implementation", implementation)
        
        return manifest.id
    
    def _validate_implementation(self, manifest: ToolManifest, implementation: Callable) -> None:
        """Validate that the implementation matches the manifest."""
        # Check if the implementation is callable
        if not callable(implementation):
            raise ValueError("Tool implementation must be callable")
        
        # Check if the parameters match
        sig = inspect.signature(implementation)
        param_names = set(sig.parameters.keys())
        manifest_param_names = set(manifest.parameters.keys())
        
        # Allow additional parameters in the implementation
        missing_params = manifest_param_names - param_names
        if missing_params:
            raise ValueError(f"Implementation missing parameters: {missing_params}")
    
    def get_tool(self, tool_id: str) -> Optional[ToolInstance]:
        """Get a tool by ID."""
        return self.tools.get(tool_id)
    
    def get_tool_implementation(self, tool_id: str) -> Optional[Callable]:
        """Get the implementation of a tool."""
        tool = self.get_tool(tool_id)
        if not tool:
            return None
        return getattr(tool, "_implementation", None)
    
    def list_tools(self, 
                 enabled_only: bool = True, 
                 tags: Optional[List[str]] = None,
                 permissions: Optional[List[str]] = None) -> List[ToolManifest]:
        """List tools matching the criteria."""
        result = []
        
        for tool_id, tool in self.tools.items():
            # Skip disabled tools if enabled_only is True
            if enabled_only and not tool.enabled:
                continue
            
            # Filter by tags if specified
            if tags and not any(tag in tool.manifest.tags for tag in tags):
                continue
            
            # Filter by permissions if specified
            if permissions:
                # Skip tools that require permissions not in the provided list
                required_permissions = set(tool.manifest.required_permissions)
                if required_permissions and not required_permissions.issubset(set(permissions)):
                    continue
            
            result.append(tool.manifest)
        
        return result
    
    def register_from_function(self, 
                              func: Callable, 
                              name: Optional[str] = None,
                              description: Optional[str] = None,
                              version: str = "0.1.0",
                              required_permissions: List[str] = None,
                              tags: List[str] = None) -> str:
        """Register a tool from a function using introspection."""
        # Get function information
        func_name = name or func.__name__
        func_doc = inspect.getdoc(func) or ""
        func_desc = description or func_doc.split("\n")[0] if func_doc else f"{func_name} function"
        
        # Get function signature
        sig = inspect.signature(func)
        
        # Create parameter schemas
        parameters = {}
        for param_name, param in sig.parameters.items():
            param_type = ToolParameterType.ANY
            if param.annotation is not param.empty:
                if param.annotation is str:
                    param_type = ToolParameterType.STRING
                elif param.annotation is int:
                    param_type = ToolParameterType.INTEGER
                elif param.annotation is float:
                    param_type = ToolParameterType.NUMBER
                elif param.annotation is bool:
                    param_type = ToolParameterType.BOOLEAN
                elif param.annotation is list or param.annotation is List:
                    param_type = ToolParameterType.ARRAY
                elif param.annotation is dict or param.annotation is Dict:
                    param_type = ToolParameterType.OBJECT
            
            parameters[param_name] = ToolParameterSchema(
                type=param_type,
                description=f"{param_name} parameter",
                required=param.default is param.empty,
                default=None if param.default is param.empty else param.default
            )
        
        # Create response schema
        response_type = ToolParameterType.ANY
        if sig.return_annotation is not sig.empty:
            if sig.return_annotation is str:
                response_type = ToolParameterType.STRING
            elif sig.return_annotation is int:
                response_type = ToolParameterType.INTEGER
            elif sig.return_annotation is float:
                response_type = ToolParameterType.NUMBER
            elif sig.return_annotation is bool:
                response_type = ToolParameterType.BOOLEAN
            elif sig.return_annotation is list or sig.return_annotation is List:
                response_type = ToolParameterType.ARRAY
            elif sig.return_annotation is dict or sig.return_annotation is Dict:
                response_type = ToolParameterType.OBJECT
        
        response_schema = ToolResponseSchema(
            type=response_type,
            description="Tool response"
        )
        
        # Create manifest
        manifest = ToolManifest(
            name=func_name,
            version=version,
            description=func_desc,
            parameters=parameters,
            response=response_schema,
            required_permissions=required_permissions or [],
            tags=tags or []
        )
        
        # Register the tool
        return self.register_tool(manifest, func)
    
    def enable_tool(self, tool_id: str, enabled: bool = True) -> bool:
        """Enable or disable a tool."""
        tool = self.get_tool(tool_id)
        if not tool:
            return False
        
        tool.enabled = enabled
        return True
    
    def update_tool_config(self, tool_id: str, config: Dict[str, Any]) -> bool:
        """Update the configuration of a tool."""
        tool = self.get_tool(tool_id)
        if not tool:
            return False
        
        tool.config.update(config)
        return True
    
    def remove_tool(self, tool_id: str) -> bool:
        """Remove a tool from the registry."""
        if tool_id not in self.tools:
            return False
        
        del self.tools[tool_id]
        return True