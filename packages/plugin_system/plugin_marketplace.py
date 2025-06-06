"""
Plugin Marketplace for SpaceNew

Allows admin users to discover, install, enable, disable, and configure plugins via the UI and API.
"""
from typing import List, Dict, Any
import importlib
import os
import sys

PLUGINS_DIR = "api/plugins"

# Add support for discovering plugins in archivist_package/plugins
ARCHIVIST_PLUGINS_DIR = "core/packages/archivist_package/plugins"

class PluginMarketplace:
    def __init__(self):
        self.plugins = self.discover_plugins()

    def discover_plugins(self) -> List[Dict[str, Any]]:
        plugins = []
        # Discover plugins in /api/plugins (legacy)
        if os.path.exists(PLUGINS_DIR):
            for name in os.listdir(PLUGINS_DIR):
                manifest_path = f"{PLUGINS_DIR}/{name}/plugin_manifest.py"
                if os.path.exists(manifest_path):
                    module = importlib.import_module(f"api.plugins.{name}.plugin_manifest")
                    plugin_class = getattr(module, "HumanSimulatorPlugin", None)
                    if plugin_class:
                        plugin_instance = plugin_class()
                        manifest = plugin_instance.get_manifest()
                        plugins.append({
                            "id": manifest.id,
                            "name": manifest.name,
                            "version": manifest.version,
                            "description": manifest.description,
                            "enabled": True,  # Placeholder, should be persisted
                            "manifest": manifest
                        })
        # Discover plugins in archivist_package/plugins
        if os.path.exists(ARCHIVIST_PLUGINS_DIR):
            sys.path.append(os.path.abspath("core/packages/archivist_package"))
            for fname in os.listdir(ARCHIVIST_PLUGINS_DIR):
                if fname.endswith(".py") and fname != "__init__.py":
                    module_name = f"archivist_package.plugins.{fname[:-3]}"
                    try:
                        module = importlib.import_module(module_name)
                        for attr in dir(module):
                            obj = getattr(module, attr)
                            if hasattr(obj, "get_manifest"):
                                manifest = obj().get_manifest()
                                plugins.append({
                                    "id": manifest.id,
                                    "name": manifest.name,
                                    "version": manifest.version,
                                    "description": manifest.description,
                                    "enabled": True,
                                    "manifest": manifest
                                })
                    except Exception as e:
                        print(f"Failed to load plugin {module_name}: {e}")
        return plugins

    def get_plugin(self, plugin_id: str) -> Dict[str, Any]:
        for plugin in self.plugins:
            if plugin["id"] == plugin_id:
                return plugin
        return None

    def enable_plugin(self, plugin_id: str):
        # TODO: Implement persistent enable/disable logic
        for plugin in self.plugins:
            if plugin["id"] == plugin_id:
                plugin["enabled"] = True
        # Persist state to DB or config file

    def disable_plugin(self, plugin_id: str):
        # TODO: Implement persistent enable/disable logic
        for plugin in self.plugins:
            if plugin["id"] == plugin_id:
                plugin["enabled"] = False
        # Persist state to DB or config file

    def configure_plugin(self, plugin_id: str, config: Dict[str, Any]):
        # TODO: Implement plugin configuration logic
        pass

    def install_plugin(self, plugin_source: str):
        """
        Install a plugin from a given source (git url, local path, or package registry).
        """
        # TODO: Implement plugin installation logic (clone/copy, pip/npm install, etc.)
        pass

    def uninstall_plugin(self, plugin_id: str):
        """
        Uninstall a plugin and remove its files/configuration.
        """
        # TODO: Implement plugin uninstallation logic
        pass

    def list_plugins(self) -> List[Dict[str, Any]]:
        """
        Return a list of all discovered plugins with their status.
        """
        return self.plugins

    def register_plugin_routes(self, app):
        """
        Register all enabled plugin routes with the main FastAPI app.
        """
        for plugin in self.plugins:
            if plugin["enabled"]:
                try:
                    routes_module = importlib.import_module(f"api.plugins.{plugin['id']}.routes")
                    if hasattr(routes_module, "router"):
                        app.include_router(routes_module.router, prefix=f"/api/{plugin['id']}")
                except Exception as e:
                    print(f"Failed to register routes for plugin {plugin['id']}: {e}")

    def register_plugin_ui(self, ui_registry):
        """
        Register all enabled plugin UI components with the SpaceNew UI registry.
        """
        for plugin in self.plugins:
            if plugin["enabled"]:
                for comp in plugin["manifest"].ui_components:
                    ui_registry.register(comp)
