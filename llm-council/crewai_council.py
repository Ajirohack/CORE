"""
CrewAI-based LLM Council integration for The Archivist
- Specialist registration and selection
- Capability execution and planning
- Memory/context sharing
- Tool integration hooks

NOTE: This is an alternative implementation using CrewAI.
The main LLM Council service is in llm_council_service.py
"""
from typing import List, Dict, Any, Optional
import logging

# Optional CrewAI imports (fallback if not installed)
try:
    from crewai import Crew, Specialist, Task, Memory, Context, Tool
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    logging.warning("CrewAI not available. Install with: pip install crewai")

# Updated imports for new architecture
try:
    from ..services.communication import SpaceAPIClient
    from ..services.service_logging import get_logger
except ImportError:
    # Fallback for direct execution
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from services.communication import SpaceAPIClient
    from services.service_logging import get_logger

logger = get_logger(__name__)

class CrewAICouncil:
    def __init__(self):
        if not CREWAI_AVAILABLE:
            raise ImportError("CrewAI is required but not installed. Run: pip install crewai")
            
        self.specialists: Dict[str, Specialist] = {}
        self.memory = Memory()
        self.context = Context()
        self.tools: Dict[str, Tool] = {}
        self.crew = Crew()
        
        # Integration points (updated for new architecture)
        self.api_client = SpaceAPIClient()
        self.running = False
        logger.info("CrewAI Council initialized")

    def register_specialist(self, name: str, role: str, capabilities: List[str]):
        specialist = Specialist(name=name, role=role, capabilities=capabilities)
        self.specialists[name] = specialist
        self.crew.add_specialist(specialist)

    def register_tool(self, name: str, tool: Tool):
        self.tools[name] = tool
        self.crew.add_tool(tool)

    def share_memory(self, key: str, value: Any):
        """Share memory between specialists."""
        if not CREWAI_AVAILABLE:
            logger.warning("CrewAI not available, memory operation skipped")
            return
        self.memory.set(key, value)
        logger.debug(f"Memory shared: {key}")

    def get_memory(self, key: str) -> Any:
        """Retrieve shared memory."""
        if not CREWAI_AVAILABLE:
            logger.warning("CrewAI not available, returning None")
            return None
        return self.memory.get(key)

    def execute_plan(self, plan: List[Task], context: Optional[Dict[str, Any]] = None) -> Any:
        """Execute a plan using the CrewAI crew."""
        if not CREWAI_AVAILABLE:
            raise RuntimeError("CrewAI not available for plan execution")
        
        # Set context if provided
        if context:
            self.context.update(context)
        
        # Execute the plan
        result = self.crew.execute(plan, context=self.context)
        
        # Log the execution
        logger.info(f"Plan executed with {len(plan)} tasks")
        
        return result

    def get_context(self) -> Context:
        return self.context

    def set_context(self, context: Context):
        self.context = context
        # Sync with unified storage
        self.storage.set('crewai_context', 'context', context)

    def run_event_loop(self, poll_interval: float = 5.0):
        """Run an autonomous event loop for the council (background operation)"""
        import threading, time
        def loop():
            self.running = True
            while self.running:
                # Example: poll for new events or tasks
                events = self.event_bus.poll('council.task_queue')
                for event in events:
                    if event['type'] == 'execute_plan':
                        self.execute_plan(event['plan'], event.get('context'))
                time.sleep(poll_interval)
        t = threading.Thread(target=loop, daemon=True)
        t.start()

    def stop_event_loop(self):
        self.running = False

# Example usage (to be replaced with real integration):
# council = CrewAICouncil()
# council.register_specialist('researcher', 'Research', ['search', 'summarize'])
# council.register_tool('web_search', SomeWebSearchTool())
# plan = [Task(...), ...]
# result = council.execute_plan(plan)
