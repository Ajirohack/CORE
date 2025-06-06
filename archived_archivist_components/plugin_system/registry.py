"""
Plugin registry for managing plugin lifecycle and discovery.
"""
import importlib
import os
import sys
import json
from typing import Dict, List, Optional, Any, TypeVar, Type, cast
import logging

from .interface import PluginInterface, PluginManifest, PluginContext

# Setup logger
logger = logging.getLogger(__name__)

# Type variable for plugin class
T = TypeVar('T', bound=PluginInterface)

class PluginRegistry:
    """
    Registry for plugin discovery, loading, and lifecycle management.
    Maintains a collection of all available plugins and their status.
    """
    
    def __init__(self):
        """Initialize an empty plugin registry"""
        self._plugins: Dict[str, PluginInterface] = {}
        self._manifests: Dict[str, PluginManifest] = {}
        self._plugin_paths: Dict[str, str] = {}
        self._enabled_plugins: Dict[str, bool] = {}
        self._contexts: Dict[str, PluginContext] = {}
        
    def discover_plugins(self, plugins_dir: str) -> List[str]:
        """
        Discover available plugins in the specified directory.
        Returns list of discovered plugin IDs.
        
        Args:
            plugins_dir: Directory to scan for plugins
            
        Returns:
            List of discovered plugin IDs
        """
        discovered_plugins = []
        
        if not os.path.exists(plugins_dir) or not os.path.isdir(plugins_dir):
            logger.warning(f"Plugins directory {plugins_dir} does not exist")
            return discovered_plugins
            
        # Look for direct subdirectories that contain manifest.json
        for item in os.listdir(plugins_dir):
            plugin_dir = os.path.join(plugins_dir, item)
            
            # Skip if not a directory
            if not os.path.isdir(plugin_dir):
                continue
                
            # Check for manifest file
            manifest_path = os.path.join(plugin_dir, "manifest.json")
            if not os.path.exists(manifest_path):
                continue
                
            try:
                # Load and validate manifest
                with open(manifest_path, "r") as f:
                    manifest_data = json.load(f)
                    
                # Check if plugin.py exists
                plugin_path = os.path.join(plugin_dir, "plugin.py")
                if not os.path.exists(plugin_path):
                    logger.warning(f"Plugin {manifest_data.get('id')} is missing plugin.py")
                    continue
                    
                plugin_id = manifest_data.get("id")
                if not plugin_id:
                    logger.warning(f"Plugin in {plugin_dir} is missing ID in manifest")
                    continue
                    
                # Record plugin location
                self._plugin_paths[plugin_id] = plugin_dir
                discovered_plugins.append(plugin_id)
                
            except Exception as e:
                logger.error(f"Error processing plugin in {plugin_dir}: {e}")
                
        return discovered_plugins
        
    def load_plugin(self, plugin_id: str) -> bool:
        """
        Load a specific plugin by ID.
        
        Args:
            plugin_id: ID of the plugin to load
            
        Returns:
            True if plugin was loaded successfully
        """
        if plugin_id in self._plugins:
            logger.warning(f"Plugin {plugin_id} is already loaded")
            return True
            
        if plugin_id not in self._plugin_paths:
            logger.error(f"Plugin {plugin_id} not found in discovered plugins")
            return False
            
        plugin_dir = self._plugin_paths[plugin_id]
        
        try:
            # Add plugin directory to path temporarily
            sys.path.insert(0, os.path.dirname(plugin_dir))
            
            # Import the plugin module
            module_name = os.path.basename(plugin_dir)
            plugin_module = importlib.import_module(f"{module_name}.plugin")
            
            # Find plugin class (subclass of PluginInterface)
            plugin_class = None
            for attr_name in dir(plugin_module):
                attr = getattr(plugin_module, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, PluginInterface)
                    and attr is not PluginInterface
                ):
                    plugin_class = attr
                    break
                    
            if not plugin_class:
                logger.error(f"No PluginInterface implementation found in {plugin_id}")
                return False
                
            # Instantiate plugin
            plugin = plugin_class()
            
            # Get and validate manifest
            manifest = plugin.get_manifest()
            if manifest.id != plugin_id:
                logger.error(f"Plugin {plugin_id} has mismatched ID in manifest: {manifest.id}")
                return False
                
            # Store plugin and manifest
            self._plugins[plugin_id] = plugin
            self._manifests[plugin_id] = manifest
            self._enabled_plugins[plugin_id] = True
            
            # Create default context
            context = PluginContext(
                plugin_id=plugin_id,
                settings={},
                environment="development"
            )
            self._contexts[plugin_id] = context
            
            # Initialize plugin
            plugin.initialize(context)
            
            logger.info(f"Successfully loaded plugin {plugin_id} v{manifest.version}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading plugin {plugin_id}: {e}")
            return False
            
        finally:
            # Remove the directory from path
            if os.path.dirname(plugin_dir) in sys.path:
                sys.path.remove(os.path.dirname(plugin_dir))
                
    def unload_plugin(self, plugin_id: str) -> bool:
        """
        Unload a specific plugin by ID.
        
        Args:
            plugin_id: ID of the plugin to unload
            
        Returns:
            True if plugin was unloaded successfully
        """
        if plugin_id not in self._plugins:
            logger.warning(f"Plugin {plugin_id} is not loaded")
            return False
            
        try:
            # Get plugin instance
            plugin = self._plugins[plugin_id]
            
            # Shutdown plugin
            plugin.shutdown()
            
            # Remove from registry
            del self._plugins[plugin_id]
            del self._manifests[plugin_id]
            del self._enabled_plugins[plugin_id]
            del self._contexts[plugin_id]
            
            logger.info(f"Successfully unloaded plugin {plugin_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error unloading plugin {plugin_id}: {e}")
            return False
            
    def enable_plugin(self, plugin_id: str) -> bool:
        """
        Enable a plugin.
        
        Args:
            plugin_id: ID of the plugin to enable
            
        Returns:
            True if plugin was enabled successfully
        """
        if plugin_id not in self._plugins:
            logger.warning(f"Plugin {plugin_id} is not loaded")
            return False
            
        self._enabled_plugins[plugin_id] = True
        logger.info(f"Enabled plugin {plugin_id}")
        return True
        
    def disable_plugin(self, plugin_id: str) -> bool:
        """
        Disable a plugin.
        
        Args:
            plugin_id: ID of the plugin to disable
            
        Returns:
            True if plugin was disabled successfully
        """
        if plugin_id not in self._plugins:
            logger.warning(f"Plugin {plugin_id} is not loaded")
            return False
            
        self._enabled_plugins[plugin_id] = False
        logger.info(f"Disabled plugin {plugin_id}")
        return True
        
    def get_plugin(self, plugin_id: str) -> Optional[PluginInterface]:
        """
        Get a plugin instance by ID.
        
        Args:
            plugin_id: ID of the plugin
            
        Returns:
            Plugin instance or None if not found/loaded
        """
        if plugin_id not in self._plugins:
            return None
        if not self._enabled_plugins.get(plugin_id, False):
            return None
        return self._plugins[plugin_id]
        
    def get_plugin_manifest(self, plugin_id: str) -> Optional[PluginManifest]:
        """
        Get a plugin manifest by ID.
        
        Args:
            plugin_id: ID of the plugin
            
        Returns:
            Plugin manifest or None if not found/loaded
        """
        return self._manifests.get(plugin_id)
        
    def get_all_plugins(self) -> List[str]:
        """
        Get IDs of all loaded plugins.
        
        Returns:
            List of plugin IDs
        """
        return list(self._plugins.keys())
        
    def get_enabled_plugins(self) -> List[str]:
        """
        Get IDs of all enabled plugins.
        
        Returns:
            List of enabled plugin IDs
        """
        return [pid for pid, enabled in self._enabled_plugins.items() if enabled]
        
    def update_plugin_settings(self, plugin_id: str, settings: Dict[str, Any]) -> bool:
        """
        Update settings for a specific plugin.
        
        Args:
            plugin_id: ID of the plugin
            settings: New settings dictionary
            
        Returns:
            True if settings were updated successfully
        """
        if plugin_id not in self._plugins:
            logger.warning(f"Plugin {plugin_id} is not loaded")
            return False
            
        try:
            # Update context
            context = self._contexts[plugin_id]
            context.settings = settings
            
            # Notify plugin
            plugin = self._plugins[plugin_id]
            plugin.on_settings_change(settings)
            
            logger.info(f"Updated settings for plugin {plugin_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating settings for plugin {plugin_id}: {e}")
            return False
            
    def get_plugin_by_type(self, plugin_type: Type[T]) -> List[T]:
        """
        Get all plugins of a specific type.
        
        Args:
            plugin_type: Plugin interface type to filter by
            
        Returns:
            List of plugin instances matching the type
        """
        result = []
        for plugin_id, plugin in self._plugins.items():
            if isinstance(plugin, plugin_type) and self._enabled_plugins.get(plugin_id, False):
                result.append(cast(T, plugin))
        return result

# Create singleton instance
registry = PluginRegistry()
