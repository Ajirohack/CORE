"""
Task orchestration and event dispatch for the cognitive core.
Implements the central control system for Archivist's cognitive architecture.
"""

import asyncio
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass
from .memory import MemorySystem
from .reasoning import ReasoningEngine
from .knowledge import KnowledgeManager
from ..event_bus import EventBus
from prometheus_client import Counter, Histogram

@dataclass
class CognitiveContext:
    user_id: str
    session_id: str
    request_id: str
    metadata: Dict[str, Any]

BRAIN_TASKS = Counter('archivist_brain_tasks', 'Number of brain tasks dispatched', ['type'])
BRAIN_ERRORS = Counter('archivist_brain_errors', 'Number of brain errors', ['type'])
BRAIN_TASK_DURATION = Histogram('archivist_brain_task_duration_seconds', 'Duration of brain tasks', ['type'])

class BrainController:
    def __init__(self):
        self.memory = MemorySystem()
        self.reasoning = ReasoningEngine()
        self.knowledge = KnowledgeManager()
        self.event_bus = EventBus()
        self.task_queue = asyncio.Queue()
        self.metrics = {
            'tasks_dispatched': 0,
            'errors': 0
        }
        self.last_error = None
        self.last_task = None
        self.last_task_time = None
        
    async def initialize(self):
        """Initialize all cognitive subsystems"""
        await self.memory.initialize()
        await self.reasoning.initialize()
        await self.knowledge.initialize()
        self.event_bus.subscribe("task.new", self._handle_new_task)
        
    @property
    def health(self):
        return {
            'metrics': self.metrics,
            'last_error': self.last_error,
            'last_task': self.last_task,
            'last_task_time': self.last_task_time
        }

    async def dispatch_task(self, task: Dict[str, Any], context: CognitiveContext):
        task_type = task.get("type", "unknown")
        with BRAIN_TASK_DURATION.labels(type=task_type).time():
            try:
                if task_type == "memory":
                    result = await self.memory.process(task, context)
                elif task_type == "reasoning":
                    result = await self.reasoning.process(task, context)
                elif task_type == "knowledge":
                    result = await self.knowledge.process(task, context)
                else:
                    raise ValueError(f"Unknown task type: {task_type}")
                BRAIN_TASKS.labels(type=task_type).inc()
                return result
            except Exception as e:
                await self._handle_error(e, context)
                BRAIN_ERRORS.labels(type=task_type).inc()
                raise

    async def monitor_events(self):
        """Process events from the event queue"""
        while True:
            task = await self.task_queue.get()
            context = task.get("context")
            try:
                result = await self.dispatch_task(task, context)
                await self._handle_result(result, context)
            except Exception as e:
                await self._handle_error(e, context)
            finally:
                self.task_queue.task_done()

    async def _handle_new_task(self, task: Dict[str, Any]):
        """Handle incoming tasks from event bus"""
        await self.task_queue.put(task)

    async def _handle_result(self, result: Any, context: CognitiveContext):
        """Process and distribute task results"""
        await self.event_bus.publish("task.complete", {
            "result": result,
            "context": context
        })

    async def _handle_error(self, error: Exception, context: CognitiveContext):
        """Handle and log task errors"""
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"BrainController error: {error}")
        await self.event_bus.publish("task.error", {
            "error": str(error),
            "context": context
        })
