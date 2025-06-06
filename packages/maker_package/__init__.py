"""
The Maker Package - Advanced Simulation System

This package integrates human simulator capabilities with financial tools
to create immersive, autonomous agent experiences for the SpaceNew platform.
"""

from .plugin import MakerPackagePlugin
from .config_schema import MakerPackageConfig
from .tools_integration import MakerPackageTools

__version__ = "1.0.0"

# Export main plugin class
plugin_class = MakerPackagePlugin
