"""
Mode-based permission system for the Space Project.
Controls access to abilities and features based on system modes.
"""

import logging
from enum import Enum
from typing import Dict, List, Any, Optional, Set, Union
import json

# Import base permission system
from core.packages.permissions.base_permissions import (
    BasePermission, PermissionLevel, ResourceType, PermissionManager
)

# Import ability registry types
from core.packages.ability_registry.ability_registry import AbilityLevel

# Setup logging
logger = logging.getLogger(__name__)

class SystemMode(Enum):
    """System operational modes with increasing levels of capability"""
    ARCHIVIST = "archivist"       # Basic information retrieval and storage
    ORCHESTRATOR = "orchestrator" # Coordination and basic agent capabilities
    GODFATHER = "godfather"       # Advanced reasoning and privileged operations
    ENTITY = "entity"             # Full system capabilities with minimal restrictions


class ModePermissionConfig:
    """Configuration for mode-based permissions"""
    
    # Map system modes to ability levels
    MODE_TO_ABILITY_LEVEL = {
        SystemMode.ARCHIVIST: AbilityLevel.BASIC,
        SystemMode.ORCHESTRATOR: AbilityLevel.INTERMEDIATE,
        SystemMode.GODFATHER: AbilityLevel.EXPERT,
        SystemMode.ENTITY: AbilityLevel.SUPERHUMAN
    }
    
    # Map system modes to permission levels for different resource types
    MODE_PERMISSIONS = {
        SystemMode.ARCHIVIST: {
            ResourceType.DOCUMENT: PermissionLevel.READ,
            ResourceType.WORKFLOW: PermissionLevel.READ,
            ResourceType.ENGINE: PermissionLevel.READ,
            ResourceType.API: PermissionLevel.READ,
            ResourceType.MODEL: PermissionLevel.READ,
            ResourceType.SYSTEM: PermissionLevel.READ
        },
        SystemMode.ORCHESTRATOR: {
            ResourceType.DOCUMENT: PermissionLevel.WRITE,
            ResourceType.WORKFLOW: PermissionLevel.EXECUTE,
            ResourceType.ENGINE: PermissionLevel.READ,
            ResourceType.API: PermissionLevel.EXECUTE,
            ResourceType.MODEL: PermissionLevel.READ,
            ResourceType.SYSTEM: PermissionLevel.READ
        },
        SystemMode.GODFATHER: {
            ResourceType.DOCUMENT: PermissionLevel.ADMIN,
            ResourceType.WORKFLOW: PermissionLevel.ADMIN,
            ResourceType.ENGINE: PermissionLevel.EXECUTE,
            ResourceType.API: PermissionLevel.ADMIN,
            ResourceType.MODEL: PermissionLevel.EXECUTE,
            ResourceType.SYSTEM: PermissionLevel.WRITE
        },
        SystemMode.ENTITY: {
            ResourceType.DOCUMENT: PermissionLevel.ADMIN,
            ResourceType.WORKFLOW: PermissionLevel.ADMIN,
            ResourceType.ENGINE: PermissionLevel.ADMIN,
            ResourceType.API: PermissionLevel.ADMIN,
            ResourceType.MODEL: PermissionLevel.ADMIN,
            ResourceType.SYSTEM: PermissionLevel.ADMIN
        }
    }
    
    # Resource-specific permissions override
    RESOURCE_OVERRIDES = {
        # Example: Override specific resources
        "sensitive_data": {
            SystemMode.ORCHESTRATOR: PermissionLevel.READ,  # Downgrade
            SystemMode.GODFATHER: PermissionLevel.WRITE     # Downgrade
        },
        "admin_functions": {
            SystemMode.ARCHIVIST: None,  # No access
            SystemMode.ORCHESTRATOR: None  # No access
        }
    }


class ModePermission(BasePermission):
    """
    Permission implementation based on system modes.
    Controls what abilities and resources are available in each mode.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the mode permission system
        
        Args:
            config: Configuration options
        """
        super().__init__(config)
        self.user_modes: Dict[str, SystemMode] = {}
        self.overrides: Dict[str, Dict[str, PermissionLevel]] = {}
        
        # Load any custom configuration
        self._load_config()
        
        logger.info("Mode permission system initialized")
    
    def _load_config(self):
        """Load custom configuration if provided"""
        if not self.config:
            return
        
        # Load user modes if provided
        if "user_modes" in self.config:
            for user_id, mode_name in self.config["user_modes"].items():
                try:
                    mode = SystemMode(mode_name.lower())
                    self.user_modes[user_id] = mode
                    logger.info(f"Loaded mode {mode.value} for user {user_id}")
                except (ValueError, AttributeError):
                    logger.warning(f"Invalid mode {mode_name} for user {user_id}")
        
        # Load permission overrides if provided
        if "overrides" in self.config:
            self.overrides = self.config["overrides"]
    
    async def has_permission(
        self,
        user_id: str,
        resource_id: str,
        permission_level: PermissionLevel,
        resource_type: ResourceType,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Check if a user has the required permission based on their mode
        
        Args:
            user_id: ID of the user
            resource_id: ID of the resource
            permission_level: Required permission level
            resource_type: Type of the resource
            context: Additional context data
            
        Returns:
            Whether the user has the required permission
        """
        # Get the user's mode
        user_mode = self.get_user_mode(user_id)
        
        if user_mode is None:
            logger.warning(f"No mode set for user {user_id}, denying access")
            return False
        
        # Check for resource-specific overrides
        if resource_id in ModePermissionConfig.RESOURCE_OVERRIDES:
            if user_mode in ModePermissionConfig.RESOURCE_OVERRIDES[resource_id]:
                override_level = ModePermissionConfig.RESOURCE_OVERRIDES[resource_id][user_mode]
                if override_level is None:
                    logger.info(f"Resource {resource_id} explicitly denied for mode {user_mode.value}")
                    return False
                
                # Compare the permission levels
                has_access = self._compare_permission_levels(override_level, permission_level)
                logger.info(f"Override permission for {resource_id} in mode {user_mode.value}: {has_access}")
                return has_access
        
        # Get the mode's permission level for this resource type
        if resource_type not in ModePermissionConfig.MODE_PERMISSIONS[user_mode]:
            logger.warning(f"Resource type {resource_type} not defined for mode {user_mode.value}")
            return False
        
        mode_permission = ModePermissionConfig.MODE_PERMISSIONS[user_mode][resource_type]
        
        # Compare the permission levels
        has_access = self._compare_permission_levels(mode_permission, permission_level)
        
        logger.info(f"Permission check for user {user_id} on {resource_id} ({resource_type.value}): {has_access}")
        return has_access
    
    def _compare_permission_levels(
        self, 
        actual: PermissionLevel, 
        required: PermissionLevel
    ) -> bool:
        """
        Compare permission levels to determine if access should be granted
        
        Args:
            actual: The permission level the user has
            required: The permission level required
            
        Returns:
            Whether access should be granted
        """
        # Permission hierarchy
        hierarchy = {
            PermissionLevel.READ: 1,
            PermissionLevel.WRITE: 2,
            PermissionLevel.EXECUTE: 3,
            PermissionLevel.ADMIN: 4
        }
        
        # Higher permission includes lower permissions
        return hierarchy.get(actual, 0) >= hierarchy.get(required, 0)
    
    async def grant_permission(
        self,
        user_id: str,
        resource_id: str,
        permission_level: PermissionLevel,
        resource_type: ResourceType,
        granted_by: str
    ) -> bool:
        """
        Grant a specific permission override for a user
        
        Args:
            user_id: ID of the user
            resource_id: ID of the resource
            permission_level: Permission level to grant
            resource_type: Type of the resource
            granted_by: ID of the user granting the permission
            
        Returns:
            Success status
        """
        # Check if the granting user has admin rights
        granter_mode = self.get_user_mode(granted_by)
        if granter_mode != SystemMode.ENTITY:
            logger.warning(f"User {granted_by} does not have permission to grant permissions")
            return False
        
        # Create the override
        if user_id not in self.overrides:
            self.overrides[user_id] = {}
        
        override_key = f"{resource_id}:{resource_type.value}"
        self.overrides[user_id][override_key] = permission_level
        
        logger.info(f"Granted {permission_level.value} permission on {resource_id} to {user_id}")
        return True
    
    async def revoke_permission(
        self,
        user_id: str,
        resource_id: str,
        permission_level: PermissionLevel,
        resource_type: ResourceType,
        revoked_by: str
    ) -> bool:
        """
        Revoke a specific permission override for a user
        
        Args:
            user_id: ID of the user
            resource_id: ID of the resource
            permission_level: Permission level to revoke
            resource_type: Type of the resource
            revoked_by: ID of the user revoking the permission
            
        Returns:
            Success status
        """
        # Check if the revoking user has admin rights
        revoker_mode = self.get_user_mode(revoked_by)
        if revoker_mode != SystemMode.ENTITY:
            logger.warning(f"User {revoked_by} does not have permission to revoke permissions")
            return False
        
        # Remove the override if it exists
        if user_id in self.overrides:
            override_key = f"{resource_id}:{resource_type.value}"
            if override_key in self.overrides[user_id]:
                del self.overrides[user_id][override_key]
                
                logger.info(f"Revoked permission on {resource_id} from {user_id}")
                return True
        
        logger.info(f"No permission found to revoke for {user_id} on {resource_id}")
        return False
    
    def set_user_mode(self, user_id: str, mode: Union[str, SystemMode]) -> bool:
        """
        Set a user's system mode
        
        Args:
            user_id: ID of the user
            mode: Mode to set
            
        Returns:
            Success status
        """
        # Convert string mode to enum if needed
        if isinstance(mode, str):
            try:
                mode = SystemMode(mode.lower())
            except ValueError:
                logger.warning(f"Invalid mode: {mode}")
                return False
        
        # Set the mode
        self.user_modes[user_id] = mode
        logger.info(f"Set mode {mode.value} for user {user_id}")
        return True
    
    def get_user_mode(self, user_id: str) -> Optional[SystemMode]:
        """
        Get a user's current system mode
        
        Args:
            user_id: ID of the user
            
        Returns:
            The user's current mode
        """
        mode = self.user_modes.get(user_id)
        
        # Default to ARCHIVIST if no mode is set
        if mode is None:
            mode = SystemMode.ARCHIVIST
            self.user_modes[user_id] = mode
            logger.info(f"Default mode {mode.value} set for new user {user_id}")
        
        return mode
    
    def get_ability_level_for_mode(self, mode: Union[str, SystemMode]) -> AbilityLevel:
        """
        Get the ability level corresponding to a system mode
        
        Args:
            mode: System mode
            
        Returns:
            Corresponding ability level
        """
        # Convert string mode to enum if needed
        if isinstance(mode, str):
            try:
                mode = SystemMode(mode.lower())
            except ValueError:
                logger.warning(f"Invalid mode: {mode}, defaulting to ARCHIVIST")
                mode = SystemMode.ARCHIVIST
        
        # Get the ability level
        return ModePermissionConfig.MODE_TO_ABILITY_LEVEL.get(mode, AbilityLevel.BASIC)
    
    def get_allowed_ability_level(self, user_id: str) -> AbilityLevel:
        """
        Get the allowed ability level for a user based on their mode
        
        Args:
            user_id: ID of the user
            
        Returns:
            Allowed ability level
        """
        mode = self.get_user_mode(user_id)
        return self.get_ability_level_for_mode(mode)
    
    def export_permissions(self) -> Dict[str, Any]:
        """
        Export the current permission configuration
        
        Returns:
            Dictionary of permission configuration
        """
        return {
            "user_modes": {
                user_id: mode.value 
                for user_id, mode in self.user_modes.items()
            },
            "overrides": self.overrides
        }
    
    def import_permissions(self, data: Dict[str, Any]) -> bool:
        """
        Import permission configuration
        
        Args:
            data: Permission configuration data
            
        Returns:
            Success status
        """
        try:
            # Import user modes
            if "user_modes" in data:
                for user_id, mode_name in data["user_modes"].items():
                    self.set_user_mode(user_id, mode_name)
            
            # Import overrides
            if "overrides" in data:
                self.overrides = data["overrides"]
            
            logger.info("Successfully imported permissions")
            return True
        except Exception as e:
            logger.error(f"Error importing permissions: {str(e)}")
            return False


# Create singleton instance
mode_permission = ModePermission()