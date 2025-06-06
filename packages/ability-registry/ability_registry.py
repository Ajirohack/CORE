"""
Ability Registry System for Space Project
Manages abilities, capabilities, and traits for AI agents
"""

import logging
import uuid
from typing import Dict, List, Any, Optional, Callable, Type, Union, Set
from enum import Enum
from dataclasses import dataclass, field
import json

# Setup logging
logger = logging.getLogger(__name__)


class AbilityScope(Enum):
    """Scope/domain of an ability"""
    COGNITIVE = "cognitive"      # Thinking, reasoning, problem-solving
    PERCEPTION = "perception"    # Understanding, interpreting data/input
    ACTION = "action"            # Taking actions, manipulating
    SOCIAL = "social"            # Communication, interaction
    CREATIVE = "creative"        # Generation, innovation
    MEMORY = "memory"            # Storage, retrieval, organization
    SYSTEM = "system"            # System-level operations
    CUSTOM = "custom"            # User-defined scope


class AbilityLevel(Enum):
    """Proficiency level of an ability"""
    BASIC = 1        # Fundamental capability
    INTERMEDIATE = 2 # Enhanced capability
    ADVANCED = 3     # Sophisticated capability
    EXPERT = 4       # Mastery of capability
    SUPERHUMAN = 5   # Beyond human capability


@dataclass
class Ability:
    """
    Represents a specific ability or capability that an agent can possess
    """
    id: str
    name: str
    description: str
    scope: AbilityScope
    level: AbilityLevel
    tags: List[str] = field(default_factory=list)
    requirements: List[str] = field(default_factory=list)  # IDs of prerequisite abilities
    parameters: Dict[str, Any] = field(default_factory=dict)
    implementation: Optional[Callable] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validation after initialization"""
        # Convert string scope to enum if needed
        if isinstance(self.scope, str):
            try:
                self.scope = AbilityScope(self.scope)
            except ValueError:
                logger.warning(f"Unknown scope: {self.scope}. Setting to CUSTOM.")
                self.scope = AbilityScope.CUSTOM
        
        # Convert string level to enum if needed
        if isinstance(self.level, str):
            try:
                self.level = AbilityLevel(self.level)
            except ValueError:
                logger.warning(f"Unknown level: {self.level}. Setting to BASIC.")
                self.level = AbilityLevel.BASIC
    
    def to_dict(self, include_impl: bool = False) -> Dict[str, Any]:
        """
        Convert ability to a dictionary representation
        
        Args:
            include_impl: Whether to include the implementation
            
        Returns:
            Ability as a dictionary
        """
        result = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "scope": self.scope.value,
            "level": self.level.value,
            "tags": self.tags,
            "requirements": self.requirements,
            "parameters": self.parameters,
            "metadata": self.metadata
        }
        
        if include_impl and self.implementation is not None:
            result["implementation"] = str(self.implementation)
        
        return result


@dataclass
class Trait:
    """
    Represents a trait or characteristic that can be assigned to agents
    Traits influence behavior but don't provide direct capabilities
    """
    id: str
    name: str
    description: str
    influence: Dict[str, float]  # How this trait influences different behavior aspects
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert trait to a dictionary representation
        
        Returns:
            Trait as a dictionary
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "influence": self.influence,
            "tags": self.tags,
            "metadata": self.metadata
        }


class AbilityRegistry:
    """
    Registry for storing and retrieving abilities and traits
    """
    
    def __init__(self):
        """Initialize the ability registry"""
        self.abilities: Dict[str, Ability] = {}
        self.traits: Dict[str, Trait] = {}
        self.scope_index: Dict[AbilityScope, List[str]] = {
            scope: [] for scope in AbilityScope
        }
        self.tag_index: Dict[str, List[str]] = {}
        self.level_index: Dict[AbilityLevel, List[str]] = {
            level: [] for level in AbilityLevel
        }
        
        logger.info("Ability Registry initialized")
    
    def register_ability(
        self,
        name: str,
        description: str,
        scope: Union[str, AbilityScope],
        level: Union[str, AbilityLevel],
        tags: List[str] = None,
        requirements: List[str] = None,
        parameters: Dict[str, Any] = None,
        implementation: Optional[Callable] = None,
        metadata: Dict[str, Any] = None,
        ability_id: Optional[str] = None
    ) -> str:
        """
        Register a new ability in the registry
        
        Args:
            name: Name of the ability
            description: Description of what the ability does
            scope: Scope/domain of the ability
            level: Proficiency level of the ability
            tags: List of tags for categorizing the ability
            requirements: IDs of prerequisite abilities
            parameters: Parameters for the ability
            implementation: Function implementing the ability
            metadata: Additional metadata
            ability_id: Optional custom ID (auto-generated if not provided)
            
        Returns:
            ID of the registered ability
        """
        # Convert scope and level to enum if they are strings
        if isinstance(scope, str):
            try:
                scope = AbilityScope(scope)
            except ValueError:
                logger.warning(f"Unknown scope: {scope}. Setting to CUSTOM.")
                scope = AbilityScope.CUSTOM
        
        if isinstance(level, str):
            try:
                level = AbilityLevel(level)
            except ValueError:
                logger.warning(f"Unknown level: {level}. Setting to BASIC.")
                level = AbilityLevel.BASIC
        
        # Generate an ID if not provided
        ability_id = ability_id or f"ability_{uuid.uuid4()}"
        
        # Create the ability
        ability = Ability(
            id=ability_id,
            name=name,
            description=description,
            scope=scope,
            level=level,
            tags=tags or [],
            requirements=requirements or [],
            parameters=parameters or {},
            implementation=implementation,
            metadata=metadata or {}
        )
        
        # Add to registry
        self.abilities[ability_id] = ability
        
        # Update indexes
        self.scope_index[ability.scope].append(ability_id)
        
        for tag in ability.tags:
            if tag not in self.tag_index:
                self.tag_index[tag] = []
            self.tag_index[tag].append(ability_id)
        
        self.level_index[ability.level].append(ability_id)
        
        logger.info(f"Registered ability '{name}' with ID '{ability_id}'")
        return ability_id
    
    def register_trait(
        self,
        name: str,
        description: str,
        influence: Dict[str, float],
        tags: List[str] = None,
        metadata: Dict[str, Any] = None,
        trait_id: Optional[str] = None
    ) -> str:
        """
        Register a new trait in the registry
        
        Args:
            name: Name of the trait
            description: Description of the trait
            influence: How this trait influences different behavior aspects
            tags: List of tags for categorizing the trait
            metadata: Additional metadata
            trait_id: Optional custom ID (auto-generated if not provided)
            
        Returns:
            ID of the registered trait
        """
        # Generate an ID if not provided
        trait_id = trait_id or f"trait_{uuid.uuid4()}"
        
        # Create the trait
        trait = Trait(
            id=trait_id,
            name=name,
            description=description,
            influence=influence,
            tags=tags or [],
            metadata=metadata or {}
        )
        
        # Add to registry
        self.traits[trait_id] = trait
        
        # Update tag index for traits
        for tag in trait.tags:
            if tag not in self.tag_index:
                self.tag_index[tag] = []
            self.tag_index[tag].append(trait_id)
        
        logger.info(f"Registered trait '{name}' with ID '{trait_id}'")
        return trait_id
    
    def get_ability(self, ability_id: str) -> Optional[Ability]:
        """
        Get an ability by ID
        
        Args:
            ability_id: ID of the ability
            
        Returns:
            Ability if found, else None
        """
        return self.abilities.get(ability_id)
    
    def get_trait(self, trait_id: str) -> Optional[Trait]:
        """
        Get a trait by ID
        
        Args:
            trait_id: ID of the trait
            
        Returns:
            Trait if found, else None
        """
        return self.traits.get(trait_id)
    
    def list_abilities(
        self,
        scope: Optional[Union[str, AbilityScope]] = None,
        level: Optional[Union[str, AbilityLevel]] = None,
        tags: Optional[List[str]] = None,
        min_level: Optional[Union[str, AbilityLevel]] = None
    ) -> List[Dict[str, Any]]:
        """
        List abilities, optionally filtered by criteria
        
        Args:
            scope: Filter by scope
            level: Filter by exact level
            tags: Filter by tags (requires all tags)
            min_level: Filter by minimum level
            
        Returns:
            List of ability dictionaries
        """
        # Convert string scope to enum if needed
        if isinstance(scope, str):
            try:
                scope = AbilityScope(scope)
            except ValueError:
                logger.warning(f"Unknown scope: {scope}. Ignoring scope filter.")
                scope = None
        
        # Convert string level to enum if needed
        if isinstance(level, str):
            try:
                level = AbilityLevel(level)
            except ValueError:
                logger.warning(f"Unknown level: {level}. Ignoring level filter.")
                level = None
        
        # Convert string min_level to enum if needed
        if isinstance(min_level, str):
            try:
                min_level = AbilityLevel(min_level)
            except ValueError:
                logger.warning(f"Unknown min_level: {min_level}. Ignoring min_level filter.")
                min_level = None
        
        # Start with all ability IDs
        ability_ids = set(self.abilities.keys())
        
        # Filter by scope if specified
        if scope is not None:
            scope_ids = set(self.scope_index.get(scope, []))
            ability_ids = ability_ids.intersection(scope_ids)
        
        # Filter by exact level if specified
        if level is not None:
            level_ids = set(self.level_index.get(level, []))
            ability_ids = ability_ids.intersection(level_ids)
        
        # Filter by minimum level if specified
        if min_level is not None:
            min_level_ids = set()
            for l in AbilityLevel:
                if l.value >= min_level.value:
                    min_level_ids.update(self.level_index.get(l, []))
            ability_ids = ability_ids.intersection(min_level_ids)
        
        # Filter by tags if specified
        if tags:
            for tag in tags:
                tag_ids = set(self.tag_index.get(tag, []))
                ability_ids = ability_ids.intersection(tag_ids)
        
        # Convert abilities to dictionaries
        return [self.abilities[aid].to_dict() for aid in ability_ids]
    
    def list_traits(
        self,
        tags: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        List traits, optionally filtered by tags
        
        Args:
            tags: Filter by tags (requires all tags)
            
        Returns:
            List of trait dictionaries
        """
        # Start with all trait IDs
        trait_ids = set(self.traits.keys())
        
        # Filter by tags if specified
        if tags:
            for tag in tags:
                tag_ids = set(self.tag_index.get(tag, []))
                trait_ids = trait_ids.intersection(tag_ids)
        
        # Convert traits to dictionaries
        return [self.traits[tid].to_dict() for tid in trait_ids]
    
    def ability_exists(self, ability_id: str) -> bool:
        """
        Check if an ability exists in the registry
        
        Args:
            ability_id: ID of the ability
            
        Returns:
            True if the ability exists, False otherwise
        """
        return ability_id in self.abilities
    
    def trait_exists(self, trait_id: str) -> bool:
        """
        Check if a trait exists in the registry
        
        Args:
            trait_id: ID of the trait
            
        Returns:
            True if the trait exists, False otherwise
        """
        return trait_id in self.traits
    
    def get_ability_requirements_graph(self, ability_id: str) -> Dict[str, Any]:
        """
        Get a graph of requirements for an ability
        
        Args:
            ability_id: ID of the ability
            
        Returns:
            Dict representation of the requirements graph
        """
        if not self.ability_exists(ability_id):
            logger.warning(f"Ability '{ability_id}' not found")
            return {"error": f"Ability '{ability_id}' not found"}
        
        graph = {}
        visited = set()
        
        def build_graph(current_id):
            if current_id in visited:
                return  # Avoid cycles
            
            if not self.ability_exists(current_id):
                return  # Skip non-existent abilities
            
            visited.add(current_id)
            current = self.get_ability(current_id)
            
            node = {
                "id": current.id,
                "name": current.name,
                "level": current.level.value,
                "requirements": {}
            }
            
            for req_id in current.requirements:
                if self.ability_exists(req_id):
                    node["requirements"][req_id] = build_graph(req_id)
            
            return node
        
        return build_graph(ability_id)
    
    def export_registry(self) -> Dict[str, Any]:
        """
        Export the entire registry as a dictionary
        
        Returns:
            Dict representation of the registry
        """
        return {
            "abilities": {aid: ability.to_dict() for aid, ability in self.abilities.items()},
            "traits": {tid: trait.to_dict() for tid, trait in self.traits.items()}
        }
    
    def import_registry(self, data: Dict[str, Any]) -> None:
        """
        Import registry data
        
        Args:
            data: Registry data to import
        """
        # Import abilities
        for ability_id, ability_data in data.get("abilities", {}).items():
            if not self.ability_exists(ability_id):
                self.register_ability(
                    name=ability_data["name"],
                    description=ability_data["description"],
                    scope=ability_data["scope"],
                    level=ability_data["level"],
                    tags=ability_data.get("tags", []),
                    requirements=ability_data.get("requirements", []),
                    parameters=ability_data.get("parameters", {}),
                    metadata=ability_data.get("metadata", {}),
                    ability_id=ability_id
                )
        
        # Import traits
        for trait_id, trait_data in data.get("traits", {}).items():
            if not self.trait_exists(trait_id):
                self.register_trait(
                    name=trait_data["name"],
                    description=trait_data["description"],
                    influence=trait_data["influence"],
                    tags=trait_data.get("tags", []),
                    metadata=trait_data.get("metadata", {}),
                    trait_id=trait_id
                )
        
        logger.info(f"Imported {len(data.get('abilities', {}))} abilities and {len(data.get('traits', {}))} traits")


# Create singleton instance
ability_registry = AbilityRegistry()


# Decorator for registering abilities
def ability(
    name: str,
    description: str,
    scope: Union[str, AbilityScope],
    level: Union[str, AbilityLevel],
    tags: List[str] = None,
    requirements: List[str] = None,
    parameters: Dict[str, Any] = None,
    metadata: Dict[str, Any] = None
):
    """
    Decorator to register a function as an ability
    
    Args:
        name: Name of the ability
        description: Description of the ability
        scope: Scope/domain of the ability
        level: Proficiency level of the ability
        tags: List of tags for categorizing the ability
        requirements: IDs of prerequisite abilities
        parameters: Parameters for the ability
        metadata: Additional metadata
        
    Returns:
        Decorator function
    """
    def decorator(func):
        ability_registry.register_ability(
            name=name,
            description=description,
            scope=scope,
            level=level,
            tags=tags,
            requirements=requirements,
            parameters=parameters,
            implementation=func,
            metadata=metadata
        )
        return func
    return decorator