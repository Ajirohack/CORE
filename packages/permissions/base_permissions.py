"""Base permissions system for the space project."""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from utils.logging import logger
from utils.metrics import collector

class PermissionLevel(Enum):
    """Permission levels for the system."""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    ADMIN = "admin"

class ResourceType(Enum):
    """Types of resources that can be protected."""
    DOCUMENT = "document"
    WORKFLOW = "workflow"
    ENGINE = "engine"
    API = "api"
    MODEL = "model"
    SYSTEM = "system"

class BasePermission(ABC):
    """Abstract base class for permissions."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logger
        self.metrics = collector
    
    @abstractmethod
    async def has_permission(
        self,
        user_id: str,
        resource_id: str,
        permission_level: PermissionLevel,
        resource_type: ResourceType,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Check if a user has the required permission."""
        pass
    
    @abstractmethod
    async def grant_permission(
        self,
        user_id: str,
        resource_id: str,
        permission_level: PermissionLevel,
        resource_type: ResourceType,
        granted_by: str
    ) -> bool:
        """Grant a permission to a user."""
        pass
    
    @abstractmethod
    async def revoke_permission(
        self,
        user_id: str,
        resource_id: str,
        permission_level: PermissionLevel,
        resource_type: ResourceType,
        revoked_by: str
    ) -> bool:
        """Revoke a permission from a user."""
        pass

class PermissionManager:
    """Manages permissions across the system."""
    
    def __init__(self, permission_backend: BasePermission):
        self.backend = permission_backend
        self.logger = logger
        self.metrics = collector
        self._permission_cache: Dict[str, Set[str]] = {}
    
    async def check_permission(
        self,
        user_id: str,
        resource_id: str,
        required_level: PermissionLevel,
        resource_type: ResourceType,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Check if a user has the required permission level."""
        cache_key = f"{user_id}:{resource_id}:{required_level.value}"
        
        # Check cache first
        if cache_key in self._permission_cache:
            return True
            
        with self.metrics.measure_time("permission_check"):
            try:
                has_permission = await self.backend.has_permission(
                    user_id,
                    resource_id,
                    required_level,
                    resource_type,
                    context
                )
                
                if has_permission:
                    self._permission_cache.add(cache_key)
                    
                return has_permission
                
            except Exception as e:
                self.logger.error(f"Error checking permissions: {e}")
                return False
    
    async def batch_check_permissions(
        self,
        user_id: str,
        resources: List[Dict[str, Any]],
        required_level: PermissionLevel
    ) -> Dict[str, bool]:
        """Check permissions for multiple resources at once."""
        results = {}
        for resource in resources:
            resource_id = resource["id"]
            resource_type = ResourceType(resource["type"])
            
            has_access = await self.check_permission(
                user_id,
                resource_id,
                required_level,
                resource_type,
                context=resource.get("context")
            )
            results[resource_id] = has_access
            
        return results
    
    def invalidate_cache(
        self,
        user_id: Optional[str] = None,
        resource_id: Optional[str] = None
    ) -> None:
        """Invalidate permission cache entries."""
        if user_id and resource_id:
            # Remove specific entries
            prefix = f"{user_id}:{resource_id}"
            self._permission_cache = {
                k: v for k, v in self._permission_cache.items()
                if not k.startswith(prefix)
            }
        elif user_id:
            # Remove all entries for user
            self._permission_cache = {
                k: v for k, v in self._permission_cache.items()
                if not k.startswith(f"{user_id}:")
            }
        else:
            # Clear entire cache
            self._permission_cache.clear()