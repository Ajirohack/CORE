"""
Base LLM provider class for the RAG system
"""

import logging
from typing import Dict, Any, Optional, List
import os
import requests

logger = logging.getLogger(__name__)

class BaseLLMProvider:
    """Base class for all LLM providers"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the LLM provider
        
        Args:
            config: Configuration dictionary for the provider
        """
        self.config = config or {}
    
    def generate_with_context(
        self, 
        prompt: str, 
        context: str, 
        system_message: Optional[str] = None,
        temperature: float = 0.0
    ) -> str:
        """
        Generate a response based on the prompt and context
        
        Args:
            prompt: The user's question or prompt
            context: The context retrieved from the RAG system
            system_message: Optional system message to guide the LLM
            temperature: Temperature parameter for response generation
            
        Returns:
            The generated response as a string
        """
        raise NotImplementedError("Subclasses must implement generate_with_context")
    
    def generate(
        self, 
        prompt: str, 
        system_message: Optional[str] = None,
        temperature: float = 0.0
    ) -> str:
        """
        Generate a response based only on the prompt
        
        Args:
            prompt: The user's question or prompt
            system_message: Optional system message to guide the LLM
            temperature: Temperature parameter for response generation
            
        Returns:
            The generated response as a string
        """
        raise NotImplementedError("Subclasses must implement generate")

class GroqProvider(BaseLLMProvider):
    def __init__(self):
        super().__init__()
        self.api_key = os.environ.get("GROQ_API_KEY")
        self.model = os.environ.get("GROQ_MODEL", "llama3-8b-8192")
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"

    def generate_with_context(self, prompt, context, system_message=None, temperature=0.0):
        if not system_message:
            system_message = (
                "You are a helpful AI assistant answering questions based on the provided context. "
                "If the context doesn't contain relevant information to answer the question, say so."
            )
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": f"Context information:\n{context}\n\nQuestion: {prompt}"}
            ],
            "temperature": temperature
        }
        response = requests.post(self.api_url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    def generate(self, prompt, system_message=None, temperature=0.0):
        # For direct prompt (no context)
        return self.generate_with_context(prompt, context="", system_message=system_message, temperature=temperature)

def get_llm_provider(provider_name=None):
    # Only Groq is implemented here for your config
    return GroqProvider()