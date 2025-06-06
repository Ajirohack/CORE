"""
Memory Orchestrator Module
Provides advanced memory and context management capabilities for the RAG system
"""

import logging
from typing import Dict, List, Any, Optional, Union
import datetime
import json

from core.rag_system.memory.conversation_memory import ConversationMemory
from core.rag_system.memory.context_manager import ContextManager

logger = logging.getLogger(__name__)

class MemoryOrchestrator:
    """
    Orchestrates memory and context operations across the RAG system
    
    Features:
    - Long-term and short-term memory management
    - Multi-faceted memory types (semantic, episodic, factual)
    - Context prioritization based on relevance and recency
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the memory orchestrator
        
        Args:
            config: Configuration for the memory orchestrator
        """
        self.config = config or {}
        
        # Initialize related components
        self.context_manager = ContextManager(config=config)
        
        # Memory settings
        self.max_memory_items = self.config.get("max_memory_items", 100)
        self.recency_weight = self.config.get("recency_weight", 0.3)
        self.relevance_weight = self.config.get("relevance_weight", 0.7)
        self.memory_decay_factor = self.config.get("memory_decay_factor", 0.95)
        
        # Initialize memory stores
        self.short_term_memory = []  # Recent interactions (cleared between sessions)
        self.long_term_memory = []   # Important facts and insights (persistent)
        self.working_memory = []     # Current context items
        
        # For tracking time
        self.session_start = datetime.datetime.now()
        
        logger.info("Memory orchestrator initialized")
    
    def add_to_short_term_memory(self, item: Dict[str, Any]) -> None:
        """
        Add an item to short-term memory
        
        Args:
            item: Memory item (should have 'content' and 'timestamp' at minimum)
        """
        if "timestamp" not in item:
            item["timestamp"] = datetime.datetime.now().isoformat()
            
        if "importance" not in item:
            item["importance"] = 0.5  # Default medium importance
            
        self.short_term_memory.append(item)
        
        # Trim if needed
        if len(self.short_term_memory) > self.max_memory_items:
            # Remove least important items first
            self.short_term_memory.sort(key=lambda x: x.get("importance", 0))
            self.short_term_memory = self.short_term_memory[-self.max_memory_items:]
    
    def add_to_long_term_memory(self, item: Dict[str, Any], importance: float = 0.8) -> None:
        """
        Add an important item to long-term memory
        
        Args:
            item: Memory item
            importance: How important this item is (0.0-1.0)
        """
        if "timestamp" not in item:
            item["timestamp"] = datetime.datetime.now().isoformat()
            
        item["importance"] = importance
        self.long_term_memory.append(item)
        
        # Trim if needed - keep most important items
        if len(self.long_term_memory) > self.max_memory_items * 2:
            self.long_term_memory.sort(key=lambda x: x.get("importance", 0))
            self.long_term_memory = self.long_term_memory[-self.max_memory_items*2:]
    
    def update_working_memory(self, query: str, context_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Update working memory with relevant items from short and long-term memory
        
        Args:
            query: Current user query
            context_docs: Retrieved context documents
            
        Returns:
            Enhanced context with memory items
        """
        # Start with retrieved documents
        enhanced_context = context_docs.copy()
        
        # Add relevant items from memory
        memory_items = self._get_relevant_memory_items(query)
        
        # Calculate available token space
        available_tokens = self.context_manager.effective_max_tokens
        
        # Add memory items until we hit the token limit
        for item in memory_items:
            item_tokens = len(item.get("content", "").split())
            if item_tokens < available_tokens:
                enhanced_context.append({
                    "id": item.get("id", f"memory-{len(enhanced_context)}"),
                    "content": item.get("content", ""),
                    "metadata": {
                        "source": "memory",
                        "type": item.get("type", "general"),
                        "importance": item.get("importance", 0.5)
                    }
                })
                available_tokens -= item_tokens
            else:
                break
                
        return enhanced_context
    
    def _get_relevant_memory_items(self, query: str) -> List[Dict[str, Any]]:
        """
        Get memory items relevant to the current query
        
        Args:
            query: Current user query
            
        Returns:
            List of relevant memory items
        """
        # Combine memory sources
        all_memory = self.short_term_memory + self.long_term_memory
        
        # Skip if no memory
        if not all_memory:
            return []
            
        # Calculate simple relevance scores
        # In a production system, use embeddings for semantic similarity
        scored_items = []
        query_words = set(query.lower().split())
        
        for item in all_memory:
            # Calculate recency (0-1, higher is more recent)
            timestamp = datetime.datetime.fromisoformat(item.get("timestamp", self.session_start.isoformat()))
            seconds_ago = (datetime.datetime.now() - timestamp).total_seconds()
            recency = max(0, 1.0 - (seconds_ago / (3600 * 24)))  # 1.0 for now, 0.0 for 24+ hours ago
            
            # Calculate simple relevance (word overlap)
            content = item.get("content", "")
            content_words = set(content.lower().split())
            
            if not query_words or not content_words:
                relevance = 0.0
            else:
                overlap = len(query_words.intersection(content_words))
                relevance = min(1.0, overlap / len(query_words) if query_words else 0)
                
            # Calculate importance considering recency and relevance
            importance = (
                self.recency_weight * recency +
                self.relevance_weight * relevance
            ) * item.get("importance", 0.5)
            
            scored_items.append({
                **item,
                "_score": importance
            })
            
        # Sort by score and return top items
        scored_items.sort(key=lambda x: x.get("_score", 0), reverse=True)
        return scored_items[:10]  # Return top 10 items
    
    def apply_memory_decay(self) -> None:
        """
        Apply time-based decay to memory importance
        Should be called periodically (e.g., once per day)
        """
        for item in self.short_term_memory:
            item["importance"] = item.get("importance", 0.5) * self.memory_decay_factor
            
        # Clean up items below threshold
        threshold = 0.1
        self.short_term_memory = [item for item in self.short_term_memory 
                                 if item.get("importance", 0) > threshold]
                                 
        # Long-term memory decays more slowly
        for item in self.long_term_memory:
            item["importance"] = item.get("importance", 0.5) * (self.memory_decay_factor + 0.03)
    
    def extract_insights_for_long_term_memory(self, conversation: ConversationMemory) -> None:
        """
        Extract important insights from conversation for long-term memory
        
        Args:
            conversation: Conversation memory object
        """
        # In a production system, use an LLM to identify key insights
        # Here we use a simple heuristic - long responses might contain insights
        history = conversation.get_history()
        
        for exchange in history[-5:]:  # Look at recent exchanges
            if "response" in exchange:
                response = exchange["response"]
                
                # Simple heuristic: longer responses might contain important information
                if len(response.split()) > 100:
                    # Add summary to long-term memory
                    # In production, generate an actual summary with an LLM
                    summary = response[:200] + "..." if len(response) > 200 else response
                    self.add_to_long_term_memory({
                        "content": summary,
                        "type": "insight",
                        "source": "conversation",
                        "full_content": response
                    })
    
    def serialize(self) -> Dict[str, Any]:
        """
        Serialize memory state for storage
        
        Returns:
            Dictionary of serialized memory state
        """
        return {
            "short_term_memory": self.short_term_memory,
            "long_term_memory": self.long_term_memory,
            "session_start": self.session_start.isoformat()
        }
    
    def deserialize(self, data: Dict[str, Any]) -> None:
        """
        Restore memory state from serialized data
        
        Args:
            data: Dictionary of serialized memory state
        """
        self.short_term_memory = data.get("short_term_memory", [])
        self.long_term_memory = data.get("long_term_memory", [])
        
        if "session_start" in data:
            self.session_start = datetime.datetime.fromisoformat(data["session_start"])
