"""
Token Management Module for RAG System

This module provides utilities for counting tokens, managing context window limits,
and optimizing document chunks to fit within context windows.
"""

from typing import List, Dict, Any, Optional
import logging
import tiktoken

logger = logging.getLogger(__name__)

class TokenManager:
    """
    Utility class for token counting and context window management.
    
    This class helps ensure that text content fits within LLM context windows
    by counting tokens and truncating content as necessary.
    """
    
    def __init__(self, model_name: str = "gpt-4"):
        """
        Initialize the token manager with a specific model tokenizer.
        
        Args:
            model_name (str): Name of the model to use for tokenization
        """
        self.model_name = model_name
        try:
            self.tokenizer = tiktoken.encoding_for_model(model_name)
        except KeyError:
            logger.warning(f"Model {model_name} not found, falling back to cl100k_base encoding")
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        # Set default context window sizes for common models
        self.model_max_tokens = self._get_model_max_tokens(model_name)
    
    def _get_model_max_tokens(self, model_name: str) -> int:
        """
        Get the maximum context window size for a given model.
        
        Args:
            model_name (str): Model name
            
        Returns:
            int: Maximum context window size in tokens
        """
        model_limits = {
            "gpt-3.5-turbo": 16385,
            "gpt-4": 8192,
            "gpt-4-turbo": 128000,
            "claude-3-opus": 200000,
            "claude-3-sonnet": 180000,
            "claude-3-haiku": 100000,
            "llama3": 8192,
        }
        return model_limits.get(model_name, 4096)  # Default to 4K if unknown
    
    def count_tokens(self, text: str) -> int:
        """
        Count the number of tokens in a text string.
        
        Args:
            text (str): Text to count tokens for
            
        Returns:
            int: Number of tokens
        """
        if not text:
            return 0
        return len(self.tokenizer.encode(text))
    
    def truncate_to_token_limit(self, text: str, max_tokens: int) -> str:
        """
        Truncate text to fit within a token limit.
        
        Args:
            text (str): Text to truncate
            max_tokens (int): Maximum number of tokens allowed
            
        Returns:
            str: Truncated text that fits within token limit
        """
        tokens = self.tokenizer.encode(text)
        if len(tokens) <= max_tokens:
            return text
            
        truncated_tokens = tokens[:max_tokens]
        return self.tokenizer.decode(truncated_tokens)
    
    def fit_documents_to_context(
        self, 
        docs: List[Dict[str, Any]], 
        system_message: str,
        question: str,
        max_context_window: int = None,
        buffer_tokens: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Fit documents into available context window.
        
        This method ensures that the combined length of all documents,
        plus the system message and user question, fits within the
        model's context window.
        
        Args:
            docs (List[Dict]): List of document dictionaries with 'content' fields
            system_message (str): System message to include in prompt
            question (str): User question to include in prompt
            max_context_window (int, optional): Maximum context window size. 
                                               If None, use the model's default.
            buffer_tokens (int): Reserve tokens for response generation
            
        Returns:
            List[Dict]: List of documents that fit in the context window,
                       potentially with some truncated
        """
        if max_context_window is None:
            max_context_window = self.model_max_tokens
        
        # Calculate tokens in system message and question
        available_tokens = max_context_window - buffer_tokens
        system_tokens = self.count_tokens(system_message)
        question_tokens = self.count_tokens(question)
        
        available_tokens -= system_tokens
        available_tokens -= question_tokens
        
        logger.debug(f"Available tokens for documents: {available_tokens}")
        
        if available_tokens <= 0:
            logger.warning("No tokens available for documents after accounting for system message and question")
            return []
        
        result_docs = []
        current_tokens = 0
        
        # Sort docs by relevance (assuming they're already sorted)
        for doc in docs:
            doc_tokens = self.count_tokens(doc['content'])
            
            # If this document would fit completely
            if current_tokens + doc_tokens <= available_tokens:
                result_docs.append(doc)
                current_tokens += doc_tokens
                logger.debug(f"Added document with {doc_tokens} tokens, total: {current_tokens}/{available_tokens}")
            else:
                # If we can fit a truncated version
                remaining_tokens = available_tokens - current_tokens
                if remaining_tokens > 100:  # Only truncate if we can fit a meaningful chunk
                    truncated_content = self.truncate_to_token_limit(
                        doc['content'], remaining_tokens
                    )
                    doc_copy = doc.copy()
                    doc_copy['content'] = truncated_content
                    doc_copy['truncated'] = True
                    result_docs.append(doc_copy)
                    logger.debug(f"Added truncated document with {remaining_tokens} tokens")
                
                # Stop adding documents as we've filled the context window
                break
                
        logger.info(f"Fitted {len(result_docs)} documents into context window, using {current_tokens}/{available_tokens} tokens")
        return result_docs
    
    def truncate_context(self, context: str, max_tokens: int) -> str:
        """
        Truncate a context string to fit within max_tokens.
        
        Args:
            context (str): The context string to truncate
            max_tokens (int): Maximum number of tokens allowed
            
        Returns:
            str: Truncated context that fits within token limit
        """
        # Simple implementation: just truncate the whole context
        return self.truncate_to_token_limit(context, max_tokens)
        
    def format_context_with_sources(self, 
                                  filtered_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Format filtered documents into a context string with tracked sources.
        
        Args:
            filtered_docs: List of documents that fit in context window
            
        Returns:
            Dict with "context" string and "sources" metadata
        """
        context_parts = []
        sources = []
        
        for i, doc in enumerate(filtered_docs):
            # Extract source information
            source = "Unknown"
            if "metadata" in doc:
                source = doc["metadata"].get("source", doc["metadata"].get("filename", "Unknown"))
            
            # Add source to sources list if not already there
            source_info = {
                "id": i+1,
                "source": source,
                "truncated": doc.get("truncated", False)
            }
            sources.append(source_info)
            
            # Format document with source reference
            doc_text = f"[Document {i+1}, Source: {source}]\n{doc['content']}\n"
            context_parts.append(doc_text)
        
        return {
            "context": "\n".join(context_parts),
            "sources": sources
        }