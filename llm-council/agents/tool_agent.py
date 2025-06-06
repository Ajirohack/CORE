"""
Tool Agent for AI Council
Acts as an interface to system abilities and tools
"""

import logging
import json
from typing import Dict, List, Any, Optional, Union, Callable
import autogen
from autogen.agentchat.agent import Agent

# Import the ability registry
from core.packages.ability_registry.ability_registry import (
    ability_registry, Ability, AbilityLevel, AbilityScope
)

# Setup logging
logger = logging.getLogger(__name__)

class ToolAgent(autogen.ConversableAgent):
    """
    Tool Agent that interfaces with the system's abilities and tools.
    This agent handles the execution of tools and abilities based on user
    permissions and request requirements.
    """
    
    def __init__(
        self, 
        name: str, 
        system_message: str, 
        llm_config: Dict[str, Any],
        access_level: str = "basic"
    ):
        """
        Initialize the Tool Agent
        
        Args:
            name: Name of the agent
            system_message: The system message that defines the agent's role
            llm_config: Configuration for the language model
            access_level: Access level for abilities (basic, intermediate, advanced, expert, superhuman)
        """
        super().__init__(
            name=name,
            system_message=system_message,
            llm_config=llm_config
        )
        
        # Set the access level
        self.access_level = access_level
        self.access_level_map = {
            "basic": AbilityLevel.BASIC,
            "intermediate": AbilityLevel.INTERMEDIATE,
            "advanced": AbilityLevel.ADVANCED,
            "expert": AbilityLevel.EXPERT,
            "superhuman": AbilityLevel.SUPERHUMAN
        }
        
        # Initialize available abilities based on access level
        self._initialize_abilities()
        
        # Register ability execution function
        self._register_functions()
        
        logger.info(f"Tool Agent '{name}' initialized with access level: {access_level}")
    
    def _initialize_abilities(self):
        """Initialize available abilities based on access level"""
        # Get the numeric access level
        access_level_enum = self.access_level_map.get(
            self.access_level.lower(), 
            AbilityLevel.BASIC
        )
        
        # Get all abilities up to the current access level
        self.available_abilities = {}
        
        # Filter abilities by access level
        for level in AbilityLevel:
            if level.value <= access_level_enum.value:
                level_abilities = ability_registry.list_abilities(level=level)
                for ability_dict in level_abilities:
                    ability_id = ability_dict["id"]
                    ability = ability_registry.get_ability(ability_id)
                    if ability:
                        self.available_abilities[ability_id] = ability
        
        logger.info(f"Initialized {len(self.available_abilities)} abilities for access level: {self.access_level}")
    
    def _register_functions(self):
        """Register functions for the agent"""
        self.register_function(
            function_map={
                "list_abilities": self.list_abilities,
                "execute_ability": self.execute_ability,
                "get_ability_details": self.get_ability_details
            }
        )
    
    def set_access_level(self, access_level: str):
        """
        Set the agent's access level
        
        Args:
            access_level: New access level
        """
        self.access_level = access_level.lower()
        self._initialize_abilities()
        logger.info(f"Updated access level to: {self.access_level}")
    
    def list_abilities(
        self, 
        scope: Optional[str] = None, 
        tags: Optional[List[str]] = None
    ) -> str:
        """
        List available abilities, optionally filtered by scope or tags
        
        Args:
            scope: Optional scope to filter by
            tags: Optional tags to filter by
            
        Returns:
            Formatted string of available abilities
        """
        filtered_abilities = []
        
        for ability_id, ability in self.available_abilities.items():
            # Apply scope filter if provided
            if scope and ability.scope.value != scope:
                continue
                
            # Apply tags filter if provided
            if tags and not all(tag in ability.tags for tag in tags):
                continue
                
            filtered_abilities.append(ability)
        
        # Sort abilities by level
        filtered_abilities.sort(key=lambda a: a.level.value)
        
        if not filtered_abilities:
            return "No abilities found matching the specified criteria."
        
        # Format the result
        result = "Available abilities:\n\n"
        
        for ability in filtered_abilities:
            result += f"- {ability.name} (Level: {ability.level.name})\n"
            result += f"  Description: {ability.description}\n"
            result += f"  ID: {ability.id}\n"
            if ability.tags:
                result += f"  Tags: {', '.join(ability.tags)}\n"
            result += "\n"
        
        return result
    
    def get_ability_details(self, ability_id: str) -> str:
        """
        Get detailed information about a specific ability
        
        Args:
            ability_id: ID of the ability
            
        Returns:
            Detailed information about the ability
        """
        ability = self.available_abilities.get(ability_id)
        
        if not ability:
            return f"Ability with ID '{ability_id}' not found or not available at your access level."
        
        result = f"Ability: {ability.name}\n"
        result += f"ID: {ability.id}\n"
        result += f"Description: {ability.description}\n"
        result += f"Scope: {ability.scope.value}\n"
        result += f"Level: {ability.level.name} ({ability.level.value})\n"
        
        if ability.tags:
            result += f"Tags: {', '.join(ability.tags)}\n"
        
        if ability.requirements:
            result += "Requirements: "
            req_details = []
            for req_id in ability.requirements:
                req_ability = ability_registry.get_ability(req_id)
                if req_ability:
                    req_details.append(f"{req_ability.name} ({req_id})")
                else:
                    req_details.append(req_id)
            result += ", ".join(req_details) + "\n"
        
        if ability.parameters:
            result += "Parameters:\n"
            for param_name, param_details in ability.parameters.items():
                result += f"  - {param_name}: {param_details}\n"
        
        return result
    
    async def execute_ability(
        self, 
        ability_id: str, 
        parameters: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Execute an ability with the provided parameters
        
        Args:
            ability_id: ID of the ability to execute
            parameters: Parameters to pass to the ability
            
        Returns:
            Result of the ability execution
        """
        # Check if the ability exists and is available
        ability = self.available_abilities.get(ability_id)
        
        if not ability:
            return f"Error: Ability '{ability_id}' not found or not available at your access level."
        
        logger.info(f"Executing ability: {ability.name} ({ability_id})")
        
        # Check if implementation is available
        if not ability.implementation:
            return f"Error: Ability '{ability.name}' does not have an implementation."
        
        # Validate parameters
        parameters = parameters or {}
        required_params = {
            name: details for name, details in ability.parameters.items() 
            if details.get("required", False)
        }
        
        missing_params = [
            name for name in required_params 
            if name not in parameters
        ]
        
        if missing_params:
            return f"Error: Missing required parameters: {', '.join(missing_params)}"
        
        try:
            # Execute the ability
            result = ability.implementation(**parameters)
            return f"Successfully executed ability '{ability.name}':\n{result}"
        except Exception as e:
            logger.error(f"Error executing ability '{ability.name}': {str(e)}")
            return f"Error executing ability '{ability.name}': {str(e)}"
    
    def _filter_abilities_by_mode(self, mode: str) -> List[Ability]:
        """
        Filter abilities based on the system mode
        
        Args:
            mode: System mode (archivist, orchestrator, godfather, entity)
            
        Returns:
            List of allowed abilities for the mode
        """
        # Map modes to maximum allowed ability levels
        mode_levels = {
            "archivist": AbilityLevel.BASIC,
            "orchestrator": AbilityLevel.INTERMEDIATE,
            "godfather": AbilityLevel.EXPERT,
            "entity": AbilityLevel.SUPERHUMAN
        }
        
        # Get maximum level for the mode
        max_level = mode_levels.get(mode.lower(), AbilityLevel.BASIC)
        
        # Filter abilities by level
        filtered = []
        for ability in self.available_abilities.values():
            if ability.level.value <= max_level.value:
                filtered.append(ability)
        
        return filtered
    
    async def process_request_with_tools(
        self, 
        request: str,
        mode: str = "archivist"
    ) -> str:
        """
        Process a request using appropriate tools based on system mode
        
        Args:
            request: The user request to process
            mode: System mode determining tool access
            
        Returns:
            Result of processing with appropriate tools
        """
        # Filter abilities by mode
        allowed_abilities = self._filter_abilities_by_mode(mode)
        
        # Log available abilities for this mode
        logger.info(f"Processing request in {mode} mode with {len(allowed_abilities)} available abilities")
        
        # This would typically involve LLM to determine which abilities to use
        # For now, we'll return a placeholder
        
        ability_names = [ability.name for ability in allowed_abilities[:5]]
        
        return f"Processed request in {mode} mode. Available tools: {', '.join(ability_names)}"