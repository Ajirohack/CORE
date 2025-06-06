"""
LLM Factory for creating LLM provider instances
"""

import logging
import importlib
from typing import Dict, Any, Optional, Type

from core.rag_system.llm_integration.llm_provider import BaseLLMProvider

logger = logging.getLogger(__name__)

class LLMProviderFactory:
    """Factory for creating LLM provider instances"""
    
    # Default mapping of provider types to their implementations
    PROVIDER_MAPPING = {
        "ollama": "core.rag_system.llm_integration.providers.ollama_provider.OllamaProvider",
        "openai": "core.rag_system.llm_integration.providers.openai_provider.OpenaiProvider",
        "anthropic": "core.rag_system.llm_integration.providers.anthropic_provider.AnthropicProvider",
        "groq": "core.rag_system.llm_integration.providers.groq_provider.GroqProvider",
        "openrouter": "core.rag_system.llm_integration.providers.openrouter_provider.OpenrouterProvider",
    }
    
    @classmethod
    def create_provider(cls, provider_type: str, config: Dict[str, Any] = None) -> BaseLLMProvider:
        """
        Create an LLM provider instance based on the specified type
        
        Args:
            provider_type: The type of provider to create
            config: Configuration dictionary for the provider
            
        Returns:
            An instance of the specified LLM provider
        """
        provider_type = provider_type.lower()
        
        if provider_type not in cls.PROVIDER_MAPPING:
            logger.warning(f"Unknown provider type: {provider_type}, falling back to ollama")
            provider_type = "ollama"
            
        provider_class = cls._get_provider_class(provider_type)
        
        try:
            return provider_class(config=config)
        except Exception as e:
            logger.error(f"Failed to create provider {provider_type}: {str(e)}")
            # Fall back to Ollama if other providers fail
            if provider_type != "ollama":
                logger.warning(f"Falling back to Ollama provider due to error")
                return cls.create_provider("ollama", config)
            else:
                raise
    
    @classmethod
    def _get_provider_class(cls, provider_type: str) -> Type[BaseLLMProvider]:
        """
        Get the provider class for the specified provider type
        
        Args:
            provider_type: The type of provider
            
        Returns:
            The provider class
        """
        try:
            module_path, class_name = cls.PROVIDER_MAPPING[provider_type].rsplit(".", 1)
            module = importlib.import_module(module_path)
            return getattr(module, class_name)
        except (ImportError, AttributeError) as e:
            logger.error(f"Error loading provider class for {provider_type}: {str(e)}")
            raise ImportError(f"Failed to load provider class for {provider_type}")