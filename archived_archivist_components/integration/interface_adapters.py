"""
Interface Adapter Scaffolding for The Archivist
- Conversational, voice, visual, and API adapters
- Event-driven integration with core system
"""
from typing import Any, Dict, Callable
from core.enhanced_event_bus import EventBus

class BaseInterfaceAdapter:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
    def send(self, data: Any):
        raise NotImplementedError
    def receive(self, data: Any):
        raise NotImplementedError

class ConversationalAdapter(BaseInterfaceAdapter):
    def send(self, message: str):
        # Send message to chat UI or API
        self.event_bus.publish('interface.outgoing', {'type': 'text', 'content': message})
    def receive(self, message: str):
        # Receive message from chat UI or API
        self.event_bus.publish('interface.incoming', {'type': 'text', 'content': message})

class VoiceAdapter(BaseInterfaceAdapter):
    def send(self, audio_data: bytes):
        self.event_bus.publish('interface.outgoing', {'type': 'audio', 'content': audio_data})
    def receive(self, audio_data: bytes):
        self.event_bus.publish('interface.incoming', {'type': 'audio', 'content': audio_data})

class VisualAdapter(BaseInterfaceAdapter):
    def send(self, visual_data: Any):
        self.event_bus.publish('interface.outgoing', {'type': 'visual', 'content': visual_data})
    def receive(self, visual_data: Any):
        self.event_bus.publish('interface.incoming', {'type': 'visual', 'content': visual_data})

class APIAdapter(BaseInterfaceAdapter):
    def send(self, payload: Dict):
        self.event_bus.publish('interface.outgoing', {'type': 'api', 'content': payload})
    def receive(self, payload: Dict):
        self.event_bus.publish('interface.incoming', {'type': 'api', 'content': payload})

# Example: Adapter registry for dynamic loading
class InterfaceAdapterRegistry:
    def __init__(self):
        self.adapters = {}
    def register(self, name: str, adapter: BaseInterfaceAdapter):
        self.adapters[name] = adapter
    def get(self, name: str) -> BaseInterfaceAdapter:
        return self.adapters[name]
