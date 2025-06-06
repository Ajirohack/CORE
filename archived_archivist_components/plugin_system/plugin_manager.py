"""
Plugin System scaffold for The Archivist (AgentGPT pattern)
- Tool/capability registration, permission, event hooks
"""
from typing import Callable, Dict, Any
import os
import json

class PluginManager:
    def __init__(self):
        self.plugins: Dict[str, Any] = {}
        self.permissions: Dict[str, Any] = {}
        self.plugin_meta: Dict[str, dict] = {}
        self.event_hooks: Dict[str, Callable] = {}

    def register_plugin(self, plugin: dict) -> str:
        """Register a plugin/tool/capability from a dict manifest."""
        name = plugin.get('name')
        if not name:
            raise ValueError('Plugin must have a name')
        self.plugins[name] = plugin.get('implementation') or (lambda *a, **k: 'No implementation')
        self.plugin_meta[name] = plugin
        if 'permissions' in plugin:
            self.permissions[name] = plugin['permissions']
        return name

    def list_plugins(self):
        return list(self.plugin_meta.values())

    def trigger_plugin_action(self, data: dict):
        name = data.get('name')
        args = data.get('args', [])
        kwargs = data.get('kwargs', {})
        if name in self.plugins:
            # Permission checks can be added here
            result = self.plugins[name](*args, **kwargs)
            # Event hook
            if name in self.event_hooks:
                self.event_hooks[name](result)
            return result
        raise ValueError(f"Plugin {name} not registered")

    def register_event_hook(self, name: str, hook: Callable):
        self.event_hooks[name] = hook

    def discover_plugins(self, plugins_dir: str = "plugins"):
        """Auto-discover plugins from a directory (each plugin as a manifest.json or .py file)."""
        for entry in os.listdir(plugins_dir):
            entry_path = os.path.join(plugins_dir, entry)
            if os.path.isdir(entry_path):
                manifest_path = os.path.join(entry_path, "manifest.json")
                if os.path.exists(manifest_path):
                    with open(manifest_path, "r") as f:
                        manifest = json.load(f)
                        # Optionally load implementation from a .py file
                        impl_path = os.path.join(entry_path, manifest.get("implementation_file", ""))
                        if impl_path and os.path.exists(impl_path):
                            # Dynamically import implementation (simplified)
                            import importlib.util
                            spec = importlib.util.spec_from_file_location(entry, impl_path)
                            mod = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(mod)
                            manifest["implementation"] = getattr(mod, manifest.get("implementation_symbol", "main"), None)
                        self.register_plugin(manifest)

    def get_marketplace_metadata(self):
        """Return plugin metadata for UI marketplace (no code, just info)."""
        return [
            {
                "name": meta.get("name"),
                "description": meta.get("description"),
                "version": meta.get("version"),
                "author": meta.get("author"),
                "capabilities": meta.get("capabilities", []),
                "permissions": meta.get("permissions", []),
                "icon": meta.get("icon", ""),
                "tags": meta.get("tags", []),
            }
            for meta in self.plugin_meta.values()
        ]
