"""
Ollama LLM provider implementation
"""

import os
import logging
import requests
import json
from typing import Dict, Any, Optional, List

from core.rag_system.llm_integration.llm_provider import BaseLLMProvider

logger = logging.getLogger(__name__)

class OllamaProvider(BaseLLMProvider):
    """Ollama LLM provider implementation"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the Ollama provider"""
        super().__init__(config)
        
        # Get configuration
        self.base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434") or self.config.get("base_url", "http://localhost:11434")
        self.model = os.environ.get("OLLAMA_MODEL", "llama3") or self.config.get("model", "llama3")
        self.api_url = f"{self.base_url}/api/generate"
        self.timeout = self.config.get("timeout", 120)
        
        logger.info(f"Initialized Ollama provider with model: {self.model} at {self.base_url}")
    
    def generate_with_context(
        self, 
        prompt: str, 
        context: str, 
        system_message: Optional[str] = None,
        temperature: float = 0.0
    ) -> str:
        """
        Generate a response based on the prompt and context using Ollama
        
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
            payload = {
                "model": self.model,
                "prompt": f"{system_message}\n\nContext information:\n{context}\n\nQuestion: {prompt}",
                "temperature": temperature
            }
            
            response = requests.post(
                self.api_url,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                logger.error(f"Ollama API error: {response.status_code}, {response.text}")
                return f"Error: Failed to generate response from Ollama (Status: {response.status_code})"
            
            response_text = response.json().get("response", "")
            return response_text
            
        except Exception as e:
            logger.error(f"Ollama API error: {str(e)}")
            return f"Error: Failed to generate response from Ollama: {str(e)}"
    
    def generate(
        self, 
        prompt: str, 
        system_message: Optional[str] = None,
        temperature: float = 0.0
    ) -> str:
        """
        Generate a response based only on the prompt using Ollama
        
        Args:
            prompt: The user's question or prompt
            system_message: Optional system message to guide the LLM
            temperature: Temperature parameter for response generation
            
        Returns:
            The generated response as a string
        """
        try:
            full_prompt = prompt
            if system_message:
                full_prompt = f"{system_message}\n\n{prompt}"
                
            payload = {
                "model": self.model,
                "prompt": full_prompt,
                "temperature": temperature
            }
            
            response = requests.post(
                self.api_url,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                logger.error(f"Ollama API error: {response.status_code}, {response.text}")
                return f"Error: Failed to generate response from Ollama (Status: {response.status_code})"
            
            response_text = response.json().get("response", "")
            return response_text
            
        except Exception as e:
            logger.error(f"Ollama API error: {str(e)}")
            return f"Error: Failed to generate response from Ollama: {str(e)}"