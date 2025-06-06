"""
Shared LLM provider module for the RAG system
"""

import logging
import os
from typing import Dict, Any, Optional

from core.rag_system.llm_integration.llm_factory import LLMProviderFactory
from core.rag_system.llm_integration.llm_provider import BaseLLMProvider

logger = logging.getLogger(__name__)

# Global provider instance
_provider_instance = None

def get_provider(force_reload: bool = False, provider_type: str = None, config: Dict[str, Any] = None) -> BaseLLMProvider:
    """
    Get a shared instance of an LLM provider
    
    Args:
        force_reload: Whether to force a reload of the provider instance
        provider_type: The type of provider to use
        config: Configuration dictionary for the provider
        
    Returns:
        An instance of the LLM provider
    """
    global _provider_instance
    
    # Create provider if it doesn't exist or force reload is requested
    if _provider_instance is None or force_reload:
        # Get provider type from config, environment, or use 'ollama' as default
        if provider_type is None:
            provider_type = os.environ.get("LLM_PROVIDER", "ollama")
        
        # Create provider instance
        try:
            _provider_instance = LLMProviderFactory.create_provider(provider_type, config)
            logger.info(f"Initialized LLM provider: {provider_type}")
        except Exception as e:
            logger.error(f"Error initializing LLM provider: {str(e)}")
            raise
    
    return _provider_instance

def generate_response(
    prompt: str, 
    context: str = None, 
    system_message: Optional[str] = None,
    temperature: float = 0.0,
    provider_type: str = None,
    config: Dict[str, Any] = None
) -> str:
    """
    Generate a response from an LLM provider
    
    Args:
        prompt: The user's question or prompt
        context: Optional context for RAG
        system_message: Optional system message to guide the LLM
        temperature: Temperature parameter for response generation
        provider_type: The type of provider to use
        config: Configuration for the provider
        
    Returns:
        The generated response as a string
    """
    provider = get_provider(
        force_reload=(provider_type is not None or config is not None),
        provider_type=provider_type,
        config=config
    )
    
    if context:
        return provider.generate_with_context(
            prompt=prompt,
            context=context,
            system_message=system_message,
            temperature=temperature
        )
    else:
        return provider.generate(
            prompt=prompt,
            system_message=system_message,
            temperature=temperature
        )