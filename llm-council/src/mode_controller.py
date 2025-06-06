"""
Mode Controller for AI Council
Controls system mode and permissions for AI Council agents
"""

import logging
from typing import Dict, List, Any, Optional, Union

# Import permission system
from core.packages.permissions.mode_permissions import (
    mode_permission, SystemMode, ModePermissionConfig
)
from core.packages.permissions.base_permissions import (
    PermissionLevel, ResourceType
)

# Import ability registry
from core.packages.ability_registry.ability_registry import (
    ability_registry, AbilityLevel
)

# Setup logging
logger = logging.getLogger(__name__)

class ModeController:
    """
    Controls the system mode and permissions for the AI Council.
    Acts as a mediator between the council, permissions, and abilities.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the mode controller
        
        Args:
            config: Configuration options
        """
        self.config = config or {}
        self.default_mode = SystemMode.ARCHIVIST
        self.current_session_id = None
        self.session_modes = {}
        
        # Load any configuration
        self._load_config()
        
        logger.info("Mode Controller initialized")
    
    def _load_config(self):
        """Load configuration if provided"""
        if "default_mode" in self.config:
            mode_name = self.config["default_mode"]
            try:
                self.default_mode = SystemMode(mode_name.lower())
                logger.info(f"Set default mode to {self.default_mode.value}")
            except ValueError:
                logger.warning(f"Invalid default mode: {mode_name}")
    
    def start_session(self, session_id: str, mode: Optional[Union[str, SystemMode]] = None) -> SystemMode:
        """
        Start a new session with a specified mode
        
        Args:
            session_id: ID for the session
            mode: Optional mode to start with (default to configured default)
            
        Returns:
            The mode set for the session
        """
        # Convert string mode to enum if needed
        if isinstance(mode, str):
            try:
                mode = SystemMode(mode.lower())
            except ValueError:
                logger.warning(f"Invalid mode: {mode}, using default")
                mode = self.default_mode
        elif mode is None:
            mode = self.default_mode
        
        # Set the mode for this session
        self.session_modes[session_id] = mode
        self.current_session_id = session_id
        
        # Register the mode with the permissions system
        mode_permission.set_user_mode(session_id, mode)
        
        logger.info(f"Started session {session_id} in {mode.value} mode")
        return mode
    
    def get_current_mode(self, session_id: Optional[str] = None) -> SystemMode:
        """
        Get the current mode for a session
        
        Args:
            session_id: ID of the session (defaults to current session)
            
        Returns:
            Current mode for the session
        """
        # Use current session if not specified
        if session_id is None:
            session_id = self.current_session_id
            if session_id is None:
                logger.warning("No current session, returning default mode")
                return self.default_mode
        
        # Get the mode
        mode = self.session_modes.get(session_id, self.default_mode)
        return mode
    
    def change_mode(self, mode: Union[str, SystemMode], session_id: Optional[str] = None) -> bool:
        """
        Change the mode for a session
        
        Args:
            mode: New mode to set
            session_id: ID of the session (defaults to current session)
            
        Returns:
            Success status
        """
        # Use current session if not specified
        if session_id is None:
            session_id = self.current_session_id
            if session_id is None:
                logger.warning("No current session, can't change mode")
                return False
        
        # Convert string mode to enum if needed
        if isinstance(mode, str):
            try:
                mode = SystemMode(mode.lower())
            except ValueError:
                logger.warning(f"Invalid mode: {mode}")
                return False
        
        # Set the new mode
        self.session_modes[session_id] = mode
        
        # Update the mode in the permissions system
        mode_permission.set_user_mode(session_id, mode)
        
        logger.info(f"Changed mode for session {session_id} to {mode.value}")
        return True
    
    def get_allowed_abilities(self, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get a list of abilities allowed for the current mode
        
        Args:
            session_id: ID of the session (defaults to current session)
            
        Returns:
            List of allowed abilities
        """
        # Get the current mode
        mode = self.get_current_mode(session_id)
        
        # Get the corresponding ability level
        ability_level = ModePermissionConfig.MODE_TO_ABILITY_LEVEL.get(mode, AbilityLevel.BASIC)
        
        # Get abilities up to this level
        abilities = []
        for level in AbilityLevel:
            if level.value <= ability_level.value:
                level_abilities = ability_registry.list_abilities(level=level)
                abilities.extend(level_abilities)
        
        logger.info(f"Retrieved {len(abilities)} allowed abilities for mode {mode.value}")
        return abilities
    
    def check_ability_access(self, ability_id: str, session_id: Optional[str] = None) -> bool:
        """
        Check if an ability can be used in the current mode
        
        Args:
            ability_id: ID of the ability to check
            session_id: ID of the session (defaults to current session)
            
        Returns:
            Whether the ability can be used
        """
        # Get the ability
        ability = ability_registry.get_ability(ability_id)
        if not ability:
            logger.warning(f"Ability {ability_id} not found")
            return False
        
        # Get the current mode
        mode = self.get_current_mode(session_id)
        
        # Get the allowed ability level for this mode
        allowed_level = ModePermissionConfig.MODE_TO_ABILITY_LEVEL.get(mode, AbilityLevel.BASIC)
        
        # Check if the ability level is allowed
        has_access = ability.level.value <= allowed_level.value
        
        logger.info(f"Access to {ability.name} ({ability_id}) in mode {mode.value}: {has_access}")
        return has_access
    
    async def check_resource_access(
        self,
        resource_id: str,
        resource_type: Union[str, ResourceType],
        permission: Union[str, PermissionLevel],
        session_id: Optional[str] = None
    ) -> bool:
        """
        Check if a resource can be accessed with the specified permission in the current mode
        
        Args:
            resource_id: ID of the resource
            resource_type: Type of the resource
            permission: Permission level needed
            session_id: ID of the session (defaults to current session)
            
        Returns:
            Whether the resource can be accessed
        """
        # Use current session if not specified
        if session_id is None:
            session_id = self.current_session_id
            if session_id is None:
                logger.warning("No current session, denying access")
                return False
        
        # Convert string resource type to enum if needed
        if isinstance(resource_type, str):
            try:
                resource_type = ResourceType(resource_type.lower())
            except ValueError:
                logger.warning(f"Invalid resource type: {resource_type}")
                return False
        
        # Convert string permission to enum if needed
        if isinstance(permission, str):
            try:
                permission = PermissionLevel(permission.lower())
            except ValueError:
                logger.warning(f"Invalid permission level: {permission}")
                return False
        
        # Check permission with the permission system
        has_permission = await mode_permission.has_permission(
            user_id=session_id,
            resource_id=resource_id,
            resource_type=resource_type,
            permission_level=permission,
            context={"controller": "mode_controller"}
        )
        
        return has_permission
    
    def get_mode_description(self, mode: Optional[Union[str, SystemMode]] = None) -> Dict[str, Any]:
        """
        Get a description of a mode and its capabilities
        
        Args:
            mode: Mode to describe (defaults to current mode)
            
        Returns:
            Description of the mode
        """
        # Use current mode if not specified
        if mode is None:
            mode = self.get_current_mode()
        
        # Convert string mode to enum if needed
        if isinstance(mode, str):
            try:
                mode = SystemMode(mode.lower())
            except ValueError:
                logger.warning(f"Invalid mode: {mode}")
                mode = self.default_mode
        
        # Get ability level for this mode
        ability_level = ModePermissionConfig.MODE_TO_ABILITY_LEVEL.get(mode)
        
        # Get permission levels for this mode
        permission_levels = ModePermissionConfig.MODE_PERMISSIONS.get(mode, {})
        
        # Format the description
        description = {
            "mode": mode.value,
            "ability_level": ability_level.name if ability_level else "UNKNOWN",
            "permissions": {
                r_type.value: p_level.value 
                for r_type, p_level in permission_levels.items()
            },
            "description": self._get_mode_description_text(mode)
        }
        
        return description
    
    def _get_mode_description_text(self, mode: SystemMode) -> str:
        """Get a textual description of a mode"""
        descriptions = {
            SystemMode.ARCHIVIST: (
                "Basic information retrieval and organization mode. "
                "Can access and read information but has limited "
                "action capabilities and reasoning."
            ),
            SystemMode.ORCHESTRATOR: (
                "Coordination and workflow mode with enhanced capabilities. "
                "Can organize tasks, create workflows, and manage basic "
                "system processes."
            ),
            SystemMode.GODFATHER: (
                "Advanced reasoning and privileged operations mode. "
                "Can make complex decisions, access sensitive information, "
                "and execute most system functions."
            ),
            SystemMode.ENTITY: (
                "Highest level mode with full system capabilities. "
                "Has unrestricted access to all system functions "
                "and can operate with minimal limitations."
            )
        }
        
        return descriptions.get(mode, "No description available.")
    
    def list_available_modes(self) -> List[Dict[str, Any]]:
        """
        Get a list of all available modes with descriptions
        
        Returns:
            List of modes with descriptions
        """
        modes = []
        
        for mode in SystemMode:
            description = self.get_mode_description(mode)
            modes.append(description)
        
        return modes
    
    def get_permissions_for_mode(
        self, 
        mode: Optional[Union[str, SystemMode]] = None
    ) -> Dict[ResourceType, PermissionLevel]:
        """
        Get the permissions available for a mode
        
        Args:
            mode: Mode to get permissions for (defaults to current mode)
            
        Returns:
            Dict of resource types to permission levels
        """
        # Use current mode if not specified
        if mode is None:
            mode = self.get_current_mode()
        
        # Convert string mode to enum if needed
        if isinstance(mode, str):
            try:
                mode = SystemMode(mode.lower())
            except ValueError:
                logger.warning(f"Invalid mode: {mode}")
                mode = self.default_mode
        
        # Get permissions for this mode
        return ModePermissionConfig.MODE_PERMISSIONS.get(mode, {})


# Create singleton instance
mode_controller = ModeController()