import time
import traceback
import json
from typing import Dict, Any, Optional
import jsonschema
try:
    from .schemas import ToolExecutionRequest, ToolExecutionResponse
    from .tool_registry import ToolRegistry
    from .access_control import AccessControl
except ImportError:
    from schemas import ToolExecutionRequest, ToolExecutionResponse
    from tool_registry import ToolRegistry
    from access_control import AccessControl

class ToolExecutor:
    """Executes tools with proper validation and sandboxing."""
    
    def __init__(self, tool_registry: ToolRegistry, access_control: AccessControl):
        """Initialize the tool executor."""
        self.tool_registry = tool_registry
        self.access_control = access_control
    
    def execute(self, request: ToolExecutionRequest) -> ToolExecutionResponse:
        """Execute a tool based on the request."""
        start_time = time.time()
        tool_id = request.tool_id
        
        # Create base response structure
        response = ToolExecutionResponse(
            tool_id=tool_id,
            request_id=request.request_id,
            success=False,
            error=None,
            result=None,
            duration_ms=0,
            metadata={}
        )
        
        try:
            # Get the tool
            tool = self.tool_registry.get_tool(tool_id)
            if not tool:
                response.error = f"Tool not found: {tool_id}"
                return self._finish_response(response, start_time)
            
            # Check permissions if mode is specified
            if request.mode:
                required_permissions = tool.manifest.required_permissions
                for permission in required_permissions:
                    if not self.access_control.has_permission(request.mode, permission):
                        response.error = f"Access denied: mode '{request.mode}' lacks permission '{permission}'"
                        response.metadata["missing_permission"] = permission
                        return self._finish_response(response, start_time)
            
            # Validate parameters
            try:
                self._validate_parameters(tool.manifest.parameters, request.parameters)
            except ValueError as e:
                response.error = f"Parameter validation failed: {str(e)}"
                return self._finish_response(response, start_time)
            
            # Get the implementation
            implementation = self.tool_registry.get_tool_implementation(tool_id)
            if not implementation:
                response.error = "Tool implementation not found"
                return self._finish_response(response, start_time)
            
            # Add metadata to response
            response.metadata["tool_name"] = tool.manifest.name
            if request.user_id:
                response.metadata["user_id"] = request.user_id
            
            # Execute the tool with safety measures
            result = self._safe_execute(implementation, request.parameters)
            
            # Set success response
            response.success = True
            response.result = result
            
        except Exception as e:
            # Catch any unexpected errors
            response.error = f"Tool execution error: {str(e)}"
            response.metadata["traceback"] = traceback.format_exc()
        
        return self._finish_response(response, start_time)
    
    def _finish_response(self, response: ToolExecutionResponse, start_time: float) -> ToolExecutionResponse:
        """Calculate duration and finalize response."""
        response.duration_ms = round((time.time() - start_time) * 1000, 2)
        return response
    
    def _validate_parameters(self, schema_params: Dict, input_params: Dict) -> None:
        """Validate parameters against schema."""
        # Check for missing required parameters
        for param_name, param_schema in schema_params.items():
            if param_schema.required and param_name not in input_params:
                raise ValueError(f"Missing required parameter: {param_name}")
        
        # TODO: Implement more comprehensive validation using jsonschema
        # This would require converting our parameter schema to JSON Schema format
    
    def _safe_execute(self, func: callable, params: Dict[str, Any]) -> Any:
        """Execute a function with safety measures."""
        # TODO: Implement more comprehensive sandboxing if needed
        # Options:
        # - Use subprocess with timeout
        # - Use Docker containers for isolation
        # - Use Python's RestrictedPython
        
        # For now, we'll just execute the function directly
        # with basic exception handling
        try:
            return func(**params)
        except Exception as e:
            raise RuntimeError(f"Error in tool execution: {str(e)}")