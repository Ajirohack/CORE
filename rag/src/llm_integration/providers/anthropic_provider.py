"""
Anthropic LLM provider implementation for Claude models
"""

import os
import logging
from typing import Dict, Any, Optional, List

# Import optional dependency
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from core.rag_system.llm_integration.llm_provider import BaseLLMProvider

logger = logging.getLogger(__name__)

class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude provider implementation"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the Anthropic provider"""
        super().__init__(config)
        
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("Anthropic package not installed. Please install it with 'pip install anthropic'")
        
        # Get configuration
        self.api_key = os.environ.get("ANTHROPIC_API_KEY", "") or self.config.get("api_key", "")
        self.model = os.environ.get("ANTHROPIC_MODEL", "claude-3-sonnet-20240229") or self.config.get("model", "claude-3-sonnet-20240229")
        self.max_tokens = self.config.get("max_tokens", 1024)
        
        if not self.api_key:
            raise ValueError("Anthropic API key not found. Set ANTHROPIC_API_KEY environment variable or provide in config.")
        
        # Initialize anthropic client
        self.client = anthropic.Anthropic(api_key=self.api_key)
        
        logger.info(f"Initialized Anthropic provider with model: {self.model}")
    
    def generate_with_context(
        self, 
        prompt: str, 
        context: str, 
        system_message: Optional[str] = None,
        temperature: float = 0.0
    ) -> str:
        """
        Generate a response based on the prompt and context using Anthropic Claude
        
        Args:
            prompt: The user's question or prompt
            context: The context retrieved from the RAG system
            system_message: Optional system message to guide the LLM
            temperature: Temperature parameter for response generation
            
        Returns:
            The generated response as a string
        """
        if not system_message:
            system_message = (
                "You are a helpful AI assistant answering questions based on the provided context. "
                "If the context doesn't contain relevant information to answer the question, say so."
            )
        
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=temperature,
                system=system_message,
                messages=[
                    {
                        "role": "user",
                        "content": f"Context information:\n{context}\n\nQuestion: {prompt}"
                    }
                ]
            )
            
            return message.content[0].text
            
        except Exception as e:
            logger.error(f"Anthropic API error: {str(e)}")
            return f"Error: Failed to generate response from Claude: {str(e)}"
    
    def generate(
        self, 
        prompt: str, 
        system_message: Optional[str] = None,
        temperature: float = 0.0
    ) -> str:
        """
        Generate a response based only on the prompt using Anthropic Claude
        
        Args:
            prompt: The user's question or prompt
            system_message: Optional system message to guide the LLM
            temperature: Temperature parameter for response generation
            
        Returns:
            The generated response as a string
        """
        try:
            if not system_message:
                system_message = "You are a helpful AI assistant."
                
            message = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=temperature,
                system=system_message,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            return message.content[0].text
            
        except Exception as e:
            logger.error(f"Anthropic API error: {str(e)}")
            return f"Error: Failed to generate response from Claude: {str(e)}"