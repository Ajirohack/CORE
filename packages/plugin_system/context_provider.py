"""
Shared Context Provider for SpaceNew Plugins

Provides a global context (user, org, permissions, etc.) accessible to all plugins.
"""
from typing import Dict, Any
from threading import Lock

class SpaceNewContext:
    def __init__(self):
        self._context: Dict[str, Any] = {}
        self._lock = Lock()

    def set(self, key: str, value: Any):
        with self._lock:
            self._context[key] = value

    def get(self, key: str, default=None) -> Any:
        with self._lock:
            return self._context.get(key, default)

    def as_dict(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._context)

# Singleton instance
space_new_context = SpaceNewContext()

# Example usage:
# space_new_context.set("user", {"id": "123", "role": "admin"})
# user = space_new_context.get("user")
