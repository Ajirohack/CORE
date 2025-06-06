from typing import Set, List, Dict, Optional

class AccessMode:
    """Class to represent an access mode."""
    def __init__(self, name: str, description: str, permissions: Set[str]):
        self.name = name
        self.description = description
        self.permissions = permissions


class AccessControl:
    """Class to manage access modes and permissions."""
    def __init__(self):
        self.modes = {}
        self._initialize_default_modes()

    def _initialize_default_modes(self):
        """Initialize default access modes."""
        self.register_mode(
            name="archivist",
            description="Basic access mode with limited permissions",
            permissions={"basic_tools", "read_knowledge"}
        )
        self.register_mode(
            name="orchestrator",
            description="Standard access mode with moderate permissions",
            permissions={"basic_tools", "read_knowledge", "write_knowledge", "advanced_tools"}
        )
        self.register_mode(
            name="godfather",
            description="Advanced access mode with extended permissions",
            permissions={"basic_tools", "read_knowledge", "write_knowledge", "advanced_tools", "admin_tools"}
        )
        self.register_mode(
            name="entity",
            description="Full access mode with all permissions",
            permissions={"basic_tools", "read_knowledge", "write_knowledge", "advanced_tools", "admin_tools", "unrestricted"}
        )

    def register_mode(self, name: str, description: str, permissions: Set[str]):
        """Register a new access mode."""
        self.modes[name] = AccessMode(
            name=name,
            description=description,
            permissions=permissions
        )

    def get_permissions(self, mode: str) -> Set[str]:
        """Get permissions for a given mode."""
        mode_obj = self.modes.get(mode)
        return mode_obj.permissions if mode_obj else set()

    def has_permission(self, mode: str, permission: str) -> bool:
        """Check if a mode has a specific permission."""
        return permission in self.get_permissions(mode)

    def list_modes(self) -> List[str]:
        """List all available modes."""
        return list(self.modes.keys())
        
    def get_mode_details(self, mode: str) -> Optional[Dict]:
        """Get full details for a specific mode."""
        mode_obj = self.modes.get(mode)
        if not mode_obj:
            return None
        
        return {
            "name": mode_obj.name,
            "description": mode_obj.description,
            "permissions": list(mode_obj.permissions)
        }
    
    def add_permissions_to_mode(self, mode: str, permissions: Set[str]) -> bool:
        """Add permissions to an existing mode."""
        mode_obj = self.modes.get(mode)
        if not mode_obj:
            return False
            
        mode_obj.permissions.update(permissions)
        return True
        
    def remove_permissions_from_mode(self, mode: str, permissions: Set[str]) -> bool:
        """Remove permissions from an existing mode."""
        mode_obj = self.modes.get(mode)
        if not mode_obj:
            return False
            
        mode_obj.permissions.difference_update(permissions)
        return True