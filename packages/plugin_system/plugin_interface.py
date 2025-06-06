"""
SpaceNew Service Plugin Interface

This module defines the interface that all service plugins must implement
to be registered with the SpaceNew platform kernel.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from pydantic import BaseModel


class ServiceEndpoint(BaseModel):
    """Represents an API endpoint exposed by a service plugin"""
    path: str
    method: str
    description: str
    auth_required: bool = True
    rate_limit: Optional[int] = None


class UIComponent(BaseModel):
    """Represents a UI component exposed by a service plugin"""
    name: str
    type: str  # 'react', 'vue', 'web-component'
    path: str  # relative path to the component
    description: str
    props: Dict[str, Any] = {}


class EventSubscription(BaseModel):
    """Events that this service listens for"""
    event_type: str
    description: str


class EventPublication(BaseModel):
    """Events that this service publishes"""
    event_type: str
    description: str
    schema: Dict[str, Any] = {}


class PluginManifest(BaseModel):
    """Plugin manifest for a service"""
    id: str
    name: str
    version: str
    description: str
    endpoints: List[ServiceEndpoint] = []
    ui_components: List[UIComponent] = []
    subscribed_events: List[EventSubscription] = []
    published_events: List[EventPublication] = []
    data_models: Dict[str, Any] = {}
    dependencies: List[str] = []
    config_schema: Dict[str, Any] = {}


class ServicePlugin(ABC):
    """Interface that all service plugins must implement"""
    
    @abstractmethod
    def get_manifest(self) -> PluginManifest:
        """Return the plugin manifest"""
        pass
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the plugin with the provided configuration"""
        pass
    
    @abstractmethod
    def shutdown(self) -> bool:
        """Gracefully shut down the plugin"""
        pass
    
    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Return the health status of the plugin"""
        pass
