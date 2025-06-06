"""
Archivist Package - Advanced Simulation System for SpaceNew

This package implements sophisticated human simulation capabilities for performing
complex tasks requiring human-like interactions, including the MirrorCore system,
financial operations, and multi-platform engagement.
"""

from .plugin import ArchivistPackagePlugin
from .config_schema import ARCHIVIST_CONFIG_SCHEMA

__all__ = ["ArchivistPackagePlugin", "ARCHIVIST_CONFIG_SCHEMA"]
