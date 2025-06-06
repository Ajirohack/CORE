"""
Event bus implementation for SpaceNew platform.
Provides a central event system for communication between components.
"""
import asyncio
import logging
import uuid
from datetime import datetime
from enum import Enum, auto
from typing import Dict, List, Any, Callable, Awaitable, Optional, Set, Union

# Setup logger
logger = logging.getLogger(__name__)

class EventPriority(Enum):
    """Priority levels for event handlers"""
    LOW = auto()
    NORMAL = auto()
    HIGH = auto()
    CRITICAL = auto()

class Event:
    """Base class for all events"""
    
    def __init__(self, event_type: str, source: str, data: Any = None):
        """
        Initialize a new event.
        
        Args:
            event_type: Type identifier for the event
            source: Component that generated the event
            data: Event payload data
        """
        self.id = str(uuid.uuid4())
        self.type = event_type
        self.source = source
        self.data = data if data is not None else {}
        self.timestamp = datetime.now().isoformat()
        
    def __str__(self) -> str:
        """String representation of the event"""
        return f"Event({self.type}, source={self.source}, id={self.id})"

# Type for synchronous event handlers
EventHandler = Callable[[Event], None]

# Type for asynchronous event handlers
AsyncEventHandler = Callable[[Event], Awaitable[None]]

# Combined handler type
AnyEventHandler = Union[EventHandler, AsyncEventHandler]

class EventBus:
    """
    Central event bus for the application.
    Handles event distribution with subscription and filtering support.
    """
    
    def __init__(self):
        """Initialize an empty event bus"""
        # Maps event types to handlers with their priorities
        self._handlers: Dict[str, List[tuple[AnyEventHandler, EventPriority]]] = {}
        
        # Maps event types to source filters
        self._source_filters: Dict[AnyEventHandler, Set[str]] = {}
        
        # Cache of handler async status (is the handler a coroutine function)
        self._is_async_handler: Dict[AnyEventHandler, bool] = {}
        
        # Event loop for async handling
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        
    def _ensure_loop(self) -> asyncio.AbstractEventLoop:
        """Ensure we have a reference to the event loop"""
        if self._loop is None or self._loop.is_closed():
            self._loop = asyncio.get_event_loop()
        return self._loop
        
    def subscribe(
        self,
        event_type: str,
        handler: AnyEventHandler,
        priority: EventPriority = EventPriority.NORMAL,
        source_filter: Optional[Union[str, List[str]]] = None
    ) -> None:
        """
        Subscribe to events of a specific type.
        
        Args:
            event_type: Type of events to subscribe to
            handler: Function to call when event occurs
            priority: Handler priority
            source_filter: Optional filter for event sources
        """
        # Initialize handlers list if needed
        if event_type not in self._handlers:
            self._handlers[event_type] = []
            
        # Add handler with priority
        self._handlers[event_type].append((handler, priority))
        
        # Sort handlers by priority (highest first)
        self._handlers[event_type].sort(key=lambda h: h[1].value, reverse=True)
        
        # Store source filter if provided
        if source_filter:
            if handler not in self._source_filters:
                self._source_filters[handler] = set()
                
            # Convert single string to list
            if isinstance(source_filter, str):
                source_filter = [source_filter]
                
            # Add all sources to filter set
            for source in source_filter:
                self._source_filters[handler].add(source)
                
        # Cache async status
        self._is_async_handler[handler] = asyncio.iscoroutinefunction(handler)
        
    def unsubscribe(self, event_type: str, handler: AnyEventHandler) -> bool:
        """
        Unsubscribe from events of a specific type.
        
        Args:
            event_type: Type of events to unsubscribe from
            handler: Handler function to remove
            
        Returns:
            True if handler was removed, False if not found
        """
        if event_type not in self._handlers:
            return False
            
        # Find and remove handler
        for i, (h, _) in enumerate(self._handlers[event_type]):
            if h == handler:
                self._handlers[event_type].pop(i)
                
                # Clean up source filters
                if handler in self._source_filters:
                    del self._source_filters[handler]
                    
                # Clean up async cache
                if handler in self._is_async_handler:
                    del self._is_async_handler[handler]
                    
                return True
                
        return False
        
    def publish(self, event: Event) -> None:
        """
        Publish an event to all subscribers.
        This runs synchronously and blocks until all handlers complete.
        
        Args:
            event: Event to publish
        """
        if event.type not in self._handlers:
            return
            
        # Process handlers in priority order
        for handler, _ in self._handlers[event.type]:
            # Check source filter
            if handler in self._source_filters:
                if event.source not in self._source_filters[handler]:
                    continue
                    
            try:
                # Handle both sync and async handlers
                if self._is_async_handler[handler]:
                    # Run async handler in event loop
                    loop = self._ensure_loop()
                    if loop.is_running():
                        # Create task if loop is already running
                        asyncio.create_task(handler(event))
                    else:
                        # Run until complete if loop is not running
                        loop.run_until_complete(handler(event))
                else:
                    # Run sync handler directly
                    handler(event)
            except Exception as e:
                logger.error(f"Error in event handler: {e}")
                
    async def publish_async(self, event: Event) -> None:
        """
        Publish an event to all subscribers asynchronously.
        Returns when all handlers have been called.
        
        Args:
            event: Event to publish
        """
        if event.type not in self._handlers:
            return
            
        tasks = []
        
        # Process handlers in priority order
        for handler, _ in self._handlers[event.type]:
            # Check source filter
            if handler in self._source_filters:
                if event.source not in self._source_filters[handler]:
                    continue
                    
            try:
                # Handle both sync and async handlers
                if self._is_async_handler[handler]:
                    # Schedule async handler
                    tasks.append(handler(event))
                else:
                    # Run sync handler in executor
                    loop = self._ensure_loop()
                    tasks.append(
                        loop.run_in_executor(None, lambda: handler(event))
                    )
            except Exception as e:
                logger.error(f"Error scheduling event handler: {e}")
                
        # Wait for all handlers to complete
        if tasks:
            await asyncio.gather(*tasks)

# Create singleton instance
event_bus = EventBus()
