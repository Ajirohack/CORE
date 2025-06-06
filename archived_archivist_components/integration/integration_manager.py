"""
Integration Manager for The Archivist
- API gateway, event routing, and adapter orchestration
"""
from typing import Any, Dict

class IntegrationManager:
    def __init__(self):
        self.adapters: Dict[str, Any] = {}
        self.event_handlers: Dict[str, Any] = {}
    def register_adapter(self, name: str, adapter: Any):
        self.adapters[name] = adapter
    def register_event_handler(self, event_type: str, handler: Any):
        self.event_handlers[event_type] = handler
    def route_event(self, event_type: str, event: Dict):
        if event_type in self.event_handlers:
            return self.event_handlers[event_type](event)
        raise ValueError(f"No handler for event type {event_type}")
