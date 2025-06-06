"""
Packages service implementation.
Manages tool registry, execution, and integration capabilities.
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional
import json
from datetime import datetime
import uuid
from pathlib import Path

try:
    from ..base_service import BaseService, ServiceRequest, ServiceResponse
except ImportError:
    # For when running as a script
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from base_service import BaseService, ServiceRequest, ServiceResponse

try:
    from .src.tools_system import ToolsSystem, ToolCategory, ToolAccessLevel
    from .src.tool_registry import ToolRegistry
    from .src.tool_executor import ToolExecutor
    from .src.access_control import AccessControl
except ImportError:
    # For when running as a script, import from local src
    sys.path.append(str(Path(__file__).parent / "src"))
    from tools_system import ToolsSystem, ToolCategory, ToolAccessLevel
    from tool_registry import ToolRegistry
    from tool_executor import ToolExecutor
    from access_control import AccessControl

logger = logging.getLogger(__name__)

class PackagesService(BaseService):
    """
    Service for managing tools/packages system.
    Handles tool registration, execution, and integration with other services.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("packages", "1.0.0", config)
        self.tools_system = None
        self.registry = None
        self.executor = None
        self.access_control = None
        self.active_executions = {}
        
    def get_description(self) -> str:
        return "Tool registry and execution system for managing and running tools/packages"
    
    def get_capabilities(self) -> List[str]:
        return [
            "tool_registration",
            "tool_execution", 
            "tool_discovery",
            "permission_management",
            "execution_monitoring"
        ]
    
    def get_endpoints(self) -> Dict[str, str]:
        return {
            "register_tool": f"/api/v1/packages/register",
            "execute_tool": f"/api/v1/packages/execute",
            "list_tools": f"/api/v1/packages/tools",
            "get_tool": f"/api/v1/packages/tools/{'{tool_id}'}",
            "health": f"/api/v1/packages/health"
        }
    
    def get_metadata(self) -> Dict[str, Any]:
        return {
            "total_tools": len(self.registry.tools) if self.registry else 0,
            "active_executions": len(self.active_executions),
            "supported_categories": [cat.value for cat in ToolCategory],
            "access_levels": [level.value for level in ToolAccessLevel]
        }
    
    async def initialize(self) -> bool:
        """Initialize the packages service"""
        try:
            self.logger.info("Initializing packages service...")
            
            # Initialize tools system components
            self.registry = ToolRegistry()
            self.access_control = AccessControl()
            self.executor = ToolExecutor(self.registry, self.access_control)
            self.tools_system = ToolsSystem()
            
            # Load any pre-configured tools
            await self._load_default_tools()
            
            self.logger.info("Packages service initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error("Failed to initialize packages service", error=e)
            return False
    
    async def process_request(self, request: ServiceRequest) -> ServiceResponse:
        """Process incoming requests"""
        try:
            action = request.action
            payload = request.payload
            
            if action == "register_tool":
                result = await self._register_tool(payload)
            elif action == "execute_tool":
                result = await self._execute_tool(payload, request.user_id)
            elif action == "list_tools":
                result = await self._list_tools(payload)
            elif action == "get_tool":
                result = await self._get_tool(payload)
            elif action == "delete_tool":
                result = await self._delete_tool(payload)
            else:
                return ServiceResponse(
                    request_id=request.request_id,
                    service_id=self.service_id,
                    status="error",
                    error=f"Unknown action: {action}"
                )
            
            return ServiceResponse(
                request_id=request.request_id,
                service_id=self.service_id,
                status="success",
                data=result
            )
            
        except Exception as e:
            self.logger.error(f"Error processing request: {request.action}", error=e)
            return ServiceResponse(
                request_id=request.request_id,
                service_id=self.service_id,
                status="error",
                error=str(e)
            )
    
    async def _register_tool(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new tool"""
        tool_manifest = payload.get('manifest')
        if not tool_manifest:
            raise ValueError("Tool manifest is required")
        
        tool_id = self.registry.register_tool(tool_manifest)
        
        self.logger.info(f"Registered tool: {tool_id}")
        return {
            "tool_id": tool_id,
            "status": "registered",
            "message": "Tool successfully registered"
        }
    
    async def _execute_tool(self, payload: Dict[str, Any], user_id: Optional[str] = None) -> Dict[str, Any]:
        """Execute a tool"""
        tool_id = payload.get('tool_id')
        parameters = payload.get('parameters', {})
        access_level = payload.get('access_level', ToolAccessLevel.BASIC.value)
        
        if not tool_id:
            raise ValueError("Tool ID is required")
        
        # Create execution request
        execution_id = str(uuid.uuid4())
        execution_request = {
            'execution_id': execution_id,
            'tool_id': tool_id,
            'parameters': parameters,
            'user_id': user_id,
            'access_level': access_level,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Track execution
        self.active_executions[execution_id] = execution_request
        
        try:
            # Execute the tool
            result = await self.executor.execute_tool(tool_id, parameters, access_level)
            
            # Clean up tracking
            self.active_executions.pop(execution_id, None)
            
            self.logger.info(f"Executed tool: {tool_id}", context={'execution_id': execution_id})
            
            return {
                "execution_id": execution_id,
                "tool_id": tool_id,
                "status": "completed",
                "result": result
            }
            
        except Exception as e:
            # Clean up tracking
            self.active_executions.pop(execution_id, None)
            self.logger.error(f"Tool execution failed: {tool_id}", error=e, context={'execution_id': execution_id})
            raise
    
    async def _list_tools(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """List available tools"""
        category = payload.get('category')
        access_level = payload.get('access_level', ToolAccessLevel.BASIC.value)
        
        tools = self.registry.list_tools(category=category, access_level=access_level)
        
        return {
            "tools": tools,
            "total": len(tools),
            "category": category,
            "access_level": access_level
        }
    
    async def _get_tool(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Get tool details"""
        tool_id = payload.get('tool_id')
        if not tool_id:
            raise ValueError("Tool ID is required")
        
        tool = self.registry.get_tool(tool_id)
        if not tool:
            raise ValueError(f"Tool not found: {tool_id}")
        
        return {
            "tool": tool,
            "status": "found"
        }
    
    async def _delete_tool(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a tool"""
        tool_id = payload.get('tool_id')
        if not tool_id:
            raise ValueError("Tool ID is required")
        
        success = self.registry.unregister_tool(tool_id)
        
        if success:
            self.logger.info(f"Deleted tool: {tool_id}")
            return {
                "tool_id": tool_id,
                "status": "deleted",
                "message": "Tool successfully deleted"
            }
        else:
            raise ValueError(f"Failed to delete tool: {tool_id}")
    
    async def _load_default_tools(self):
        """Load any default tools"""
        # This would load built-in tools or tools from configuration
        self.logger.info("Loading default tools...")
        # Implementation would depend on your specific default tools
        pass
    
    async def shutdown(self):
        """Shutdown the service"""
        self.logger.info("Shutting down packages service...")
        
        # Cancel any active executions
        for execution_id in list(self.active_executions.keys()):
            self.active_executions.pop(execution_id, None)
        
        await super().shutdown()
