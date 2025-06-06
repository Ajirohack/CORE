"""
Retry Mechanism for the RAG System

This module provides utilities for retrying operations with exponential backoff,
particularly useful for API calls to LLM providers and embedding services.
"""

import time
import logging
import random
from functools import wraps
from typing import Callable, Any, List, Optional, Type, Union, Tuple

logger = logging.getLogger(__name__)

def retry_with_exponential_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    exceptions: Optional[List[Type[Exception]]] = None
) -> Callable:
    """
    Retry decorator with exponential backoff for API calls
    
    Args:
        max_retries: Maximum number of retries before giving up
        initial_delay: Initial delay between retries in seconds
        exponential_base: Base for the exponential backoff
        jitter: Whether to add randomness to the delay
        exceptions: List of exceptions that trigger a retry
        
    Returns:
        Decorated function with retry logic
    """
    if exceptions is None:
        exceptions = [Exception]
        
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Wrapper function implementing the retry logic"""
            # Initialize variables for retry logic
            num_retries = 0
            delay = initial_delay
            
            while True:
                try:
                    # Attempt to execute the function
                    return func(*args, **kwargs)
                except tuple(exceptions) as e:
                    # Increment retry counter
                    num_retries += 1
                    
                    # If we've reached the maximum number of retries, re-raise the exception
                    if num_retries > max_retries:
                        logger.error(f"Maximum retries ({max_retries}) exceeded: {str(e)}")
                        raise
                    
                    # Calculate delay with jitter if enabled
                    delay_with_jitter = delay
                    if jitter:
                        # Add randomness to the delay (±50%)
                        delay_with_jitter = delay * (0.5 + random.random())
                    
                    # Log retry attempt
                    logger.warning(
                        f"Retry {num_retries}/{max_retries} after error: {str(e)}. "
                        f"Retrying in {delay_with_jitter:.2f} seconds."
                    )
                    
                    # Wait before retrying
                    time.sleep(delay_with_jitter)
                    
                    # Increase delay for next retry
                    delay *= exponential_base
                    
        return wrapper
    return decorator


class RetryStrategy:
    """
    Configurable retry strategy that can be passed to functions
    
    Example:
        retry = RetryStrategy(max_retries=3, exceptions=[ConnectionError])
        result = retry.execute(api_call_function, arg1, arg2, kwarg1=value1)
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        exceptions: Optional[List[Type[Exception]]] = None
    ):
        """Initialize retry strategy with configuration"""
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.exceptions = exceptions or [Exception]
    
    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function with configured retry strategy
        
        Args:
            func: Function to execute
            *args: Positional arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            Result of the function call
            
        Raises:
            Exception: If all retries fail
        """
        # Initialize retry state
        num_retries = 0
        delay = self.initial_delay
        
        while True:
            try:
                # Attempt function execution
                return func(*args, **kwargs)
            except tuple(self.exceptions) as e:
                # Increment retry counter
                num_retries += 1
                
                # If we've reached max retries, re-raise the exception
                if num_retries > self.max_retries:
                    logger.error(f"Maximum retries ({self.max_retries}) exceeded: {str(e)}")
                    raise
                
                # Calculate delay with jitter if enabled
                delay_with_jitter = delay
                if self.jitter:
                    delay_with_jitter = delay * (0.5 + random.random())
                
                # Log retry attempt
                logger.warning(
                    f"Retry {num_retries}/{self.max_retries} after error: {str(e)}. "
                    f"Retrying in {delay_with_jitter:.2f} seconds."
                )
                
                # Wait before retrying
                time.sleep(delay_with_jitter)
                
                # Increase delay for next retry
                delay *= self.exponential_base


# Common retry configurations for different services
def get_openai_retry_strategy() -> RetryStrategy:
    """Get a retry strategy optimized for OpenAI API calls"""
    import requests
    return RetryStrategy(
        max_retries=3,
        initial_delay=2.0,
        exponential_base=3.0,
        exceptions=[
            requests.exceptions.RequestException, 
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
            requests.exceptions.HTTPError
        ]
    )


def get_embedding_retry_strategy() -> RetryStrategy:
    """Get a retry strategy optimized for embedding API calls"""
    import requests
    return RetryStrategy(
        max_retries=4,
        initial_delay=1.0,
        exponential_base=2.0,
        exceptions=[
            requests.exceptions.RequestException, 
            requests.exceptions.Timeout,
            ConnectionError
        ]
    )