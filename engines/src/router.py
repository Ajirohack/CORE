"""
Router for the System Engine Control.
Handles mode-based routing and permission checks.
"""
import logging
from typing import Dict, Any

from .schemas import EngineState, UserMode

# Set up logging
logger = logging.getLogger("engine_control.router")


def route_by_mode(state: EngineState) -> str:
    """
    Route a request to the appropriate engine based on the user mode.
    
    Args:
        state: Current state with user mode
        
    Returns:
        Name of the engine node to route to
    """
    mode = state.get("mode", "").lower()
    logger.info(f"Routing request with mode: {mode}")
    
    engine_node = get_engine_for_mode(mode)
    logger.info(f"Selected engine: {engine_node}")
    
    return engine_node


def get_engine_for_mode(mode: str) -> str:
    """
    Get the engine node name for a given user mode.
    
    Args:
        mode: User mode
        
    Returns:
        Name of the engine node
    """
    mode_lower = mode.lower()
    
    if mode_lower == UserMode.ARCHIVIST or mode_lower == "archivist":
        return "engine_1"
    elif mode_lower == UserMode.ORCHESTRATOR or mode_lower == "orchestrator":
        return "engine_2"
    elif mode_lower == UserMode.GODFATHER or mode_lower == "godfather":
        return "engine_3"
    elif mode_lower == UserMode.ENTITY or mode_lower == "entity":
        return "engine_4"
    else:
        # Default to Engine 1 (Archivist)
        logger.warning(f"Unknown mode: {mode}, defaulting to Engine 1")
        return "engine_1"


def check_permissions(state: EngineState) -> EngineState:
    """
    Check if the user has permission to use the specified mode.
    
    Args:
        state: Current state with user ID and mode
        
    Returns:
        Updated state, potentially with an error if permission is denied
    """
    user_id = state.get("user_id", "")
    mode = state.get("mode", "")
    
    logger.info(f"Checking permissions for user {user_id} with mode {mode}")
    
    # In a real implementation, this would check against a user database
    # For now, we'll assume all modes are accessible for demo purposes
    has_permission = True
    
    # Example permission check:
    # has_permission = check_user_permission(user_id, mode)
    
    if not has_permission:
        logger.warning(f"Permission denied for user {user_id} with mode {mode}")
        state["error"] = f"Permission denied: User {user_id} does not have access to {mode} mode"
        # Default to Archivist mode
        state["mode"] = "archivist"
    
    return state


def mode_to_engine_number(mode: str) -> int:
    """
    Convert a mode string to an engine number.
    
    Args:
        mode: User mode
        
    Returns:
        Engine number (1-4)
    """
    mode_lower = mode.lower()
    
    if mode_lower == UserMode.ARCHIVIST or mode_lower == "archivist":
        return 1
    elif mode_lower == UserMode.ORCHESTRATOR or mode_lower == "orchestrator":
        return 2
    elif mode_lower == UserMode.GODFATHER or mode_lower == "godfather":
        return 3
    elif mode_lower == UserMode.ENTITY or mode_lower == "entity":
        return 4
    else:
        return 1  # Default to Engine 1