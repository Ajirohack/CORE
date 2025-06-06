"""
Tool integration framework for Archivist.
Allows dynamic discovery and secure access to external tools.
"""
import logging
from typing import Dict, Any, Callable
from dataclasses import dataclass
from uuid import UUID

@dataclass
class ToolDefinition:
    """Defines a tool's interface and capabilities"""
    name: str
    description: str
    permissions: list[str]
    schema: Dict[str, Any]
    handler: Callable

class ToolRegistry:
    """Central registry for tool management"""
    
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._logger = logging.getLogger(__name__)

    def register(self, tool: ToolDefinition) -> None:
        """Register a new tool"""
        self._tools[tool.name] = tool
        self._logger.info(f"Registered tool: {tool.name}")

    def get_tool(self, name: str) -> ToolDefinition:
        """Get tool by name"""
        return self._tools[name]

    def list_tools(self) -> list[str]:
        """List all registered tools"""
        return list(self._tools.keys())

    async def execute_tool(self, name: str, user_id: UUID, **params) -> Any:
        """Execute a tool with permission checking"""
        tool = self.get_tool(name)
        # TODO: Check permissions
        return await tool.handler(**params)
