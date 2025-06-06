"""
Extension Points for SpaceNew Plugins

Defines hooks where plugins can extend or override platform functionality.
"""
from typing import Callable, Dict, List

class ExtensionPoints:
    def __init__(self):
        self._hooks: Dict[str, List[Callable]] = {}

    def register(self, hook_name: str, func: Callable):
        self._hooks.setdefault(hook_name, []).append(func)

    def run(self, hook_name: str, *args, **kwargs):
        for func in self._hooks.get(hook_name, []):
            func(*args, **kwargs)

# Singleton instance
space_new_extension_points = ExtensionPoints()
