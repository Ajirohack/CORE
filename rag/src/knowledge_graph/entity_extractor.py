"""
Entity Extractor Module for Knowledge Graph
Extracts entities and relationships from text for knowledge graph
"""

import logging
from typing import Dict, List, Any, Optional, Union
import re

logger = logging.getLogger(__name__)

class EntityExtractor:
    """
    Extracts entities and relationships from text
    
    Features:
    - Named entity recognition
    - Relationship extraction
    - Entity normalization
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the entity extractor
        
        Args:
            config: Configuration for entity extraction
        """
        self.config = config or {}
        
        # Configure entity extraction
        self.min_entity_length = self.config.get("min_entity_length", 3)
        self.max_entity_length = self.config.get("max_entity_length", 50)
        
        # Simple entity patterns
        self.entity_patterns = {
            "person": r"(?:[A-Z][a-z]+ ){1,2}[A-Z][a-z]+",  # Simple person names
            "organization": r"(?:[A-Z][a-zA-Z0-9]*[&.]? ?)+(?:Inc\.?|Corp\.?|LLC|Ltd\.?)?",
            "location": r"(?:[A-Z][a-z]+ ){0,2}(?:Street|Avenue|Boulevard|Road|Place|Plaza|Park|Bridge|River|Mountain|Ocean|Sea|Lake|City|County|State|Country|Island)",
            "date": r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}",
            "number": r"\$\d+(?:\.\d+)?|\d+(?:\.\d+)?%|\d{3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?"
        }
        
        logger.info("Entity extractor initialized")
    
    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract entities from text
        
        Args:
            text: Text to extract entities from
            
        Returns:
            List of extracted entities
        """
        logger.debug(f"Extracting entities from text: {text[:100]}...")
        
        entities = []
        
        # Apply each entity pattern
        for entity_type, pattern in self.entity_patterns.items():
            matches = re.finditer(pattern, text)
            
            for match in matches:
                entity_text = match.group(0)
                
                # Filter by length constraints
                if self.min_entity_length <= len(entity_text) <= self.max_entity_length:
                    entity = {
                        "text": entity_text,
                        "type": entity_type,
                        "start": match.start(),
                        "end": match.end()
                    }
                    entities.append(entity)
        
        # Sort by position in text
        entities.sort(key=lambda x: x["start"])
        
        return entities
    
    def extract_relationships(
        self,
        text: str,
        entities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Extract relationships between entities
        
        Args:
            text: Source text
            entities: Previously extracted entities
            
        Returns:
            List of relationships
        """
        logger.debug(f"Extracting relationships from text with {len(entities)} entities")
        
        if len(entities) < 2:
            return []
        
        # Simple relationship patterns
        relationship_patterns = [
            (r"(\w+) (?:is|was|are|were) (?:a|an|the) (\w+) of", "part_of"),
            (r"(\w+) (?:belongs|belonged) to (\w+)", "belongs_to"),
            (r"(\w+) (?:works|worked) (?:with|for) (\w+)", "works_for"),
            (r"(\w+) (?:located|situated) in (\w+)", "located_in"),
            (r"(\w+) (?:created|developed|invented|built) (\w+)", "created"),
            (r"(\w+) (?:uses|used|utilizes|utilized) (\w+)", "uses")
        ]
        
        # Extract entity indices for faster lookup
        entity_indices = {}
        for i, entity in enumerate(entities):
            entity_text = entity["text"].lower()
            if entity_text not in entity_indices:
                entity_indices[entity_text] = []
            entity_indices[entity_text].append(i)
        
        relationships = []
        
        # Find relationships using patterns
        for pattern, rel_type in relationship_patterns:
            matches = re.finditer(pattern, text.lower())
            
            for match in matches:
                source_text = match.group(1).lower()
                target_text = match.group(2).lower()
                
                # Find matching entities
                source_entities = [
                    i for i in entity_indices.get(source_text, [])
                    if entities[i]["text"].lower() == source_text
                ]
                
                target_entities = [
                    i for i in entity_indices.get(target_text, [])
                    if entities[i]["text"].lower() == target_text
                ]
                
                # Create relationship for each pair
                for source_idx in source_entities:
                    for target_idx in target_entities:
                        if source_idx != target_idx:
                            relationship = {
                                "source": source_idx,
                                "target": target_idx,
                                "type": rel_type,
                                "text": match.group(0)
                            }
                            relationships.append(relationship)
        
        return relationships
    
    def normalize_entity(self, entity: str, entity_type: str) -> str:
        """
        Normalize entity text for consistency
        
        Args:
            entity: Entity text
            entity_type: Entity type
            
        Returns:
            Normalized entity text
        """
        if entity_type == "person":
            # Normalize person names (remove titles, etc.)
            return re.sub(r"^(?:Mr\.|Mrs\.|Ms\.|Dr\.|Prof\.) ", "", entity)
            
        elif entity_type == "organization":
            # Normalize organization names
            return re.sub(r"(?:Inc\.?|Corp\.?|LLC|Ltd\.?)$", "", entity).strip()
            
        elif entity_type == "date":
            # Attempt to normalize dates (simplified)
            try:
                # Very simple date normalization, would use dateutil in production
                if re.match(r"\d{1,2}[/-]\d{1,2}[/-]\d{4}", entity):
                    parts = re.split(r"[/-]", entity)
                    return f"{parts[2]}-{parts[0].zfill(2)}-{parts[1].zfill(2)}"
            except:
                pass
            
        # Default: return unchanged
        return entity
