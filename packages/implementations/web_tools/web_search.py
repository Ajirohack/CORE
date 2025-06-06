"""
Web Search Tool Implementation
Provides web search capabilities via different search engines
"""

import logging
import requests
import json
import os
from typing import Dict, List, Any, Optional
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)

class WebSearchTool:
    """
    Web search tool implementation providing search functionality using
    various search engines APIs.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize web search tool with configuration."""
        self.config = config or {}
        self.default_engine = self.config.get("default_engine", "duckduckgo")
        
        # API keys from config or environment variables
        self.api_keys = {
            "google": self.config.get("google_api_key", os.environ.get("GOOGLE_SEARCH_API_KEY")),
            "bing": self.config.get("bing_api_key", os.environ.get("BING_SEARCH_API_KEY")),
        }
        
        # Initialize session for connection pooling
        self.session = requests.Session()
        
        # Set user agent for non-API requests
        self.user_agent = "Mozilla/5.0 (compatible; SpaceNewBot/1.0; +https://spacenew.ai/bot)"
        
    def search(self, 
              query: str, 
              engine: Optional[str] = None, 
              num_results: int = 5,
              filter_options: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Perform web search using specified engine
        
        Args:
            query: Search query string
            engine: Search engine to use (google, bing, duckduckgo)
            num_results: Number of results to return
            filter_options: Optional filtering options for search results
            
        Returns:
            List of search results with title, snippet, and URL
        """
        engine = engine or self.default_engine
        filter_options = filter_options or {}
        
        logger.info(f"Performing web search: '{query}' using {engine}")
        
        if engine == "google" and self.api_keys.get("google"):
            return self._search_google(query, num_results, filter_options)
        elif engine == "bing" and self.api_keys.get("bing"):
            return self._search_bing(query, num_results, filter_options)
        else:
            # Default to DuckDuckGo (no API key needed)
            return self._search_duckduckgo(query, num_results, filter_options)
            
    def _search_google(self, query: str, num_results: int, filter_options: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search using Google Custom Search API."""
        api_key = self.api_keys["google"]
        cx = self.config.get("google_cx", os.environ.get("GOOGLE_SEARCH_CX"))
        
        if not cx:
            logger.error("Google Custom Search Engine ID (CX) not found")
            return []
            
        url = "https://www.googleapis.com/customsearch/v1"
        
        # Extract filter options
        date_restrict = filter_options.get("date_restrict", None)  # Options like "d1", "w2", "m6"
        file_type = filter_options.get("file_type", None)
        
        # Prepare parameters
        params = {
            "key": api_key,
            "cx": cx,
            "q": query,
            "num": min(num_results, 10)  # API limit is 10 per request
        }
        
        # Add optional filters
        if date_restrict:
            params["dateRestrict"] = date_restrict
        if file_type:
            params["fileType"] = file_type
            
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            results = []
            if "items" in data:
                for item in data["items"]:
                    results.append({
                        "title": item.get("title", ""),
                        "snippet": item.get("snippet", ""),
                        "url": item.get("link", ""),
                        "source": "google"
                    })
            return results
            
        except Exception as e:
            logger.error(f"Google search error: {str(e)}")
            return []
            
    def _search_bing(self, query: str, num_results: int, filter_options: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search using Bing Web Search API."""
        api_key = self.api_keys["bing"]
            
        url = "https://api.bing.microsoft.com/v7.0/search"
        
        # Extract filter options
        freshness = filter_options.get("freshness", None)  # Options: Day, Week, Month
        
        # Prepare parameters
        params = {
            "q": query,
            "count": min(num_results, 50)  # API limit is 50 per request
        }
        
        # Add optional filters
        if freshness:
            params["freshness"] = freshness
            
        headers = {
            "Ocp-Apim-Subscription-Key": api_key
        }
            
        try:
            response = self.session.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            results = []
            if "webPages" in data and "value" in data["webPages"]:
                for item in data["webPages"]["value"]:
                    results.append({
                        "title": item.get("name", ""),
                        "snippet": item.get("snippet", ""),
                        "url": item.get("url", ""),
                        "source": "bing"
                    })
            return results
            
        except Exception as e:
            logger.error(f"Bing search error: {str(e)}")
            return []
            
    def _search_duckduckgo(self, query: str, num_results: int, filter_options: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search using DuckDuckGo text search API.
        Note: This uses an unofficial API
        """
        url = "https://api.duckduckgo.com/"
        
        # Prepare parameters
        params = {
            "q": query,
            "format": "json",
            "no_html": 1,
            "no_redirect": 1,
            "skip_disambig": 1
        }
            
        headers = {
            "User-Agent": self.user_agent
        }
            
        try:
            response = self.session.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            results = []
            
            # Get abstract result
            if data.get("Abstract"):
                results.append({
                    "title": data.get("Heading", ""),
                    "snippet": data.get("Abstract", ""),
                    "url": data.get("AbstractURL", ""),
                    "source": "duckduckgo"
                })
                
            # Get related topics
            topics = data.get("RelatedTopics", [])
            for topic in topics[:num_results]:
                if "Result" in topic:
                    results.append({
                        "title": topic.get("Text", ""),
                        "snippet": topic.get("Result", ""),
                        "url": topic.get("FirstURL", ""),
                        "source": "duckduckgo"
                    })
                    
            return results[:num_results]
            
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {str(e)}")
            return []
            
    def get_search_suggestion(self, query: str, engine: Optional[str] = None) -> List[str]:
        """
        Get search query suggestions based on partial input.
        
        Args:
            query: Partial query string
            engine: Search engine to use for suggestions
            
        Returns:
            List of suggested search queries
        """
        engine = engine or self.default_engine
        
        # Use DuckDuckGo suggestions (does not require API key)
        url = f"https://duckduckgo.com/ac/?q={quote_plus(query)}&type=list"
        
        headers = {
            "User-Agent": self.user_agent
        }
        
        try:
            response = self.session.get(url, headers=headers)
            response.raise_for_status()
            suggestions = response.json()
            
            return [item["phrase"] for item in suggestions]
        except Exception as e:
            logger.error(f"Error getting search suggestions: {str(e)}")
            return []
