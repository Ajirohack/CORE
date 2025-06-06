"""
Simplified packages service implementation.
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

logger = logging.getLogger(__name__)

class PackagesService(BaseService):
    """
    Service for managing tools/packages system.
    Handles tool registration, execution, and integration with other services.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("packages", "1.0.0", config)
        self.tools_registry = {}
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
            "total_tools": len(self.tools_registry),
            "active_executions": len(self.active_executions),
            "supported_categories": ["web", "content", "data", "code", "system", "utility", "custom"],
            "access_levels": ["basic", "standard", "advanced", "admin"]
        }
    
    async def initialize(self) -> bool:
        """Initialize the packages service"""
        try:
            self.logger.info("Initializing packages service...")
            
            # Initialize tools registry
            self.tools_registry = {}
            
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
        
        tool_id = str(uuid.uuid4())
        self.tools_registry[tool_id] = {
            "id": tool_id,
            "manifest": tool_manifest,
            "registered_at": datetime.utcnow().isoformat()
        }
        
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
        
        if not tool_id:
            raise ValueError("Tool ID is required")
        
        if tool_id not in self.tools_registry:
            raise ValueError(f"Tool not found: {tool_id}")
        
        # Create execution request
        execution_id = str(uuid.uuid4())
        execution_request = {
            'execution_id': execution_id,
            'tool_id': tool_id,
            'parameters': parameters,
            'user_id': user_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Track execution
        self.active_executions[execution_id] = execution_request
        
        try:
            # Simulate tool execution
            result = {
                "message": f"Tool {tool_id} executed successfully",
                "parameters": parameters,
                "execution_time": "0.5s"
            }
            
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
        access_level = payload.get('access_level', 'basic')
        
        tools = []
        for tool_id, tool_data in self.tools_registry.items():
            tool_info = {
                "id": tool_id,
                "manifest": tool_data["manifest"],
                "registered_at": tool_data["registered_at"]
            }
            tools.append(tool_info)
        
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
        
        if tool_id not in self.tools_registry:
            raise ValueError(f"Tool not found: {tool_id}")
        
        tool_data = self.tools_registry[tool_id]
        
        return {
            "tool": tool_data,
            "status": "found"
        }
    
    async def _delete_tool(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Delete a tool"""
        tool_id = payload.get('tool_id')
        if not tool_id:
            raise ValueError("Tool ID is required")
        
        if tool_id not in self.tools_registry:
            raise ValueError(f"Tool not found: {tool_id}")
        
        del self.tools_registry[tool_id]
        
        self.logger.info(f"Deleted tool: {tool_id}")
        return {
            "tool_id": tool_id,
            "status": "deleted",
            "message": "Tool successfully deleted"
        }
    
    async def _load_default_tools(self):
        """Load any default tools"""
        # This would load built-in tools or tools from configuration
        self.logger.info("Loading default tools...")
        
        # Add a sample tool for testing
        sample_tool = {
            "name": "echo_tool",
            "description": "Simple echo tool for testing",
            "version": "1.0.0",
            "category": "utility"
        }
        
        await self._register_tool({"manifest": sample_tool})
    
    async def shutdown(self):
        """Shutdown the service"""
        self.logger.info("Shutting down packages service...")
        
        # Cancel any active executions
        for execution_id in list(self.active_executions.keys()):
            self.active_executions.pop(execution_id, None)
        
        await super().shutdown()
