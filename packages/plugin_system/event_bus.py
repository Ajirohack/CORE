"""
Event Bus for SpaceNew Plugins

Supports event-driven communication between plugins (in-memory, can be replaced with RabbitMQ/Kafka).
"""
from typing import Callable, Dict, List, Any
from threading import Lock

class EventBus:
    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[Any], None]]] = {}
        self._lock = Lock()

    def subscribe(self, event_type: str, handler: Callable[[Any], None]):
        with self._lock:
            self._subscribers.setdefault(event_type, []).append(handler)

    def publish(self, event_type: str, payload: Any):
        handlers = self._subscribers.get(event_type, [])
        for handler in handlers:
            handler(payload)

# Singleton instance
space_new_event_bus = EventBus()

# Example usage:
# space_new_event_bus.subscribe("mirrorcore.stage_transition", lambda payload: print(payload))
# space_new_event_bus.publish("mirrorcore.stage_transition", {"user_id": "123", "to_stage": "FPP"})
