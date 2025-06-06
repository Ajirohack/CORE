"""
Plugin interface definition for SpaceNew platform.
Provides the base interface and types for all plugins.
"""
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field

class PluginCapability(str, Enum):
    """Capabilities that a plugin can provide"""
    DATA_PROCESSING = "data_processing"
    AI_MODEL = "ai_model"
    CONTENT_GENERATION = "content_generation"
    USER_INTERFACE = "user_interface"
    WORKFLOW = "workflow"
    INTEGRATION = "integration"
    SECURITY = "security"
    ANALYTICS = "analytics"

class PluginPermission(str, Enum):
    """Permissions that a plugin can request"""
    READ_USER_DATA = "read_user_data"
    WRITE_USER_DATA = "write_user_data"
    EXECUTE_WORKFLOWS = "execute_workflows"
    ACCESS_EXTERNAL_SERVICES = "access_external_services"
    MODIFY_SYSTEM_SETTINGS = "modify_system_settings"
    SEND_NOTIFICATIONS = "send_notifications"

class PluginDependency(BaseModel):
    """Definition of a plugin dependency"""
    plugin_id: str = Field(..., description="Unique identifier of the required plugin")
    version_constraint: str = Field(..., description="Version constraint (e.g. >=1.0.0)")
    is_optional: bool = Field(False, description="Whether this dependency is optional")

class PluginApiEndpoint(BaseModel):
    """Definition of a REST API endpoint provided by the plugin"""
    path: str = Field(..., description="URL path of the endpoint")
    method: str = Field(..., description="HTTP method (GET, POST, etc.)")
    description: str = Field(..., description="Human-readable description")
    requires_auth: bool = Field(True, description="Whether authentication is required")
    permissions: List[str] = Field([], description="Required permissions")

class PluginUiComponent(BaseModel):
    """Definition of a UI component provided by the plugin"""
    component_id: str = Field(..., description="Unique identifier of the component")
    name: str = Field(..., description="Display name of the component")
    description: str = Field(..., description="Human-readable description")
    extension_points: List[str] = Field([], description="UI extension points this can attach to")
    entry_point: str = Field(..., description="Module entry point for the component")
    
class PluginHook(BaseModel):
    """Definition of a hook provided or consumed by the plugin"""
    hook_id: str = Field(..., description="Unique identifier of the hook")
    description: str = Field(..., description="Human-readable description")
    is_provider: bool = Field(False, description="True if plugin provides this hook")

class PluginManifest(BaseModel):
    """Plugin manifest containing metadata and capabilities"""
    id: str = Field(..., description="Unique plugin identifier")
    name: str = Field(..., description="Display name of the plugin")
    version: str = Field(..., description="Semantic version (e.g. 1.0.0)")
    description: str = Field(..., description="Human-readable description")
    author: str = Field(..., description="Plugin author")
    license: str = Field("MIT", description="License identifier")
    capabilities: List[PluginCapability] = Field([], description="Capabilities provided")
    permissions: List[PluginPermission] = Field([], description="Required permissions")
    dependencies: List[PluginDependency] = Field([], description="Plugin dependencies")
    api_endpoints: List[PluginApiEndpoint] = Field([], description="REST API endpoints")
    ui_components: List[PluginUiComponent] = Field([], description="UI components")
    hooks: List[PluginHook] = Field([], description="Hooks provided or consumed")
    settings_schema: Dict[str, Any] = Field({}, description="JSON schema for plugin settings")
    
    class Config:
        """Pydantic model configuration"""
        extra = "forbid"  # Prevent unknown fields

class PluginContext(BaseModel):
    """Context provided to plugin methods"""
    plugin_id: str = Field(..., description="Plugin ID")
    settings: Dict[str, Any] = Field({}, description="Plugin settings")
    environment: str = Field("development", description="Environment (dev/prod)")
    user_id: Optional[str] = Field(None, description="Current user ID if authenticated")
    request_id: Optional[str] = Field(None, description="Current request ID for tracing")

class PluginInterface(ABC):
    """Interface that must be implemented by all plugins"""
    
    @abstractmethod
    def get_manifest(self) -> PluginManifest:
        """Get the plugin manifest"""
        pass
        
    @abstractmethod
    def initialize(self, context: PluginContext) -> None:
        """Initialize the plugin with the given context"""
        pass
        
    @abstractmethod
    def shutdown(self) -> None:
        """Shut down the plugin and release resources"""
        pass
        
    def on_settings_change(self, settings: Dict[str, Any]) -> None:
        """Called when plugin settings are changed"""
        pass
        
    def get_api_router(self) -> Any:  # Returns a FastAPI router
        """Get the FastAPI router for this plugin's API endpoints"""
        return None
        
    def get_ui_components(self) -> Dict[str, Any]:
        """Get the UI components for this plugin"""
        return {}
