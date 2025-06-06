"""
Data schemas for the System Engine Control.
"""
from enum import Enum
from typing import Dict, Any, List, Optional, TypedDict
from pydantic import BaseModel, Field


class UserMode(str, Enum):
    """User mode enum."""
    ARCHIVIST = "archivist"
    ORCHESTRATOR = "orchestrator"
    GODFATHER = "godfather"
    ENTITY = "entity"


class RequestInput(BaseModel):
    """Input for a request to be processed."""
    user_id: str = Field(..., description="User ID")
    message: str = Field(..., description="User message")
    mode: str = Field(..., description="User mode (archivist, orchestrator, godfather, entity)")
    context: Optional[Dict[str, Any]] = Field(default={}, description="Additional context for the request")
    metadata: Optional[Dict[str, Any]] = Field(default={}, description="Additional metadata for the request")
    
    def dict(self):
        """Convert to dictionary."""
        return {
            "user_id": self.user_id,
            "message": self.message,
            "mode": self.mode,
            "context": self.context,
            "metadata": self.metadata
        }


class ResponseOutput(BaseModel):
    """Output from processing a request."""
    response: str = Field(..., description="Response text")
    user_id: str = Field(..., description="User ID")
    tools_used: List[str] = Field(default=[], description="List of tools used")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")
    error: Optional[str] = Field(default=None, description="Error message, if any")


class EngineState(TypedDict, total=False):
    """State for the workflow graph."""
    user_id: str
    mode: str
    query: str
    context: Dict[str, Any]
    tools_used: List[str]
    tool_results: List[Dict[str, Any]]
    current_engine: Optional[str]
    response: Optional[str]
    error: Optional[str]
    metadata: Dict[str, Any]