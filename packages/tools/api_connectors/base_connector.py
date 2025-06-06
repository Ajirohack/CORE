"""Base API connector for external service integration."""

import asyncio
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin

import aiohttp
from utils.logging import logger
from utils.metrics import collector
from utils.security import verify_signature

class BaseAPIConnector:
    """Base class for API connectors."""
    
    def __init__(
        self,
        base_url: str,
        api_key: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        verify_ssl: bool = True
    ):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.verify_ssl = verify_ssl
        self.logger = logger
        self.metrics = collector
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an HTTP session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def close(self) -> None:
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
    
    def _build_url(self, endpoint: str) -> str:
        """Build full URL from endpoint."""
        return urljoin(self.base_url, endpoint.lstrip('/'))
    
    def _get_headers(
        self,
        custom_headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """Get request headers."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "SpaceProject/1.0"
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            
        if custom_headers:
            headers.update(custom_headers)
            
        return headers
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Make an HTTP request with retries."""
        url = self._build_url(endpoint)
        timeout = timeout or self.timeout
        headers = self._get_headers(headers)
        
        for attempt in range(self.max_retries):
            try:
                session = await self._get_session()
                
                with self.metrics.measure_time(
                    "api_request",
                    {"method": method, "endpoint": endpoint}
                ):
                    async with session.request(
                        method=method,
                        url=url,
                        params=params,
                        json=data,
                        headers=headers,
                        ssl=self.verify_ssl,
                        timeout=timeout
                    ) as response:
                        response_data = await response.json()
                        
                        if response.status in {200, 201}:
                            return response_data
                        else:
                            error_msg = response_data.get(
                                'error',
                                f"HTTP {response.status}"
                            )
                            raise Exception(error_msg)
                            
            except asyncio.TimeoutError:
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)
                
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                self.logger.warning(
                    f"Request failed (attempt {attempt + 1}): {str(e)}"
                )
                await asyncio.sleep(2 ** attempt)
    
    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Make a GET request."""
        return await self._make_request(
            "GET",
            endpoint,
            params=params,
            **kwargs
        )
    
    async def post(
        self,
        endpoint: str,
        data: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """Make a POST request."""
        return await self._make_request(
            "POST",
            endpoint,
            data=data,
            **kwargs
        )
    
    async def put(
        self,
        endpoint: str,
        data: Dict[str, Any],
        **kwargs
    ) -> Dict[str, Any]:
        """Make a PUT request."""
        return await self._make_request(
            "PUT",
            endpoint,
            data=data,
            **kwargs
        )
    
    async def delete(
        self,
        endpoint: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Make a DELETE request."""
        return await self._make_request(
            "DELETE",
            endpoint,
            **kwargs
        )
    
    async def verify_response(
        self,
        response_data: Dict[str, Any],
        expected_signature: Optional[str] = None
    ) -> bool:
        """Verify response data integrity."""
        if not expected_signature:
            return True
            
        if not self.api_key:
            self.logger.warning("No API key available for signature verification")
            return False
            
        try:
            return verify_signature(
                expected_signature,
                str(response_data.get("id", "")),
                self.api_key
            )
        except Exception as e:
            self.logger.error(f"Error verifying response signature: {e}")
            return False