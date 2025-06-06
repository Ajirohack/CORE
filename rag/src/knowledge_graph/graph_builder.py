"""
Graph Builder Module for Knowledge Graph
Constructs and manages a knowledge graph for enhanced retrieval
"""

import logging
from typing import Dict, List, Any, Optional, Union
import uuid
import json

from core.rag_system.knowledge_graph.entity_extractor import EntityExtractor

logger = logging.getLogger(__name__)

class GraphBuilder:
    """
    Builds and manages a knowledge graph
    
    Features:
    - Entity and relationship management
    - Graph storage and retrieval
    - Graph-based query capabilities
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the graph builder
        
        Args:
            config: Configuration for graph builder
        """
        self.config = config or {}
        
        # Initialize entity extractor
        self.entity_extractor = EntityExtractor(config=config)
        
        # Initialize graph storage
        self.nodes = {}  # id -> node
        self.edges = {}  # id -> edge
        self.node_indices = {}  # type -> {text -> [node_ids]}
        
        logger.info("Graph builder initialized")
    
    def process_document(
        self,
        document: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """
        Process a document and add entities to the graph
        
        Args:
            document: Document dictionary with content
            
        Returns:
            Dictionary with node and edge IDs added
        """
        doc_id = document.get("id", str(uuid.uuid4()))
        content = document.get("content", "")
        metadata = document.get("metadata", {})
        source = metadata.get("source", "unknown")
        
        logger.info(f"Processing document for knowledge graph: {doc_id}")
        
        # Extract entities and relationships
        entities = self.entity_extractor.extract_entities(content)
        relationships = self.entity_extractor.extract_relationships(content, entities)
        
        # Add document node
        doc_node = self.add_node({
            "type": "document",
            "text": f"Document: {doc_id}",
            "document_id": doc_id,
            "source": source
        })
        
        # Track added nodes and edges
        added_nodes = [doc_node]
        added_edges = []
        entity_nodes = {}  # Entity index -> node_id
        
        # Add entity nodes
        for i, entity in enumerate(entities):
            # Normalize entity
            normalized_text = self.entity_extractor.normalize_entity(
                entity["text"], 
                entity["type"]
            )
            
            # Add entity node
            entity_node = self.add_node({
                "type": entity["type"],
                "text": normalized_text,
                "original_text": entity["text"],
                "source_doc": doc_id
            })
            entity_nodes[i] = entity_node
            added_nodes.append(entity_node)
            
            # Connect to document
            contains_edge = self.add_edge({
                "source": doc_node,
                "target": entity_node,
                "type": "contains",
                "weight": 1.0
            })
            added_edges.append(contains_edge)
        
        # Add relationship edges
        for relationship in relationships:
            source_idx = relationship["source"]
            target_idx = relationship["target"]
            
            if source_idx in entity_nodes and target_idx in entity_nodes:
                source_node = entity_nodes[source_idx]
                target_node = entity_nodes[target_idx]
                
                # Add edge
                rel_edge = self.add_edge({
                    "source": source_node,
                    "target": target_node,
                    "type": relationship["type"],
                    "text": relationship["text"],
                    "source_doc": doc_id,
                    "weight": 1.0
                })
                added_edges.append(rel_edge)
        
        return {
            "nodes": added_nodes,
            "edges": added_edges
        }
    
    def add_node(self, attributes: Dict[str, Any]) -> str:
        """
        Add a node to the graph
        
        Args:
            attributes: Node attributes
            
        Returns:
            Node ID
        """
        # Generate ID if not provided
        node_id = attributes.get("id", str(uuid.uuid4()))
        node_type = attributes.get("type", "unknown")
        node_text = attributes.get("text", "")
        
        # Create node with attributes
        node = attributes.copy()
        node["id"] = node_id
        
        # Store node
        self.nodes[node_id] = node
        
        # Update indices
        if node_type not in self.node_indices:
            self.node_indices[node_type] = {}
            
        if node_text:
            if node_text not in self.node_indices[node_type]:
                self.node_indices[node_type][node_text] = []
            self.node_indices[node_type][node_text].append(node_id)
        
        return node_id
    
    def add_edge(self, attributes: Dict[str, Any]) -> str:
        """
        Add an edge to the graph
        
        Args:
            attributes: Edge attributes
            
        Returns:
            Edge ID
        """
        # Generate ID if not provided
        edge_id = attributes.get("id", str(uuid.uuid4()))
        
        # Create edge with attributes
        edge = attributes.copy()
        edge["id"] = edge_id
        
        # Store edge
        self.edges[edge_id] = edge
        
        return edge_id
    
    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a node by ID
        
        Args:
            node_id: Node ID
            
        Returns:
            Node dictionary or None
        """
        return self.nodes.get(node_id)
    
    def get_edge(self, edge_id: str) -> Optional[Dict[str, Any]]:
        """
        Get an edge by ID
        
        Args:
            edge_id: Edge ID
            
        Returns:
            Edge dictionary or None
        """
        return self.edges.get(edge_id)
    
    def get_nodes_by_type(self, node_type: str) -> List[Dict[str, Any]]:
        """
        Get all nodes of a specific type
        
        Args:
            node_type: Node type
            
        Returns:
            List of node dictionaries
        """
        result = []
        
        if node_type in self.node_indices:
            for node_list in self.node_indices[node_type].values():
                for node_id in node_list:
                    result.append(self.nodes[node_id])
        
        return result
    
    def find_nodes(
        self,
        query: str,
        node_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Find nodes matching a query
        
        Args:
            query: Query string
            node_types: Optional list of node types to search
            
        Returns:
            List of matching nodes
        """
        result = []
        types_to_search = node_types or list(self.node_indices.keys())
        
        query_lower = query.lower()
        
        for node_type in types_to_search:
            if node_type in self.node_indices:
                for node_text, node_ids in self.node_indices[node_type].items():
                    if query_lower in node_text.lower():
                        for node_id in node_ids:
                            result.append(self.nodes[node_id])
        
        return result
    
    def get_neighbors(
        self,
        node_id: str,
        edge_types: Optional[List[str]] = None,
        direction: str = "both"
    ) -> List[Dict[str, Any]]:
        """
        Get neighbors of a node
        
        Args:
            node_id: Node ID
            edge_types: Optional list of edge types to filter
            direction: Direction of edges (both, outgoing, incoming)
            
        Returns:
            List of neighbor nodes
        """
        result = []
        
        for edge_id, edge in self.edges.items():
            source_id = edge.get("source")
            target_id = edge.get("target")
            edge_type = edge.get("type")
            
            # Filter by edge type if specified
            if edge_types and edge_type not in edge_types:
                continue
            
            # Check direction
            is_match = False
            if direction in ["both", "outgoing"] and source_id == node_id:
                result.append(self.nodes.get(target_id))
                is_match = True
                
            if direction in ["both", "incoming"] and target_id == node_id:
                result.append(self.nodes.get(source_id))
                is_match = True
        
        return result
    
    def save_graph(self, filepath: str) -> None:
        """
        Save the graph to a file
        
        Args:
            filepath: Path to save the graph to
        """
        graph_data = {
            "nodes": self.nodes,
            "edges": self.edges,
        }
        
        with open(filepath, "w") as f:
            json.dump(graph_data, f, indent=2)
            
        logger.info(f"Saved knowledge graph to {filepath}")
    
    def load_graph(self, filepath: str) -> None:
        """
        Load the graph from a file
        
        Args:
            filepath: Path to load the graph from
        """
        with open(filepath, "r") as f:
            graph_data = json.load(f)
            
        self.nodes = graph_data.get("nodes", {})
        self.edges = graph_data.get("edges", {})
        
        # Rebuild indices
        self.node_indices = {}
        for node_id, node in self.nodes.items():
            node_type = node.get("type", "unknown")
            node_text = node.get("text", "")
            
            if node_type not in self.node_indices:
                self.node_indices[node_type] = {}
                
            if node_text:
                if node_text not in self.node_indices[node_type]:
                    self.node_indices[node_type][node_text] = []
                self.node_indices[node_type][node_text].append(node_id)
        
        logger.info(f"Loaded knowledge graph from {filepath}")
