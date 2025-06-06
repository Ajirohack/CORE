"""
Conversation Memory Module for RAG System
Manages short-term and long-term memory for conversational RAG
"""

import logging
from typing import Dict, List, Any, Optional, Union
import time
import json
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class ConversationMemory:
    """
    Manages conversation history and memory for RAG system
    
    Features:
    - Short-term memory: Stores recent messages
    - Long-term memory: Stores important information persistently
    - Memory summarization: Condenses older messages
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the conversation memory
        
        Args:
            config: Configuration for memory management
        """
        self.config = config or {}
        
        # Configure memory limits
        self.max_messages = self.config.get("max_messages", 20)
        self.short_term_ttl = self.config.get("short_term_ttl", 3600)  # 1 hour in seconds
        self.importance_threshold = self.config.get("importance_threshold", 0.7)
        
        # Initialize memory stores
        self.messages = []  # List of message dicts
        self.long_term_memory = {}  # Key-value store for persistent information
        self.conversation_summaries = []  # List of conversation summaries
        
        logger.info("Conversation memory initialized")
    
    def add_message(
        self,
        message: str,
        role: str,
        importance: float = 0.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Add a message to conversation memory
        
        Args:
            message: The message content
            role: Role of the message sender (user, assistant, system)
            importance: Importance score (0.0-1.0) for long-term memory
            metadata: Additional message metadata
            
        Returns:
            Message ID
        """
        timestamp = time.time()
        message_id = str(uuid.uuid4())
        
        # Create message object
        message_obj = {
            "id": message_id,
            "content": message,
            "role": role,
            "timestamp": timestamp,
            "datetime": datetime.fromtimestamp(timestamp).isoformat(),
            "importance": importance,
            "metadata": metadata or {}
        }
        
        # Add to messages list
        self.messages.append(message_obj)
        
        # Move to long-term memory if important
        if importance >= self.importance_threshold:
            self._add_to_long_term_memory(message_obj)
        
        # Trim if over limit
        if len(self.messages) > self.max_messages:
            self._summarize_oldest_messages()
        
        logger.debug(f"Added message to memory: {message_id}")
        return message_id
    
    def get_recent_messages(
        self, 
        limit: int = None, 
        roles: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get recent messages from memory
        
        Args:
            limit: Maximum number of messages to return
            roles: Only include messages from these roles
            
        Returns:
            List of message objects
        """
        limit = limit or self.max_messages
        
        # Filter by role if specified
        if roles:
            filtered = [m for m in self.messages if m["role"] in roles]
        else:
            filtered = self.messages
        
        # Return most recent messages up to limit
        return filtered[-limit:]
    
    def get_conversation_context(self, max_tokens: int = 2000) -> str:
        """
        Get formatted conversation context for LLM
        
        Args:
            max_tokens: Maximum number of tokens to include
            
        Returns:
            Formatted conversation history
        """
        # Start with summaries
        context = []
        if self.conversation_summaries:
            context.append("## Previous Conversation Summary")
            context.append(self.conversation_summaries[-1])
            context.append("")
        
        # Add recent messages
        context.append("## Recent Conversation")
        for msg in self.get_recent_messages():
            formatted_msg = f"{msg['role'].capitalize()}: {msg['content']}"
            context.append(formatted_msg)
        
        # Add long-term memory highlights
        context.append("")
        context.append("## Important Information")
        for key, value in self.long_term_memory.items():
            if isinstance(value, dict) and 'content' in value:
                context.append(f"- {value['content']}")
            else:
                context.append(f"- {key}: {value}")
        
        # TODO: Token counting and truncation based on max_tokens
        
        return "\n".join(context)
    
    def _add_to_long_term_memory(self, message: Dict[str, Any]) -> None:
        """
        Add important message to long-term memory
        
        Args:
            message: Message object to add
        """
        key = f"message_{message['id']}"
        self.long_term_memory[key] = {
            "content": message["content"],
            "timestamp": message["timestamp"],
            "importance": message["importance"]
        }
    
    def _summarize_oldest_messages(self, count: int = 5) -> None:
        """
        Summarize oldest messages to make room for new ones
        
        Args:
            count: Number of oldest messages to summarize
        """
        if len(self.messages) <= count:
            return
        
        # Extract oldest messages to summarize
        to_summarize = self.messages[:count]
        
        # Generate summary string
        summary = f"Summary of {count} messages from {to_summarize[0]['datetime']} to {to_summarize[-1]['datetime']}"
        
        # Store summary
        self.conversation_summaries.append(summary)
        
        # Remove summarized messages
        self.messages = self.messages[count:]
        
        logger.info(f"Summarized {count} oldest messages")
    
    def save_state(self) -> Dict[str, Any]:
        """
        Save memory state to dictionary
        
        Returns:
            Memory state dictionary
        """
        return {
            "messages": self.messages,
            "long_term_memory": self.long_term_memory,
            "conversation_summaries": self.conversation_summaries
        }
    
    def load_state(self, state: Dict[str, Any]) -> None:
        """
        Load memory state from dictionary
        
        Args:
            state: Memory state dictionary
        """
        self.messages = state.get("messages", [])
        self.long_term_memory = state.get("long_term_memory", {})
        self.conversation_summaries = state.get("conversation_summaries", [])
        
        logger.info("Loaded conversation memory state")
