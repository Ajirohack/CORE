"""
Enhanced event bus using Redis pub/sub for async event distribution with 
prioritization, persistence, and event correlation capabilities.
"""
import redis
import json
import threading
import asyncio
import uuid
import logging
import time
from typing import Dict, Any, List, Callable, Optional, Union
from datetime import datetime
from prometheus_client import Counter, Histogram

logger = logging.getLogger(__name__)

# Prometheus metrics
EVENTS_PUBLISHED = Counter('archivist_events_published', 'Number of events published', ['event_type'])
EVENTS_ERRORS = Counter('archivist_events_errors', 'Number of event bus errors', ['event_type'])
EVENTS_PUBLISH_DURATION = Histogram('archivist_events_publish_duration_seconds', 'Duration of event publishing', ['event_type'])

class EventPriority:
    """Event priority levels"""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3

class EventStatus:
    """Event processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class EventTaxonomy:
    """Event type taxonomy"""
    # System events
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_ERROR = "system.error"
    SYSTEM_WARNING = "system.warning"
    SYSTEM_PERCEPTION = "system.perception"
    
    # User events
    USER_INTERACTION = "user.interaction"
    USER_CONNECTED = "user.connected"
    USER_DISCONNECTED = "user.disconnected"
    USER_PREFERENCE_UPDATED = "user.preference.updated"
    
    # Cognitive events
    COGNITIVE_CYCLE_START = "cognitive.cycle.started"
    COGNITIVE_CYCLE_COMPLETE = "cognitive.cycle.completed"
    COGNITIVE_INSIGHT = "cognitive.insight"
    
    # Memory events
    MEMORY_STORED = "memory.stored"
    MEMORY_RETRIEVED = "memory.retrieved"
    MEMORY_CONSOLIDATED = "memory.consolidated"
    MEMORY_FORGOTTEN = "memory.forgotten"
    
    # Reasoning events
    REASONING_REQUEST = "reasoning.request"
    REASONING_COMPLETE = "reasoning.complete"
    REASONING_ERROR = "reasoning.error"
    
    # Knowledge events
    KNOWLEDGE_UPDATED = "knowledge.updated"
    KNOWLEDGE_QUERY = "knowledge.query"
    KNOWLEDGE_INGESTED = "knowledge.ingested"
    KNOWLEDGE_SYNTHESIZED = "knowledge.synthesized"
    
    # Task events
    TASK_NEW = "task.new"
    TASK_STARTED = "task.started"
    TASK_COMPLETE = "task.complete"
    TASK_FAILED = "task.failed"
    TASK_CANCELED = "task.canceled"
    
    # Integration events
    INTEGRATION_TRIGGER = "integration.trigger"
    INTEGRATION_RESULT = "integration.result"
    INTEGRATION_ERROR = "integration.error"

class Event:
    """Enhanced event object with metadata and processing state"""
    
    def __init__(
        self, 
        event_type: str, 
        data: Dict[str, Any], 
        priority: int = EventPriority.NORMAL,
        correlation_id: Optional[str] = None,
        source: str = "system"
    ):
        self.id = str(uuid.uuid4())
        self.type = event_type
        self.data = data
        self.priority = priority
        self.correlation_id = correlation_id or self.id
        self.source = source
        self.created_at = datetime.now().isoformat()
        self.processed_at = None
        self.status = EventStatus.PENDING
        self.error = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary representation"""
        return {
            "id": self.id,
            "type": self.type,
            "data": self.data,
            "priority": self.priority,
            "correlation_id": self.correlation_id,
            "source": self.source,
            "created_at": self.created_at,
            "processed_at": self.processed_at,
            "status": self.status,
            "error": self.error
        }
    
    def to_json(self) -> str:
        """Convert event to JSON string"""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, event_dict: Dict[str, Any]) -> 'Event':
        """Create event from dictionary representation"""
        event = cls(
            event_type=event_dict["type"],
            data=event_dict["data"],
            priority=event_dict["priority"],
            correlation_id=event_dict["correlation_id"],
            source=event_dict["source"]
        )
        event.id = event_dict["id"]
        event.created_at = event_dict["created_at"]
        event.processed_at = event_dict["processed_at"]
        event.status = event_dict["status"]
        event.error = event_dict["error"]
        return event
    
    @classmethod
    def from_json(cls, event_json: str) -> 'Event':
        """Create event from JSON string"""
        return cls.from_dict(json.loads(event_json))

class EventBus:
    """
    Advanced event bus with prioritization, persistence, and correlation features.
    """
    
    def __init__(self, redis_url="redis://localhost:6379/0"):
        self.redis = redis.Redis.from_url(redis_url)
        self.pubsub = self.redis.pubsub(ignore_subscribe_messages=True)
        self._subscribers = {}  # Local mapping of callback functions by channel
        self._running = False
        self._listener_thread = None
        self._event_history_max_size = 1000  # Maximum number of events to keep in history
        
        self.metrics = {
            'events_published': 0,
            'events_failed': 0
        }
        self.last_error = None
        self.last_event = None
        self.last_event_time = None

    @property
    def health(self):
        return {
            'metrics': self.metrics,
            'last_error': self.last_error,
            'last_event': self.last_event,
            'last_event_time': self.last_event_time
        }

    def start(self):
        """Start the event bus listener"""
        if self._running:
            return
        
        self._running = True
        self._listener_thread = threading.Thread(target=self._listener_loop, daemon=True)
        self._listener_thread.start()
        logger.info("Event bus started")
        
    def stop(self):
        """Stop the event bus listener"""
        self._running = False
        if self._listener_thread:
            self._listener_thread.join(timeout=2.0)
        logger.info("Event bus stopped")
        
    async def publish(self, event_type: str, data: Dict[str, Any], priority: int = EventPriority.NORMAL, 
                      correlation_id: Optional[str] = None, source: str = "system") -> str:
        """
        Publish an event to the bus with enhanced metadata
        
        Returns the event ID
        """
        with EVENTS_PUBLISH_DURATION.labels(event_type=event_type).time():
            try:
                # Create event object
                event = Event(
                    event_type=event_type,
                    data=data,
                    priority=priority,
                    correlation_id=correlation_id,
                    source=source
                )
                
                # Store event in history
                await self._store_event(event)
                
                # Publish to Redis
                self.redis.publish(event_type, event.to_json())
                
                # Add to priority queue if needed
                if priority > EventPriority.NORMAL:
                    await self._add_to_priority_queue(event)
                
                logger.debug(f"Published event: {event_type}, ID: {event.id}")
                EVENTS_PUBLISHED.labels(event_type=event_type).inc()
                return event.id
            except Exception as e:
                logger.error(f"EventBus publish error: {e}")
                EVENTS_ERRORS.labels(event_type=event_type).inc()
                raise
    
    def subscribe(self, channel: str, callback: Callable[[Dict[str, Any]], None]):
        """
        Subscribe to a channel with a callback function
        """
        if channel not in self._subscribers:
            self._subscribers[channel] = []
            self.pubsub.subscribe(channel)
            
        self._subscribers[channel].append(callback)
        logger.debug(f"Subscribed to channel: {channel}")
    
    def unsubscribe(self, channel: str, callback: Optional[Callable] = None):
        """
        Unsubscribe from a channel, optionally specifying a specific callback
        """
        if channel in self._subscribers:
            if callback:
                self._subscribers[channel].remove(callback)
                if not self._subscribers[channel]:
                    self.pubsub.unsubscribe(channel)
                    del self._subscribers[channel]
            else:
                self.pubsub.unsubscribe(channel)
                del self._subscribers[channel]
        
        logger.debug(f"Unsubscribed from channel: {channel}")
    
    async def get_event(self, event_id: str) -> Optional[Event]:
        """
        Retrieve an event by its ID
        """
        event_json = self.redis.get(f"event:{event_id}")
        if event_json:
            return Event.from_json(event_json.decode('utf-8'))
        return None
    
    async def get_related_events(self, correlation_id: str) -> List[Event]:
        """
        Get all events with the same correlation ID
        """
        event_keys = self.redis.smembers(f"correlation:{correlation_id}")
        events = []
        
        for key in event_keys:
            event_json = self.redis.get(key.decode('utf-8'))
            if event_json:
                events.append(Event.from_json(event_json.decode('utf-8')))
        
        return sorted(events, key=lambda e: e.created_at)
    
    async def get_recent_events(self, event_type: Optional[str] = None, 
                                limit: int = 100) -> List[Event]:
        """
        Get recent events, optionally filtered by type
        """
        if event_type:
            event_keys = self.redis.zrange(f"events_by_type:{event_type}", 0, limit-1, desc=True)
        else:
            event_keys = self.redis.zrange("events", 0, limit-1, desc=True)
            
        events = []
        for key in event_keys:
            event_json = self.redis.get(key.decode('utf-8'))
            if event_json:
                events.append(Event.from_json(event_json.decode('utf-8')))
        
        return events
    
    def _listener_loop(self):
        """
        Background thread that listens for messages
        """
        self.pubsub.subscribe(*self._subscribers.keys())
        
        while self._running:
            message = self.pubsub.get_message(timeout=0.1)
            if message and message['type'] == 'message':
                channel = message['channel'].decode('utf-8')
                data = message['data'].decode('utf-8')
                self._process_message(channel, data)
        
        self.pubsub.close()
    
    def _process_message(self, channel: str, data: str):
        """
        Process a message received from Redis
        """
        try:
            # Parse the event
            event = Event.from_json(data)
            
            # Mark as processing
            event.status = EventStatus.PROCESSING
            self.redis.set(f"event:{event.id}", event.to_json())
            
            # Dispatch to subscribers
            if channel in self._subscribers:
                for callback in self._subscribers[channel]:
                    try:
                        callback(event.data)
                    except Exception as e:
                        logger.error(f"Error in event callback for {channel}: {str(e)}")
            
            # Mark as completed
            event.status = EventStatus.COMPLETED
            event.processed_at = datetime.now().isoformat()
            self.redis.set(f"event:{event.id}", event.to_json())
            
        except Exception as e:
            logger.error(f"Error processing message on {channel}: {str(e)}")
            
            # Try to mark event as failed if we can parse it
            try:
                event = Event.from_json(data)
                event.status = EventStatus.FAILED
                event.error = str(e)
                event.processed_at = datetime.now().isoformat()
                self.redis.set(f"event:{event.id}", event.to_json())
            except:
                pass
    
    async def _store_event(self, event: Event):
        """
        Store an event in Redis with appropriate indices
        """
        # Store the event itself
        self.redis.set(f"event:{event.id}", event.to_json())
        
        # Add to event history with timestamp for sorting
        timestamp = datetime.fromisoformat(event.created_at).timestamp()
        self.redis.zadd("events", {f"event:{event.id}": timestamp})
        
        # Add to type-specific event history
        self.redis.zadd(f"events_by_type:{event.type}", {f"event:{event.id}": timestamp})
        
        # Add to correlation index
        self.redis.sadd(f"correlation:{event.correlation_id}", f"event:{event.id}")
        
        # Set expiration for historical events if needed
        await self._trim_event_history()
    
    async def _add_to_priority_queue(self, event: Event):
        """
        Add an event to the priority processing queue
        """
        timestamp = datetime.fromisoformat(event.created_at).timestamp()
        # Using priority as score multiplier to ensure higher priority events come first
        score = timestamp + (1000000 * (EventPriority.CRITICAL - event.priority))
        self.redis.zadd("priority_queue", {f"event:{event.id}": score})
    
    async def _trim_event_history(self):
        """
        Remove old events to prevent unlimited growth of the history
        """
        # Trim the main events sorted set
        self.redis.zremrangebyrank("events", 0, -self._event_history_max_size-1)
        
        # Trim type-specific event histories
        for key in self.redis.keys("events_by_type:*"):
            self.redis.zremrangebyrank(key.decode('utf-8'), 0, -self._event_history_max_size-1)
