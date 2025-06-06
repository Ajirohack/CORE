"""
UI Registry for SpaceNew Plugins

Allows plugins to register UI components for dynamic loading in the SpaceNew dashboard.
"""
from typing import Dict, List, Any

class UIRegistry:
    def __init__(self):
        self._components: List[Dict[str, Any]] = []

    def register(self, component: Dict[str, Any]):
        self._components.append(component)

    def list_components(self) -> List[Dict[str, Any]]:
        return self._components

# Singleton instance
space_new_ui_registry = UIRegistry()
