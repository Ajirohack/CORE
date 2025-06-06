"""
LRU Cache utility and search result caching for the RAG system.
"""
from typing import Dict, Any, Optional, Callable
from functools import wraps
import time
import threading
import logging

logger = logging.getLogger(__name__)

class LRUCache:
    """
    Simple LRU (Least Recently Used) cache implementation with TTL.
    """
    def __init__(self, capacity: int = 100, ttl_seconds: int = 3600):
        self.capacity = capacity
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.access_times: Dict[str, float] = {}
        self.lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        with self.lock:
            if key not in self.cache:
                return None
            now = time.time()
            if now - self.access_times[key] > self.ttl_seconds:
                self._remove(key)
                return None
            self.access_times[key] = now
            return self.cache[key]
    
    def put(self, key: str, value: Any) -> None:
        with self.lock:
            if key in self.cache:
                self.cache[key] = value
                self.access_times[key] = time.time()
                return
            if len(self.cache) >= self.capacity:
                self._evict_lru()
            self.cache[key] = value
            self.access_times[key] = time.time()
    
    def _evict_lru(self) -> None:
        if not self.cache:
            return
        oldest_key = min(self.access_times, key=self.access_times.get)
        self._remove(oldest_key)
    
    def _remove(self, key: str) -> None:
        if key in self.cache:
            del self.cache[key]
            del self.access_times[key]
    
    def clear(self) -> None:
        with self.lock:
            self.cache.clear()
            self.access_times.clear()
    
    def __len__(self) -> int:
        with self.lock:
            return len(self.cache)

def cached_search(cache_size: int = 100, ttl_seconds: int = 3600):
    """
    Decorator to cache search results in the RAG system.
    """
    cache = LRUCache(capacity=cache_size, ttl_seconds=ttl_seconds)
    def decorator(search_func: Callable):
        @wraps(search_func)
        def wrapper(self, query: str, k: int = 5, filter: Optional[Dict] = None, **kwargs):
            cache_key = f"{query}::{k}::{repr(filter)}::{repr(kwargs)}"
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for query: {query}")
                return cached_result
            result = search_func(self, query, k=k, filter=filter, **kwargs)
            cache.put(cache_key, result)
            return result
        return wrapper
    return decorator
