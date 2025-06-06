"""
OpenAI LLM provider implementation
"""

import os
import logging
import json
from typing import Dict, Any, Optional, List

# Import optional dependency
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from core.rag_system.llm_integration.llm_provider import BaseLLMProvider

logger = logging.getLogger(__name__)

class OpenaiProvider(BaseLLMProvider):
    """OpenAI provider implementation"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the OpenAI provider"""
        super().__init__(config)
        
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI package not installed. Please install it with 'pip install openai'")
        
        # Get configuration
        self.api_key = os.environ.get("OPENAI_API_KEY", "") or self.config.get("api_key", "")
        self.model = os.environ.get("OPENAI_MODEL", "gpt-4") or self.config.get("model", "gpt-4")
        self.timeout = self.config.get("timeout", 60)
        
        if not self.api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable or provide in config.")
        
        # Initialize openai client
        self.client = openai.OpenAI(api_key=self.api_key)
        
        logger.info(f"Initialized OpenAI provider with model: {self.model}")
    
    def generate_with_context(
        self, 
        prompt: str, 
        context: str, 
        system_message: Optional[str] = None,
        temperature: float = 0.0
    ) -> str:
        """
        Generate a response based on the prompt and context using OpenAI
        
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
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": f"Context information:\n{context}\n\nQuestion: {prompt}"}
            ]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            return f"Error: Failed to generate response from OpenAI: {str(e)}"
    
    def generate(
        self, 
        prompt: str, 
        system_message: Optional[str] = None,
        temperature: float = 0.0
    ) -> str:
        """
        Generate a response based only on the prompt using OpenAI
        
        Args:
            prompt: The user's question or prompt
            system_message: Optional system message to guide the LLM
            temperature: Temperature parameter for response generation
            
        Returns:
            The generated response as a string
        """
        try:
            messages = []
            
            if system_message:
                messages.append({"role": "system", "content": system_message})
            
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI API error: {str(e)}")
            return f"Error: Failed to generate response from OpenAI: {str(e)}"