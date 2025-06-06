from typing import Dict, List, Any, Optional, Union, Callable, Literal
from pydantic import BaseModel, Field
from enum import Enum
import uuid

class ToolParameterType(str, Enum):
    """Types of parameters supported by tools."""
    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    OBJECT = "object"
    ARRAY = "array"
    NULL = "null"
    ANY = "any"

class ToolParameterSchema(BaseModel):
    """Schema for a tool parameter."""
    type: Union[ToolParameterType, List[ToolParameterType]]
    description: str
    default: Optional[Any] = None
    required: bool = True
    enum: Optional[List[Any]] = None
    minimum: Optional[Union[int, float]] = None
    maximum: Optional[Union[int, float]] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None
    format: Optional[str] = None
    items: Optional['ToolParameterSchema'] = None
    properties: Optional[Dict[str, 'ToolParameterSchema']] = None

class ToolResponseSchema(BaseModel):
    """Schema for a tool response."""
    type: Union[ToolParameterType, List[ToolParameterType]]
    description: str
    properties: Optional[Dict[str, ToolParameterSchema]] = None

class ToolManifest(BaseModel):
    """Manifest for a tool."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    version: str
    description: str
    parameters: Dict[str, ToolParameterSchema] = {}
    response: ToolResponseSchema
    required_permissions: List[str] = []
    author: Optional[str] = None
    homepage: Optional[str] = None
    repository: Optional[str] = None
    tags: List[str] = []
    examples: List[Dict[str, Any]] = []

class ToolInstance(BaseModel):
    """An instance of a tool with configuration."""
    manifest: ToolManifest
    enabled: bool = True
    config: Dict[str, Any] = {}

class ToolExecutionRequest(BaseModel):
    """Request to execute a tool."""
    tool_id: str
    parameters: Dict[str, Any]
    mode: Optional[str] = None
    user_id: Optional[str] = None
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class ToolExecutionResponse(BaseModel):
    """Response from tool execution."""
    tool_id: str
    request_id: str
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    duration_ms: float
    metadata: Dict[str, Any] = {}