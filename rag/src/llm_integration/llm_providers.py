"""
LLM Providers Integration Module for RAG System

This module provides integration with various Language Model (LLM) providers:
- OpenAI
- Anthropic Claude
- Ollama (self-hosted)
- OpenRouter
- Groq
- Open Web UI
"""

import os
import logging
import json
from typing import Dict, List, Any, Optional, Union, Callable
from abc import ABC, abstractmethod
import requests

# Setup logging
logger = logging.getLogger(__name__)

class BaseLLMProvider(ABC):
    """Base class for all LLM providers"""
    
    @abstractmethod
    def generate(
        self, 
        prompt: str, 
        system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """Generate a response from the LLM"""
        pass
    
    @abstractmethod
    def generate_with_context(
        self, 
        prompt: str,
        context: str,
        system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """Generate a response from the LLM with context from RAG system"""
        pass


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API integration"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4-turbo"):
        """Initialize OpenAI provider"""
        try:
            from openai import OpenAI
            self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
            if not self.api_key:
                raise ValueError("OpenAI API key not provided")
            
            self.model = model or os.environ.get("OPENAI_MODEL", "gpt-4-turbo")
            self.client = OpenAI(api_key=self.api_key)
            logger.info(f"OpenAI provider initialized with model {self.model}")
        except ImportError:
            logger.error("OpenAI package not installed. Please install with: pip install openai")
            raise
        except Exception as e:
            logger.error(f"Error initializing OpenAI provider: {str(e)}")
            raise
    
    def generate(
        self, 
        prompt: str, 
        system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """Generate a response from OpenAI"""
        try:
            system_content = system_message or "You are a helpful assistant."
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating response from OpenAI: {str(e)}")
            return f"Error generating response: {str(e)}"
    
    def generate_with_context(
        self, 
        prompt: str,
        context: str,
        system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """Generate a response from OpenAI with context"""
        rag_prompt = f"""
        Please answer the following question based on the provided context.
        If the context doesn't contain the information needed to answer the question,
        say "I don't have enough information to answer this question."

        Context:
        {context}

        Question: {prompt}
        """
        
        return self.generate(
            prompt=rag_prompt,
            system_message=system_message,
            temperature=temperature,
            max_tokens=max_tokens
        )


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude API integration"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-haiku-20240307"):
        """Initialize Anthropic provider"""
        try:
            from anthropic import Anthropic
            self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("LLM_API_KEY")
            if not self.api_key:
                raise ValueError("Anthropic API key not provided")
            
            self.model = model or os.environ.get("ANTHROPIC_MODEL", "claude-3-haiku-20240307")
            self.client = Anthropic(api_key=self.api_key)
            logger.info(f"Anthropic provider initialized with model {self.model}")
        except ImportError:
            logger.error("Anthropic package not installed. Please install with: pip install anthropic")
            raise
        except Exception as e:
            logger.error(f"Error initializing Anthropic provider: {str(e)}")
            raise
    
    def generate(
        self, 
        prompt: str, 
        system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """Generate a response from Anthropic Claude"""
        try:
            system_content = system_message or "You are Claude, a helpful AI assistant."
            
            response = self.client.messages.create(
                model=self.model,
                system=system_content,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.content[0].text
        except Exception as e:
            logger.error(f"Error generating response from Anthropic: {str(e)}")
            return f"Error generating response: {str(e)}"
    
    def generate_with_context(
        self, 
        prompt: str,
        context: str,
        system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """Generate a response from Anthropic with context"""
        rag_prompt = f"""
        Please answer the following question based on the provided context.
        If the context doesn't contain the information needed to answer the question,
        say "I don't have enough information to answer this question."

        Context:
        {context}

        Question: {prompt}
        """
        
        return self.generate(
            prompt=rag_prompt,
            system_message=system_message,
            temperature=temperature,
            max_tokens=max_tokens
        )


class OllamaProvider(BaseLLMProvider):
    """Ollama API integration for self-hosted models"""
    
    def __init__(self, base_url: Optional[str] = None, model: str = "llama3"):
        """Initialize Ollama provider"""
        self.base_url = base_url or os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = model or os.environ.get("OLLAMA_MODEL", "llama3")
        logger.info(f"Ollama provider initialized with model {self.model} at {self.base_url}")
    
    def generate(
        self, 
        prompt: str, 
        system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """Generate a response from Ollama"""
        try:
            # Prepare request payload
            payload = {
                "model": self.model,
                "prompt": prompt,
                "temperature": temperature,
                "num_predict": max_tokens
            }
            
            # Add system message if provided
            if system_message:
                payload["system"] = system_message
            
            # Make API request to Ollama
            response = requests.post(f"{self.base_url}/api/generate", json=payload)
            response.raise_for_status()
            
            # Parse response
            result = response.json()
            
            return result.get("response", "No response generated")
        except Exception as e:
            logger.error(f"Error generating response from Ollama: {str(e)}")
            return f"Error generating response: {str(e)}"
    
    def generate_with_context(
        self, 
        prompt: str,
        context: str,
        system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """Generate a response from Ollama with context"""
        rag_prompt = f"""
        Please answer the following question based on the provided context.
        If the context doesn't contain the information needed to answer the question,
        say "I don't have enough information to answer this question."

        Context:
        {context}

        Question: {prompt}
        """
        
        return self.generate(
            prompt=rag_prompt,
            system_message=system_message,
            temperature=temperature,
            max_tokens=max_tokens
        )


class OpenRouterProvider(BaseLLMProvider):
    """OpenRouter API integration for access to multiple providers"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "openai/gpt-4-turbo"):
        """Initialize OpenRouter provider"""
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OpenRouter API key not provided")
        
        self.model = model or os.environ.get("OPENROUTER_MODEL", "openai/gpt-4-turbo")
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        logger.info(f"OpenRouter provider initialized with model {self.model}")
    
    def generate(
        self, 
        prompt: str, 
        system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """Generate a response from OpenRouter"""
        try:
            system_content = system_message or "You are a helpful assistant."
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
                "HTTP-Referer": "https://space-project-rag.example.com",  # Update with your own domain
                "X-Title": "Space Project RAG"  # Update with your application name
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": prompt}
                ],
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            response = requests.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Error generating response from OpenRouter: {str(e)}")
            return f"Error generating response: {str(e)}"
    
    def generate_with_context(
        self, 
        prompt: str,
        context: str,
        system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """Generate a response from OpenRouter with context"""
        rag_prompt = f"""
        Please answer the following question based on the provided context.
        If the context doesn't contain the information needed to answer the question,
        say "I don't have enough information to answer this question."

        Context:
        {context}

        Question: {prompt}
        """
        
        return self.generate(
            prompt=rag_prompt,
            system_message=system_message,
            temperature=temperature,
            max_tokens=max_tokens
        )


class GroqProvider(BaseLLMProvider):
    """Groq API integration for high-performance inference"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "llama3-70b-8192"):
        """Initialize Groq provider"""
        try:
            self.api_key = api_key or os.environ.get("GROQ_API_KEY")
            if not self.api_key:
                raise ValueError("Groq API key not provided")
            
            self.model = model or os.environ.get("GROQ_MODEL", "llama3-70b-8192")
            self.api_url = "https://api.groq.com/openai/v1/chat/completions"
            logger.info(f"Groq provider initialized with model {self.model}")
        except Exception as e:
            logger.error(f"Error initializing Groq provider: {str(e)}")
            raise
    
    def generate(
        self, 
        prompt: str, 
        system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """Generate a response from Groq"""
        try:
            system_content = system_message or "You are a helpful assistant."
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": prompt}
                ],
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            logger.info(f"Sending request to Groq API with model {self.model}")
            response = requests.post(self.api_url, headers=headers, json=payload)
            
            # Log the response status and headers for debugging
            logger.info(f"Groq API response status: {response.status_code}")
            logger.info(f"Groq API response headers: {response.headers}")
            
            # Raise exception for non-200 responses
            response.raise_for_status()
            
            # Parse the response
            result = response.json()
            
            logger.info("Successfully received response from Groq API")
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Error generating response from Groq: {str(e)}")
            return f"Error generating response: {str(e)}"
    
    def generate_with_context(
        self, 
        prompt: str,
        context: str,
        system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """Generate a response from Groq with context"""
        rag_prompt = f"""
        Please answer the following question based on the provided context.
        If the context doesn't contain the information needed to answer the question,
        say "I don't have enough information to answer this question."

        Context:
        {context}

        Question: {prompt}
        """
        
        return self.generate(
            prompt=rag_prompt,
            system_message=system_message,
            temperature=temperature,
            max_tokens=max_tokens
        )


class OpenWebUIProvider(BaseLLMProvider):
    """Open Web UI API integration for Ollama models with OpenAI-compatible interface"""
    
    def __init__(self, base_url: Optional[str] = None, model: str = "default"):
        """Initialize Open Web UI provider"""
        self.base_url = base_url or os.environ.get("OPENWEBUI_BASE_URL", "http://localhost:8000")
        self.model = model or os.environ.get("OPENWEBUI_MODEL", "default")
        self.api_url = f"{self.base_url}/v1/chat/completions"
        logger.info(f"OpenWebUI provider initialized with model {self.model} at {self.base_url}")
    
    def generate(
        self, 
        prompt: str, 
        system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """Generate a response from Open Web UI"""
        try:
            system_content = system_message or "You are a helpful assistant."
            
            headers = {
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_content},
                    {"role": "user", "content": prompt}
                ],
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            
            response = requests.post(self.api_url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            return result["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Error generating response from Open Web UI: {str(e)}")
            return f"Error generating response: {str(e)}"
    
    def generate_with_context(
        self, 
        prompt: str,
        context: str,
        system_message: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> str:
        """Generate a response from Open Web UI with context"""
        rag_prompt = f"""
        Please answer the following question based on the provided context.
        If the context doesn't contain the information needed to answer the question,
        say "I don't have enough information to answer this question."

        Context:
        {context}

        Question: {prompt}
        """
        
        return self.generate(
            prompt=rag_prompt,
            system_message=system_message,
            temperature=temperature,
            max_tokens=max_tokens
        )


def get_llm_provider(provider_name: str = None) -> BaseLLMProvider:
    """
    Factory function to get the appropriate LLM provider
    
    Args:
        provider_name: Name of the LLM provider to use
        
    Returns:
        An instance of BaseLLMProvider
    """
    # Get provider from environment variable if not specified
    if not provider_name:
        provider_name = os.environ.get("LLM_PROVIDER", "openai").lower()
    
    logger.info(f"Initializing LLM provider: {provider_name}")
    
    try:
        if provider_name == "openai":
            return OpenAIProvider()
        elif provider_name == "anthropic":
            return AnthropicProvider()
        elif provider_name == "ollama":
            return OllamaProvider()
        elif provider_name == "openrouter":
            return OpenRouterProvider()
        elif provider_name == "groq":
            return GroqProvider()
        elif provider_name == "openwebui":
            return OpenWebUIProvider()
        else:
            logger.warning(f"Unknown LLM provider: {provider_name}. Falling back to OpenAI.")
            return OpenAIProvider()
    except Exception as e:
        logger.error(f"Error initializing LLM provider {provider_name}: {str(e)}")
        logger.warning("Falling back to OpenAI provider")
        try:
            return OpenAIProvider()
        except Exception:
            logger.error("Failed to initialize fallback OpenAI provider")
            raise ValueError("No LLM provider could be initialized. Please check your API keys.")