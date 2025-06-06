"""
Context Manager Module for RAG System
Handles token-aware context window management for LLM prompting
"""

import logging
from typing import Dict, List, Any, Optional, Union
import re
from core.rag_system.memory.conversation_memory import ConversationMemory

logger = logging.getLogger(__name__)

class ContextManager:
    """
    Manages context window for LLM interactions
    
    Features:
    - Token counting and context truncation
    - Context selection based on relevance
    - Prompt template management
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the context manager
        
        Args:
            config: Configuration for context management
        """
        self.config = config or {}
        
        # Configure context limits
        self.max_context_tokens = self.config.get("max_context_tokens", 8000)
        self.max_response_tokens = self.config.get("max_response_tokens", 1000)
        self.token_buffer = self.config.get("token_buffer", 200)  # Safety buffer
        
        # Calculated max tokens for context (excluding system prompt and buffer)
        self.effective_max_tokens = self.max_context_tokens - self.max_response_tokens - self.token_buffer
        
        # Initialize token counter
        self.token_counter = SimpleTokenCounter()
        
        logger.info("Context manager initialized")
    
    def format_rag_prompt(
        self,
        query: str,
        context_docs: List[Dict[str, Any]],
        conversation_memory: Optional[ConversationMemory] = None,
        system_prompt: Optional[str] = None,
        additional_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Format a RAG prompt with context management
        
        Args:
            query: User query
            context_docs: Retrieved context documents
            conversation_memory: Optional conversation memory
            system_prompt: Optional system prompt
            additional_context: Any additional context to include
            
        Returns:
            Dictionary with prompt components
        """
        logger.info(f"Formatting RAG prompt for query: {query[:50]}...")
        
        # Start with default system prompt if not provided
        if system_prompt is None:
            system_prompt = self._get_default_system_prompt()
        
        # Track token usage
        token_usage = {
            "system_prompt": self.token_counter.count_tokens(system_prompt),
            "query": self.token_counter.count_tokens(query),
            "response_allocation": self.max_response_tokens,
            "buffer": self.token_buffer
        }
        
        # Calculate remaining tokens for context and conversation
        remaining_tokens = self.max_context_tokens - sum(token_usage.values())
        
        # Format conversation context if available
        conversation_context = ""
        if conversation_memory:
            raw_conversation = conversation_memory.get_conversation_context()
            conversation_tokens = self.token_counter.count_tokens(raw_conversation)
            
            # Allocate up to 30% of remaining tokens for conversation context
            conversation_token_limit = min(remaining_tokens * 0.3, conversation_tokens)
            
            if conversation_tokens > conversation_token_limit:
                # Truncate conversation context if needed
                conversation_context = self._truncate_text(
                    raw_conversation, 
                    int(conversation_token_limit)
                )
            else:
                conversation_context = raw_conversation
                
            remaining_tokens -= self.token_counter.count_tokens(conversation_context)
        
        # Add additional context if provided
        additional_formatted = ""
        if additional_context:
            additional_tokens = self.token_counter.count_tokens(additional_context)
            
            # Allocate up to 10% of remaining tokens for additional context
            additional_token_limit = min(remaining_tokens * 0.1, additional_tokens)
            
            if additional_tokens > additional_token_limit:
                additional_formatted = self._truncate_text(
                    additional_context,
                    int(additional_token_limit)
                )
            else:
                additional_formatted = additional_context
                
            remaining_tokens -= self.token_counter.count_tokens(additional_formatted)
        
        # Format retrieved documents
        context_text = self._format_context_documents(context_docs, remaining_tokens)
        
        # Update token usage
        token_usage.update({
            "conversation_context": self.token_counter.count_tokens(conversation_context),
            "additional_context": self.token_counter.count_tokens(additional_formatted),
            "retrieved_context": self.token_counter.count_tokens(context_text)
        })
        
        # Create prompt components dictionary
        prompt_components = {
            "system_prompt": system_prompt,
            "conversation_context": conversation_context,
            "additional_context": additional_formatted,
            "retrieved_context": context_text,
            "query": query,
            "token_usage": token_usage,
            "total_tokens": sum(token_usage.values())
        }
        
        return prompt_components
    
    def _format_context_documents(
        self,
        documents: List[Dict[str, Any]],
        max_tokens: int
    ) -> str:
        """
        Format context documents within token limits
        
        Args:
            documents: List of context documents
            max_tokens: Maximum tokens for the formatted context
            
        Returns:
            Formatted context text
        """
        if not documents:
            return ""
        
        formatted_docs = []
        total_tokens = 0
        
        for i, doc in enumerate(documents):
            # Format document with metadata
            source = doc.get("source", f"Document {i+1}")
            content = doc.get("content", "")
            
            formatted_doc = f"[SOURCE {i+1}: {source}]\n{content}\n"
            doc_tokens = self.token_counter.count_tokens(formatted_doc)
            
            # Add if within token limit
            if total_tokens + doc_tokens <= max_tokens:
                formatted_docs.append(formatted_doc)
                total_tokens += doc_tokens
            else:
                # Try to fit a truncated version
                truncation_limit = max_tokens - total_tokens - 30  # Account for truncation notice
                if truncation_limit > 100:  # Only add if we can include reasonable content
                    truncated_content = self._truncate_text(content, truncation_limit)
                    truncated_doc = f"[SOURCE {i+1}: {source} (truncated)]\n{truncated_content}\n"
                    formatted_docs.append(truncated_doc)
                break
        
        # Format the final context block
        if formatted_docs:
            context_header = "## RETRIEVED CONTEXT\n"
            context_text = context_header + "\n".join(formatted_docs)
        else:
            context_text = "## RETRIEVED CONTEXT\nNo relevant context found."
        
        return context_text
    
    def _truncate_text(self, text: str, max_tokens: int) -> str:
        """
        Truncate text to fit within token limit
        
        Args:
            text: Text to truncate
            max_tokens: Maximum tokens allowed
            
        Returns:
            Truncated text
        """
        if self.token_counter.count_tokens(text) <= max_tokens:
            return text
        
        # Approximate tokens to characters (roughly 4 chars per token)
        char_estimate = max_tokens * 4
        
        # Truncate with some buffer room
        truncated = text[:char_estimate]
        
        # Check if we need to trim more
        while self.token_counter.count_tokens(truncated) > max_tokens and len(truncated) > 10:
            truncated = truncated[:int(len(truncated) * 0.9)]
        
        # Add truncation notice
        truncated += "\n[... text truncated due to token limits ...]"
        
        return truncated
    
    def _get_default_system_prompt(self) -> str:
        """
        Get the default system prompt for RAG
        
        Returns:
            Default system prompt
        """
        return """You are a helpful assistant that provides accurate information based on the given context.
When answering questions:
1. Only use information from the provided context
2. If the context doesn't contain the answer, say "I don't have enough information to answer this question"
3. Cite your sources by referring to the source numbers [SOURCE X]
4. Be concise and clear in your explanations
"""


class SimpleTokenCounter:
    """
    Simple token counter for estimating token usage
    
    Note: This is an approximate counter and does not match exactly
    with specific tokenizers used by different LLMs
    """
    
    def __init__(self):
        """Initialize the token counter"""
        pass
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text (approximate)
        
        Args:
            text: Text to count tokens in
            
        Returns:
            Approximate token count
        """
        if not text:
            return 0
            
        # Split on whitespace
        words = text.split()
        
        # Count punctuation as separate tokens
        punctuation_count = len(re.findall(r'[,.;:!?()]', text))
        
        # Special token estimates (e.g., for code blocks, URLs)
        special_token_estimate = len(re.findall(r'http[s]?://\S+', text)) * 5
        special_token_estimate += len(re.findall(r'```.*?```', text, re.DOTALL)) * 3
        
        # Estimate: words + punctuation + special tokens
        return len(words) + punctuation_count + special_token_estimate
