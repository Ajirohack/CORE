"""Web search manager for the space project."""

from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin

import aiohttp
from bs4 import BeautifulSoup
from utils.logging import logger
from utils.metrics import collector
from utils.security import verify_signature

class WebSearchManager:
    """Manages web search operations across the system."""
    
    def __init__(
        self,
        api_key: str,
        base_url: str,
        verify_ssl: bool = True,
        timeout: int = 30
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.logger = logger
        self.metrics = collector
        
    async def search(
        self,
        query: str,
        max_results: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Perform a web search and return results."""
        with self.metrics.measure_time("web_search"):
            try:
                async with aiohttp.ClientSession() as session:
                    params = {
                        "q": query,
                        "num": max_results,
                        **filters if filters else {}
                    }
                    headers = {
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                    
                    async with session.get(
                        urljoin(self.base_url, "/search"),
                        params=params,
                        headers=headers,
                        ssl=self.verify_ssl,
                        timeout=self.timeout
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            return await self._process_results(data)
                        else:
                            self.logger.error(
                                f"Search failed: {response.status}"
                            )
                            return []
                            
            except Exception as e:
                self.logger.error(f"Error performing web search: {e}")
                return []
    
    async def fetch_content(
        self,
        url: str,
        extract_text: bool = True
    ) -> Optional[Union[str, Dict[str, Any]]]:
        """Fetch and optionally extract text from a URL."""
        with self.metrics.measure_time("content_fetch"):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        url,
                        ssl=self.verify_ssl,
                        timeout=self.timeout
                    ) as response:
                        if response.status == 200:
                            content = await response.text()
                            if extract_text:
                                return self._extract_text(content)
                            return content
                        else:
                            self.logger.error(
                                f"Content fetch failed: {response.status}"
                            )
                            return None
                            
            except Exception as e:
                self.logger.error(f"Error fetching content: {e}")
                return None
    
    def _extract_text(self, html_content: str) -> str:
        """Extract meaningful text from HTML content."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'footer']):
                element.decompose()
            
            # Extract text
            text = soup.get_text(separator=' ', strip=True)
            return text
            
        except Exception as e:
            self.logger.error(f"Error extracting text: {e}")
            return ""
    
    async def _process_results(
        self,
        raw_results: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Process and validate search results."""
        processed = []
        
        if not raw_results.get("results"):
            return processed
            
        for result in raw_results["results"]:
            # Verify result signature if provided
            if "signature" in result:
                if not verify_signature(
                    result["signature"],
                    str(result["id"]),
                    self.api_key
                ):
                    continue
            
            # Extract relevant fields
            processed_result = {
                "id": result.get("id"),
                "title": result.get("title", ""),
                "url": result.get("url", ""),
                "snippet": result.get("snippet", ""),
                "score": result.get("score", 0.0),
                "metadata": result.get("metadata", {})
            }
            
            processed.append(processed_result)
            
        return processed