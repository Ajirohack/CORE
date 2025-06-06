"""
Communication utilities for core services
"""
import asyncio
import httpx
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ServiceCommunication:
    """Handles communication between services and with Space API"""
    
    def __init__(self, space_api_url: str, api_key: Optional[str] = None):
        self.space_api_url = space_api_url.rstrip('/')
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def register_with_space_api(self, service_info: Dict[str, Any]) -> bool:
        """Register service with Space API"""
        try:
            headers = {}
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'
            
            response = await self.client.post(
                f"{self.space_api_url}/api/v1/services/register",
                json=service_info,
                headers=headers
            )
            
            if response.status_code == 200:
                logger.info(f"Successfully registered service: {service_info.get('name')}")
                return True
            else:
                logger.error(f"Failed to register service: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error registering service: {e}")
            return False
    
    async def send_heartbeat(self, service_id: str, status: Dict[str, Any]) -> bool:
        """Send heartbeat to Space API"""
        try:
            headers = {}
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'
            
            response = await self.client.post(
                f"{self.space_api_url}/api/v1/services/{service_id}/heartbeat",
                json=status,
                headers=headers
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Error sending heartbeat: {e}")
            return False
    
    async def call_service(self, service_name: str, endpoint: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Call another service through Space API"""
        try:
            headers = {}
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'
            
            response = await self.client.post(
                f"{self.space_api_url}/api/v1/services/{service_name}/{endpoint}",
                json=data,
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Service call failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error calling service: {e}")
            return None
    
    async def discover_services(self) -> List[Dict[str, Any]]:
        """Discover available services from Space API"""
        try:
            headers = {}
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'
            
            response = await self.client.get(
                f"{self.space_api_url}/api/v1/services/discover",
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json().get('services', [])
            else:
                logger.error(f"Service discovery failed: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error discovering services: {e}")
            return []
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
