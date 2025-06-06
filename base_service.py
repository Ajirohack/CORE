"""
Base servtry:
    from .services.auth import ServiceAuth
    from .services.communication import ServiceCommunication
    from .services.service_logging import ServiceLogger
except ImportError:
    try:
        from services.auth import ServiceAuth
        from services.communication import ServiceCommunication
        from services.service_logging import ServiceLogger
    except ImportError:
        # For when running as a script
        import sys
        from pathlib import Path
        services_path = Path(__file__).parent / "services"
        sys.path.insert(0, str(services_path))
        from auth import ServiceAuth
        from communication import ServiceCommunication
        from service_logging import ServiceLoggerndependent core services.
Provides common functionality for service registration, health checks, and communication.
"""
import asyncio
import logging
import httpx
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, asdict
import uuid

try:
    from .services.auth import ServiceAuth
    from .services.communication import ServiceCommunication
    from .services.service_logging import ServiceLogger
except ImportError:
    try:
        from services.auth import ServiceAuth
        from services.communication import ServiceCommunication
        from services.service_logging import ServiceLogger
    except ImportError:
        # For when running as a script
        import sys
        from pathlib import Path
        services_path = Path(__file__).parent / "services"
        sys.path.insert(0, str(services_path))
        from auth import ServiceAuth
        from communication import ServiceCommunication
        from service_logging import ServiceLogger

logger = logging.getLogger(__name__)

@dataclass
class ServiceInfo:
    """Service registration information"""
    service_id: str
    name: str
    version: str
    description: str
    capabilities: List[str]
    endpoints: Dict[str, str]
    health_endpoint: str
    status: str = "starting"
    last_heartbeat: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class ServiceRequest:
    """Standard request format for service communication"""
    request_id: str
    service_id: str
    action: str
    payload: Dict[str, Any]
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    timestamp: str = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()

@dataclass
class ServiceResponse:
    """Standard response format for service communication"""
    request_id: str
    service_id: str
    status: str  # success, error, processing
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: str = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()

class BaseService(ABC):
    """
    Base class for all independent core services.
    Handles registration with Space API, health checks, and standard communication.
    """
    
    def __init__(self, service_name: str, service_version: str = "1.0.0", config: Optional[Dict[str, Any]] = None):
        self.service_id = f"{service_name}-{uuid.uuid4().hex[:8]}"
        self.service_name = service_name
        self.service_version = service_version
        self.config = config or {}
        
        # Space API connection
        self.space_api_url = self.config.get('space_api_url', 'http://localhost:8000')
        self.api_key = self.config.get('api_key')
        
        # Initialize utilities
        self.auth = ServiceAuth(self.config.get('jwt_secret'))
        self.communication = ServiceCommunication(self.space_api_url, self.api_key)
        self.logger = ServiceLogger(service_name, self.config.get('log_level', 'INFO'))
        
        # Service state
        self._running = False
        self._registered = False
        self._last_heartbeat = None
        self._heartbeat_task = None
    
    @property
    def service_info(self) -> ServiceInfo:
        """Get current service information"""
        return ServiceInfo(
            service_id=self.service_id,
            name=self.service_name,
            version=self.service_version,
            description=self.get_description(),
            capabilities=self.get_capabilities(),
            endpoints=self.get_endpoints(),
            health_endpoint=f"/health/{self.service_id}",
            status="running" if self._running else "stopped",
            last_heartbeat=self._last_heartbeat,
            metadata=self.get_metadata()
        )
    
    @abstractmethod
    def get_description(self) -> str:
        """Return service description"""
        pass
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Return list of service capabilities"""
        pass
    
    @abstractmethod
    def get_endpoints(self) -> Dict[str, str]:
        """Return service endpoints mapping"""
        pass
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the service"""
        pass
    
    @abstractmethod
    async def process_request(self, request: ServiceRequest) -> ServiceResponse:
        """Process incoming service request"""
        pass
    
    @abstractmethod
    async def shutdown(self):
        """Cleanup on service shutdown"""
        pass
    
    def get_metadata(self) -> Dict[str, Any]:
        """Override to provide additional service metadata"""
        return {}
    
    async def start(self) -> bool:
        """Start the service and register with Space API"""
        try:
            self.logger.info(f"Starting service {self.service_name}...")
            
            # Initialize service
            if not await self.initialize():
                self.logger.error("Service initialization failed")
                return False
            
            self._running = True
            
            # Register with Space API
            if await self.register_with_space_api():
                self._registered = True
                self.logger.info(f"Service {self.service_name} started and registered successfully")
                
                # Start heartbeat task
                asyncio.create_task(self._heartbeat_loop())
                return True
            else:
                self.logger.warning("Failed to register with Space API, running in standalone mode")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to start service: {e}")
            return False
    
    async def stop(self):
        """Stop the service and unregister"""
        self.logger.info(f"Stopping service {self.service_name}...")
        self._running = False
        
        if self._registered:
            await self.unregister_from_space_api()
        
        await self.shutdown()
        await self.client.aclose()
        self.logger.info(f"Service {self.service_name} stopped")
    
    async def register_with_space_api(self) -> bool:
        """Register this service with the Space API"""
        if not self.space_api_url:
            self.logger.warning("No Space API URL configured")
            return False
        
        try:
            registration_data = asdict(self.service_info)
            
            response = await self.client.post(
                f"{self.space_api_url}/api/v1/services/register",
                json=registration_data,
                headers=self._get_auth_headers()
            )
            
            if response.status_code == 200:
                self.logger.info("Successfully registered with Space API")
                return True
            else:
                self.logger.error(f"Registration failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to register with Space API: {e}")
            return False
    
    async def unregister_from_space_api(self) -> bool:
        """Unregister this service from the Space API"""
        try:
            response = await self.client.delete(
                f"{self.space_api_url}/api/v1/services/{self.service_id}",
                headers=self._get_auth_headers()
            )
            
            if response.status_code == 200:
                self.logger.info("Successfully unregistered from Space API")
                return True
            else:
                self.logger.warning(f"Unregistration failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to unregister from Space API: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        try:
            # Perform service-specific health checks
            service_health = await self._service_health_check()
            
            health_data = {
                "service_id": self.service_id,
                "service_name": self.service_name,
                "status": "healthy" if self._running and service_health else "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "uptime": self._get_uptime(),
                "version": self.service_version,
                "registered": self._registered,
                "details": service_health
            }
            
            return health_data
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {
                "service_id": self.service_id,
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _service_health_check(self) -> Dict[str, Any]:
        """Override for service-specific health checks"""
        return {"status": "ok"}
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeat to Space API"""
        while self._running and self._registered:
            try:
                await self._send_heartbeat()
                await asyncio.sleep(30)  # Heartbeat every 30 seconds
            except Exception as e:
                self.logger.error(f"Heartbeat failed: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _send_heartbeat(self):
        """Send heartbeat to Space API"""
        try:
            health_data = await self.health_check()
            
            response = await self.client.post(
                f"{self.space_api_url}/api/v1/services/{self.service_id}/heartbeat",
                json=health_data,
                headers=self._get_auth_headers()
            )
            
            if response.status_code == 200:
                self._last_heartbeat = datetime.utcnow().isoformat()
            else:
                self.logger.warning(f"Heartbeat failed: {response.status_code}")
                
        except Exception as e:
            self.logger.error(f"Failed to send heartbeat: {e}")
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for Space API requests"""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers
    
    def _get_uptime(self) -> int:
        """Get service uptime in seconds"""
        # This would track actual start time
        return 0
    
    async def call_service(self, target_service: str, action: str, payload: Dict[str, Any], user_id: Optional[str] = None) -> ServiceResponse:
        """Call another service through the Space API"""
        try:
            request = ServiceRequest(
                request_id=str(uuid.uuid4()),
                service_id=self.service_id,
                action=action,
                payload=payload,
                user_id=user_id
            )
            
            response = await self.client.post(
                f"{self.space_api_url}/api/v1/services/{target_service}/invoke",
                json=asdict(request),
                headers=self._get_auth_headers()
            )
            
            if response.status_code == 200:
                response_data = response.json()
                return ServiceResponse(**response_data)
            else:
                return ServiceResponse(
                    request_id=request.request_id,
                    service_id=target_service,
                    status="error",
                    error=f"Service call failed: {response.status_code}"
                )
                
        except Exception as e:
            return ServiceResponse(
                request_id=str(uuid.uuid4()),
                service_id=target_service,
                status="error",
                error=f"Service call exception: {str(e)}"
            )
