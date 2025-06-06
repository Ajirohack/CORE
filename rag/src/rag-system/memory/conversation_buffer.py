"""Conversation memory buffer for the RAG system."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from utils.logging import logger
from utils.metrics import collector

class ConversationBuffer:
    """Manages conversation history and context for the RAG system."""
    
    def __init__(
        self,
        max_tokens: int = 2000,
        max_turns: int = 10,
        ttl_minutes: int = 30
    ):
        self.max_tokens = max_tokens
        self.max_turns = max_turns
        self.ttl_minutes = ttl_minutes
        self.conversations: Dict[str, List[Dict[str, Any]]] = {}
        self.metadata: Dict[str, Dict[str, Any]] = {}
        self.logger = logger
        self.metrics = collector
    
    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Add a message to the conversation history."""
        with self.metrics.measure_time("add_message"):
            if conversation_id not in self.conversations:
                self.conversations[conversation_id] = []
                self.metadata[conversation_id] = {
                    "created_at": datetime.utcnow(),
                    "last_updated": datetime.utcnow(),
                    "turn_count": 0
                }
            
            message = {
                "role": role,
                "content": content,
                "timestamp": datetime.utcnow(),
                "metadata": metadata or {}
            }
            
            self.conversations[conversation_id].append(message)
            self.metadata[conversation_id]["turn_count"] += 1
            self.metadata[conversation_id]["last_updated"] = datetime.utcnow()
            
            # Trim if exceeded limits
            if self.metadata[conversation_id]["turn_count"] > self.max_turns:
                self.conversations[conversation_id].pop(0)
                self.metadata[conversation_id]["turn_count"] -= 1
            
            return True
    
    async def get_conversation_history(
        self,
        conversation_id: str,
        last_n_turns: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve conversation history."""
        if conversation_id not in self.conversations:
            return []
            
        history = self.conversations[conversation_id]
        if last_n_turns:
            history = history[-last_n_turns:]
            
        return history
    
    async def clear_conversation(self, conversation_id: str) -> bool:
        """Clear a conversation's history."""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            del self.metadata[conversation_id]
            return True
        return False
    
    async def get_summary(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation summary and metadata."""
        if conversation_id not in self.metadata:
            return None
            
        meta = self.metadata[conversation_id]
        return {
            "turn_count": meta["turn_count"],
            "duration_minutes": (
                datetime.utcnow() - meta["created_at"]
            ).total_seconds() / 60,
            "last_updated": meta["last_updated"],
            "is_active": self._is_conversation_active(conversation_id)
        }
    
    def _is_conversation_active(self, conversation_id: str) -> bool:
        """Check if conversation is still active based on TTL."""
        if conversation_id not in self.metadata:
            return False
            
        last_updated = self.metadata[conversation_id]["last_updated"]
        minutes_elapsed = (
            datetime.utcnow() - last_updated
        ).total_seconds() / 60
        
        return minutes_elapsed <= self.ttl_minutes