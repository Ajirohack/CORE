"""
OpenRouter LLM provider implementation
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

class OpenRouterProvider(BaseLLMProvider):
    """OpenRouter provider implementation for accessing multiple LLM providers via a single API"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the OpenRouter provider"""
        super().__init__(config)
        
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI package not installed. Please install it with 'pip install openai'")
        
        # Get configuration
        self.api_key = os.environ.get("OPENROUTER_API_KEY", "") or self.config.get("api_key", "")
        self.model = os.environ.get("OPENROUTER_MODEL", "anthropic/claude-3-opus") or self.config.get("model", "anthropic/claude-3-opus")
        self.max_tokens = self.config.get("max_tokens", 1024)
        
        if not self.api_key:
            raise ValueError("OpenRouter API key not found. Set OPENROUTER_API_KEY environment variable or provide in config.")
        
        # Initialize client with OpenRouter base URL
        self.client = openai.OpenAI(
            api_key=self.api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        
        # Set default headers for OpenRouter
        self.headers = {
            "HTTP-Referer": os.environ.get("OPENROUTER_SITE_URL", "https://spacewh.com"),
            "X-Title": "Space WH RAG System",
        }
        
        logger.info(f"Initialized OpenRouter provider with model: {self.model}")
    
    def generate_with_context(
        self, 
        prompt: str, 
        context: str, 
        system_message: Optional[str] = None,
        temperature: float = 0.0
    ) -> str:
        """
        Generate a response based on the prompt and context using OpenRouter
        
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
                temperature=temperature,
                max_tokens=self.max_tokens,
                headers=self.headers
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenRouter API error: {str(e)}")
            return f"Error: Failed to generate response from OpenRouter: {str(e)}"
    
    def generate(
        self, 
        prompt: str, 
        system_message: Optional[str] = None,
        temperature: float = 0.0
    ) -> str:
        """
        Generate a response based only on the prompt using OpenRouter
        
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
                temperature=temperature,
                max_tokens=self.max_tokens,
                headers=self.headers
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenRouter API error: {str(e)}")
            return f"Error: Failed to generate response from OpenRouter: {str(e)}"