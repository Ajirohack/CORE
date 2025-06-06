"""
Archivist Integration Framework
- Unified API gateway
- Event processing system
- Interface adapter registry
- Central router for all core components
"""
from core.enhanced_event_bus import EventBus
from core.integration.interface_adapters import (
    InterfaceAdapterRegistry, ConversationalAdapter, VoiceAdapter, VisualAdapter, APIAdapter
)
from core.llm_council.crewai_council import CrewAICouncil
from core.engines.cognitive_synthesis_engine import CognitiveSynthesisEngine
from core.plugin_system.plugin_manager import PluginManager
from core.unified_storage import UnifiedStorageLayer

class ArchivistIntegrationFramework:
    def __init__(self):
        self.event_bus = EventBus()
        self.adapters = InterfaceAdapterRegistry()
        self.llm_council = CrewAICouncil()
        self.engine = CognitiveSynthesisEngine()
        self.plugin_manager = PluginManager()
        self.storage = UnifiedStorageLayer()
        # Register default adapters
        self.adapters.register('conversational', ConversationalAdapter(self.event_bus))
        self.adapters.register('voice', VoiceAdapter(self.event_bus))
        self.adapters.register('visual', VisualAdapter(self.event_bus))
        self.adapters.register('api', APIAdapter(self.event_bus))
        # Wire up event routing
        self._setup_event_routing()

    def _setup_event_routing(self):
        # Route incoming interface events to engine/council/plugin as appropriate
        def handle_incoming(event):
            t = event.get('type')
            if t == 'text':
                self.engine.event_queue.add_event({'type': 'user.text', 'payload': event['content']})
            elif t == 'audio':
                self.engine.event_queue.add_event({'type': 'user.audio', 'payload': event['content']})
            elif t == 'visual':
                self.engine.event_queue.add_event({'type': 'user.visual', 'payload': event['content']})
            elif t == 'api':
                self.engine.event_queue.add_event({'type': 'user.api', 'payload': event['content']})
        self.event_bus.subscribe('interface.incoming', handle_incoming)
        # Route plugin events
        def handle_plugin_event(event):
            self.engine.event_queue.add_event({'type': 'plugin.event', 'payload': event})
        self.event_bus.subscribe('plugin.event', handle_plugin_event)
        # Route engine/council output to adapters
        def handle_engine_output(event):
            self.adapters.get('conversational').send(event.get('synthesis', ''))
        self.event_bus.subscribe('cognitive.synthesis.result', handle_engine_output)
        # More routing can be added as needed

    # Unified API gateway: expose core component access and event API
    def api_gateway(self, action: str, payload: dict = None):
        """Central entry point for all system actions (for API, UI, or other services)."""
        payload = payload or {}
        if action == 'send_message':
            self.adapters.get('conversational').receive(payload.get('message', ''))
            return {'status': 'sent'}
        elif action == 'trigger_plugin':
            return self.plugin_manager.trigger_plugin_action(payload)
        elif action == 'vector_search':
            return self.storage.vector_search(payload)
        elif action == 'graph_query':
            return self.storage.graph_query(payload)
        elif action == 'track_event':
            return self.storage.track_event(payload)
        # Add more actions as needed
        return {'error': 'Unknown action'}

    # Central event router: extensible for new event types/flows
    def route_event(self, event: dict):
        t = event.get('type')
        if t == 'user.text':
            self.engine.event_queue.add_event(event)
        elif t == 'user.audio':
            self.engine.event_queue.add_event(event)
        elif t == 'user.visual':
            self.engine.event_queue.add_event(event)
        elif t == 'user.api':
            self.engine.event_queue.add_event(event)
        elif t == 'plugin.event':
            self.engine.event_queue.add_event(event)
        elif t == 'council.plan':
            self.llm_council.execute_plan(event.get('plan', []), event.get('context'))
        # Add more event types as needed
        else:
            # Default: publish to event bus for other subscribers
            self.event_bus.publish('unhandled.event', event)

    # Example: expose adapters, engine, council, plugin manager, storage
    def get_adapter(self, name):
        return self.adapters.get(name)
    def get_event_bus(self):
        return self.event_bus
    def get_llm_council(self):
        return self.llm_council
    def get_engine(self):
        return self.engine
    def get_plugin_manager(self):
        return self.plugin_manager
    def get_storage(self):
        return self.storage
