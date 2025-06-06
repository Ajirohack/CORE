"""
LLM Integration Module for the RAG System

This module provides integration with various LLM providers for the RAG system.
"""

import os
import logging
from typing import Dict, Any, Optional, List
import requests
from core.rag_system.utils.retry import retry_with_exponential_backoff

logger = logging.getLogger(__name__)

class BaseLLMProvider:
    """Base class for LLM providers"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.provider_name = "base"
        
    @retry_with_exponential_backoff(
        max_retries=3,
        exceptions=[requests.RequestException, ConnectionError, TimeoutError]
    )
    def generate_with_context(
        self, 
        prompt: str, 
        context: str, 
        system_message: str = None,
        temperature: float = 0.0
    ) -> str:
        """
        Generate a response using the LLM with the given context
        
        Args:
            prompt: The user prompt/question
            context: Context information for the LLM
            system_message: Optional system message to guide the LLM
            temperature: Temperature parameter for response generation
            
        Returns:
            The generated response from the LLM
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    def _check_api_key(self, env_var_name: str) -> bool:
        """Check if the API key is available in environment variables"""
        api_key = os.environ.get(env_var_name)
        if not api_key:
            logger.warning(f"API key not found: {env_var_name} environment variable is not set")
            return False
        return True


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API integration"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.provider_name = "openai"
        
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
            self.available = self._check_api_key("OPENAI_API_KEY")
            self.model = config.get("model", os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo"))
        except ImportError:
            logger.warning("OpenAI Python package not installed")
            self.available = False
    
    @retry_with_exponential_backoff(
        max_retries=3,
        initial_delay=2.0,
        exceptions=[requests.RequestException, ConnectionError, TimeoutError]
    )
    def generate_with_context(
        self, 
        prompt: str, 
        context: str, 
        system_message: str = None,
        temperature: float = 0.0
    ) -> str:
        """Generate a response using OpenAI"""
        if not self.available:
            return "Error: OpenAI API key not set or package not installed"
        
        if not system_message:
            system_message = "You are a helpful assistant. Answer based only on the provided context."
        
        try:
            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": f"Context: {context}\n\nQuestion: {prompt}"}
            ]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating response with OpenAI: {e}")
            raise  # Let the retry decorator handle this


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude API integration"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.provider_name = "anthropic"
        
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
            self.available = self._check_api_key("ANTHROPIC_API_KEY")
            self.model = config.get("model", os.environ.get("ANTHROPIC_MODEL", "claude-3-sonnet-20240229"))
        except ImportError:
            logger.warning("Anthropic Python package not installed")
            self.available = False
    
    @retry_with_exponential_backoff(
        max_retries=3,
        initial_delay=2.0,
        exceptions=[requests.RequestException, ConnectionError, TimeoutError]
    )
    def generate_with_context(
        self, 
        prompt: str, 
        context: str, 
        system_message: str = None,
        temperature: float = 0.0
    ) -> str:
        """Generate a response using Anthropic Claude"""
        if not self.available:
            return "Error: Anthropic API key not set or package not installed"
        
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                temperature=temperature,
                system=system_message or "You are a helpful assistant. Answer based only on the provided context.",
                messages=[
                    {
                        "role": "user",
                        "content": f"Context: {context}\n\nQuestion: {prompt}"
                    }
                ]
            )
            
            # Handle Anthropic's response format
            return message.content[0].text
        except Exception as e:
            logger.error(f"Error generating response with Anthropic: {e}")
            raise  # Let the retry decorator handle this


class GroqProvider(BaseLLMProvider):
    """Groq API integration for fast inference"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.provider_name = "groq"
        
        try:
            from groq import Groq
            self.client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
            self.available = self._check_api_key("GROQ_API_KEY")
            self.model = config.get("model", os.environ.get("GROQ_MODEL", "llama3-8b-8192"))
        except ImportError:
            logger.warning("Groq Python package not installed")
            self.available = False
    
    @retry_with_exponential_backoff(
        max_retries=3,
        initial_delay=1.0,  # Groq is fast, so we can use a shorter initial delay
        exceptions=[requests.RequestException, ConnectionError, TimeoutError]
    )
    def generate_with_context(
        self, 
        prompt: str, 
        context: str, 
        system_message: str = None,
        temperature: float = 0.0
    ) -> str:
        """Generate a response using Groq"""
        if not self.available:
            return "Error: Groq API key not set or package not installed"
        
        try:
            messages = [
                {"role": "system", "content": system_message or "You are a helpful assistant. Answer based only on the provided context."},
                {"role": "user", "content": f"Context: {context}\n\nQuestion: {prompt}"}
            ]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature
            )
            
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating response with Groq: {e}")
            raise  # Let the retry decorator handle this


class OllamaProvider(BaseLLMProvider):
    """Integration with Ollama for local models"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.provider_name = "ollama"
        self.available = True  # Assuming Ollama is available locally
        self.model = config.get("model", os.environ.get("OLLAMA_MODEL", "llama3"))
        self.ollama_url = config.get("base_url", os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"))
    
    @retry_with_exponential_backoff(
        max_retries=2,  # Fewer retries for local service
        exceptions=[requests.RequestException, ConnectionError]
    )
    def generate_with_context(
        self, 
        prompt: str, 
        context: str, 
        system_message: str = None,
        temperature: float = 0.0
    ) -> str:
        """Generate a response using Ollama"""
        try:
            system = system_message or "You are a helpful assistant. Answer based only on the provided context."
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": f"<system>{system}</system>\n\nContext: {context}\n\nQuestion: {prompt}",
                    "stream": False,
                    "options": {
                        "temperature": temperature
                    }
                },
                timeout=60  # Longer timeout for local processing
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "Error: No response from Ollama")
            else:
                error_msg = f"Error: Ollama returned status code {response.status_code}"
                logger.error(error_msg)
                raise requests.HTTPError(error_msg)
            
        except Exception as e:
            logger.error(f"Error generating response with Ollama: {e}")
            raise  # Let the retry decorator handle this


class OpenRouterProvider(BaseLLMProvider):
    """Integration with OpenRouter for accessing multiple models"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.provider_name = "openrouter"
        self.available = self._check_api_key("OPENROUTER_API_KEY")
        self.model = config.get("model", os.environ.get("OPENROUTER_MODEL", "openai/gpt-3.5-turbo"))
        self.api_base = "https://openrouter.ai/api/v1"
    
    @retry_with_exponential_backoff(
        max_retries=3,
        exceptions=[requests.RequestException, ConnectionError, TimeoutError]
    )
    def generate_with_context(
        self, 
        prompt: str, 
        context: str, 
        system_message: str = None,
        temperature: float = 0.0
    ) -> str:
        """Generate a response using OpenRouter"""
        if not self.available:
            return "Error: OpenRouter API key not set"
        
        try:
            headers = {
                "Authorization": f"Bearer {os.environ.get('OPENROUTER_API_KEY')}",
                "Content-Type": "application/json",
                "HTTP-Referer": os.environ.get("OPENROUTER_REFERER", "http://localhost:8000"),
                "X-Title": os.environ.get("OPENROUTER_TITLE", "RAG System")
            }
            
            data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": system_message or "You are a helpful assistant. Answer based only on the provided context."},
                    {"role": "user", "content": f"Context: {context}\n\nQuestion: {prompt}"}
                ],
                "temperature": temperature
            }
            
            response = requests.post(
                f"{self.api_base}/chat/completions",
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                error_msg = f"Error: OpenRouter returned status code {response.status_code}: {response.text}"
                logger.error(error_msg)
                raise requests.HTTPError(error_msg)
            
        except Exception as e:
            logger.error(f"Error generating response with OpenRouter: {e}")
            raise  # Let the retry decorator handle this


def get_llm_provider(provider_name: str = None, config: Dict[str, Any] = None) -> BaseLLMProvider:
    """
    Factory function to get an LLM provider by name
    
    Args:
        provider_name: Name of the provider to use
        config: Optional configuration for the provider
        
    Returns:
        An instance of the requested LLM provider
    """
    config = config or {}
    
    # If no provider name specified, try to get from config, then environment
    if not provider_name:
        provider_name = (
            config.get("provider") or 
            os.environ.get("LLM_PROVIDER", "openai")
        ).lower()
    else:
        provider_name = provider_name.lower()
    
    providers = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "groq": GroqProvider,
        "ollama": OllamaProvider,
        "openrouter": OpenRouterProvider
    }
    
    if provider_name not in providers:
        logger.warning(f"Unknown provider: {provider_name}, falling back to Groq")
        provider_name = "groq"
    
    return providers[provider_name](config)


def list_available_models() -> Dict[str, List[str]]:
    """
    List available models for each provider
    
    Returns:
        Dictionary of provider names to lists of available model names
    """
    return {
        "openai": ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"],
        "anthropic": ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"],
        "groq": ["llama3-8b-8192", "llama3-70b-8192", "mixtral-8x7b-32768"],
        "ollama": ["llama3", "mistral", "codellama"],
        "openrouter": ["openai/gpt-3.5-turbo", "anthropic/claude-3-opus", "meta-llama/llama-3-70b"]
    }


def get_provider_status() -> Dict[str, bool]:
    """
    Check which providers are available based on API keys
    
    Returns:
        Dictionary of provider names to availability status
    """
    return {
        "openai": os.environ.get("OPENAI_API_KEY") is not None,
        "anthropic": os.environ.get("ANTHROPIC_API_KEY") is not None,
        "groq": os.environ.get("GROQ_API_KEY") is not None,
        "ollama": True,  # Always available as it's local
        "openrouter": os.environ.get("OPENROUTER_API_KEY") is not None
    }