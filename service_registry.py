"""
Service registry for managing and discovering core services.
Provides service discovery, load balancing, and health monitoring.
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json

from .base_service import ServiceInfo, ServiceRequest, ServiceResponse

logger = logging.getLogger(__name__)

@dataclass
class ServiceMetrics:
    """Service performance metrics"""
    request_count: int = 0
    error_count: int = 0
    avg_response_time: float = 0.0
    last_request: Optional[str] = None
    last_error: Optional[str] = None

class ServiceRegistry:
    """
    Central registry for managing core services.
    Handles service discovery, health monitoring, and load balancing.
    """
    
    def __init__(self):
        self._services: Dict[str, ServiceInfo] = {}
        self._service_metrics: Dict[str, ServiceMetrics] = {}
        self._service_instances: Dict[str, List[str]] = {}  # service_name -> [instance_ids]
        self._health_check_interval = 60  # seconds
        self._unhealthy_threshold = 3  # failed health checks before marking unhealthy
        self._running = False
        
    async def start(self):
        """Start the service registry"""
        self._running = True
        asyncio.create_task(self._health_monitor_loop())
        logger.info("Service registry started")
    
    async def stop(self):
        """Stop the service registry"""
        self._running = False
        logger.info("Service registry stopped")
    
    async def register_service(self, service_info: ServiceInfo) -> bool:
        """Register a new service"""
        try:
            self._services[service_info.service_id] = service_info
            self._service_metrics[service_info.service_id] = ServiceMetrics()
            
            # Track service instances
            if service_info.name not in self._service_instances:
                self._service_instances[service_info.name] = []
            self._service_instances[service_info.name].append(service_info.service_id)
            
            logger.info(f"Registered service: {service_info.name} ({service_info.service_id})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register service {service_info.service_id}: {e}")
            return False
    
    async def unregister_service(self, service_id: str) -> bool:
        """Unregister a service"""
        try:
            if service_id in self._services:
                service_info = self._services[service_id]
                service_name = service_info.name
                
                # Remove from registry
                del self._services[service_id]
                del self._service_metrics[service_id]
                
                # Remove from instances
                if service_name in self._service_instances:
                    self._service_instances[service_name] = [
                        sid for sid in self._service_instances[service_name] if sid != service_id
                    ]
                    if not self._service_instances[service_name]:
                        del self._service_instances[service_name]
                
                logger.info(f"Unregistered service: {service_name} ({service_id})")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to unregister service {service_id}: {e}")
            return False
    
    async def update_service_heartbeat(self, service_id: str, health_data: Dict[str, Any]) -> bool:
        """Update service heartbeat and health status"""
        try:
            if service_id in self._services:
                self._services[service_id].last_heartbeat = datetime.utcnow().isoformat()
                self._services[service_id].status = health_data.get('status', 'unknown')
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to update heartbeat for {service_id}: {e}")
            return False
    
    def get_service(self, service_id: str) -> Optional[ServiceInfo]:
        """Get service information by ID"""
        return self._services.get(service_id)
    
    def get_services_by_name(self, service_name: str) -> List[ServiceInfo]:
        """Get all instances of a service by name"""
        instance_ids = self._service_instances.get(service_name, [])
        return [self._services[sid] for sid in instance_ids if sid in self._services]
    
    def get_healthy_service(self, service_name: str) -> Optional[ServiceInfo]:
        """Get a healthy instance of a service"""
        services = self.get_services_by_name(service_name)
        healthy_services = [s for s in services if s.status == "running"]
        
        if not healthy_services:
            return None
        
        # Simple round-robin selection
        # In production, this could be more sophisticated load balancing
        return min(healthy_services, key=lambda s: self._service_metrics[s.service_id].request_count)
    
    def get_all_services(self) -> List[ServiceInfo]:
        """Get all registered services"""
        return list(self._services.values())
    
    def get_services_by_capability(self, capability: str) -> List[ServiceInfo]:
        """Get services that provide a specific capability"""
        return [
            service for service in self._services.values()
            if capability in service.capabilities
        ]
    
    def get_service_metrics(self, service_id: str) -> Optional[ServiceMetrics]:
        """Get service performance metrics"""
        return self._service_metrics.get(service_id)
    
    def record_service_request(self, service_id: str, response_time: float, success: bool = True):
        """Record a service request for metrics"""
        if service_id in self._service_metrics:
            metrics = self._service_metrics[service_id]
            metrics.request_count += 1
            metrics.last_request = datetime.utcnow().isoformat()
            
            # Update average response time
            if metrics.avg_response_time == 0:
                metrics.avg_response_time = response_time
            else:
                # Simple moving average
                metrics.avg_response_time = (metrics.avg_response_time + response_time) / 2
            
            if not success:
                metrics.error_count += 1
                metrics.last_error = datetime.utcnow().isoformat()
    
    async def get_registry_status(self) -> Dict[str, Any]:
        """Get overall registry status"""
        total_services = len(self._services)
        healthy_services = sum(1 for s in self._services.values() if s.status == "running")
        
        service_types = {}
        for service in self._services.values():
            service_types[service.name] = service_types.get(service.name, 0) + 1
        
        return {
            "total_services": total_services,
            "healthy_services": healthy_services,
            "unhealthy_services": total_services - healthy_services,
            "service_types": service_types,
            "registry_status": "running" if self._running else "stopped",
            "last_updated": datetime.utcnow().isoformat()
        }
    
    async def _health_monitor_loop(self):
        """Monitor service health periodically"""
        while self._running:
            try:
                await self._check_service_health()
                await asyncio.sleep(self._health_check_interval)
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
                await asyncio.sleep(30)
    
    async def _check_service_health(self):
        """Check health of all registered services"""
        current_time = datetime.utcnow()
        stale_threshold = timedelta(minutes=2)  # 2 minutes without heartbeat
        
        stale_services = []
        for service_id, service_info in self._services.items():
            if service_info.last_heartbeat:
                last_heartbeat = datetime.fromisoformat(service_info.last_heartbeat.replace('Z', '+00:00'))
                if current_time - last_heartbeat.replace(tzinfo=None) > stale_threshold:
                    stale_services.append(service_id)
                    logger.warning(f"Service {service_info.name} ({service_id}) has stale heartbeat")
        
        # Mark stale services as unhealthy
        for service_id in stale_services:
            if service_id in self._services:
                self._services[service_id].status = "unhealthy"
    
    def export_registry(self) -> Dict[str, Any]:
        """Export registry state for backup/migration"""
        return {
            "services": {sid: asdict(info) for sid, info in self._services.items()},
            "metrics": {sid: asdict(metrics) for sid, metrics in self._service_metrics.items()},
            "instances": self._service_instances,
            "exported_at": datetime.utcnow().isoformat()
        }
    
    def import_registry(self, registry_data: Dict[str, Any]) -> bool:
        """Import registry state from backup"""
        try:
            # Clear current state
            self._services.clear()
            self._service_metrics.clear()
            self._service_instances.clear()
            
            # Import services
            for service_id, service_data in registry_data.get("services", {}).items():
                self._services[service_id] = ServiceInfo(**service_data)
            
            # Import metrics
            for service_id, metrics_data in registry_data.get("metrics", {}).items():
                self._service_metrics[service_id] = ServiceMetrics(**metrics_data)
            
            # Import instances
            self._service_instances = registry_data.get("instances", {})
            
            logger.info(f"Imported {len(self._services)} services into registry")
            return True
            
        except Exception as e:
            logger.error(f"Failed to import registry: {e}")
            return False


# Global service registry instance
service_registry = ServiceRegistry()
