"""
Graph Retriever Module for Knowledge Graph
Uses knowledge graph for enhanced document retrieval
"""

import logging
from typing import Dict, List, Any, Optional, Union
import uuid
from collections import defaultdict, Counter
import heapq

from core.rag_system.knowledge_graph.graph_builder import GraphBuilder
from core.rag_system.knowledge_graph.entity_extractor import EntityExtractor

logger = logging.getLogger(__name__)

class GraphRetriever:
    """
    Uses knowledge graph for enhanced document retrieval
    
    Features:
    - Graph-based search and retrieval
    - Entity-centric document retrieval
    - Path-based relevance scoring
    """
    
    def __init__(self, graph_builder: GraphBuilder = None, config: Dict[str, Any] = None):
        """
        Initialize the graph retriever
        
        Args:
            graph_builder: Knowledge graph builder
            config: Configuration for graph retriever
        """
        self.config = config or {}
        
        # Initialize graph builder if not provided
        if graph_builder is None:
            logger.info("Initializing new graph builder")
            self.graph_builder = GraphBuilder(config=config)
        else:
            self.graph_builder = graph_builder
        
        # Initialize entity extractor
        self.entity_extractor = EntityExtractor(config=config)
        
        logger.info("Graph retriever initialized")
    
    def retrieve(
        self,
        query: str,
        k: int = 5,
        max_path_depth: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Retrieve documents based on knowledge graph
        
        Args:
            query: Query string
            k: Number of results to return
            max_path_depth: Maximum path depth for graph exploration
            
        Returns:
            List of retrieved documents
        """
        logger.info(f"Graph retrieval for query: {query[:50]}...")
        
        # Extract entities from query
        query_entities = self.entity_extractor.extract_entities(query)
        
        # Find matching nodes in graph
        matching_nodes = []
        for entity in query_entities:
            entity_text = self.entity_extractor.normalize_entity(
                entity["text"],
                entity["type"]
            )
            
            # Find matching nodes
            nodes = self.graph_builder.find_nodes(
                entity_text,
                node_types=[entity["type"]]
            )
            matching_nodes.extend(nodes)
        
        # Extract document nodes connected to matching entities
        doc_scores = self._score_documents_by_graph_proximity(
            matching_nodes,
            max_path_depth
        )
        
        # Sort documents by score
        sorted_docs = sorted(
            doc_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Retrieve top-k documents
        result = []
        for doc_id, score in sorted_docs[:k]:
            doc_node = self.graph_builder.get_node(doc_id)
            if doc_node:
                # Get original document ID
                original_doc_id = doc_node.get("document_id")
                
                # Create result entry
                result_entry = {
                    "id": original_doc_id,
                    "score": score,
                    "document_node": doc_id
                }
                
                result.append(result_entry)
        
        return result
    
    def _score_documents_by_graph_proximity(
        self,
        seed_nodes: List[Dict[str, Any]],
        max_path_depth: int = 2
    ) -> Dict[str, float]:
        """
        Score documents by proximity to seed nodes in the graph
        
        Args:
            seed_nodes: List of seed nodes to start from
            max_path_depth: Maximum path depth for exploration
            
        Returns:
            Dictionary mapping document node IDs to scores
        """
        if not seed_nodes:
            return {}
        
        # Track scores for document nodes
        doc_scores = defaultdict(float)
        
        # Get document nodes directly connected to seed nodes
        for node in seed_nodes:
            node_id = node.get("id")
            
            # Explore graph from this node
            self._explore_graph_from_node(
                node_id, 
                doc_scores, 
                depth=0,
                max_depth=max_path_depth,
                visited=set(),
                base_score=1.0
            )
        
        return doc_scores
    
    def _explore_graph_from_node(
        self,
        node_id: str,
        doc_scores: Dict[str, float],
        depth: int,
        max_depth: int,
        visited: set,
        base_score: float
    ) -> None:
        """
        Recursively explore graph from a node to find connected documents
        
        Args:
            node_id: Current node ID
            doc_scores: Dictionary to update with document scores
            depth: Current exploration depth
            max_depth: Maximum exploration depth
            visited: Set of visited node IDs
            base_score: Base score for this path
        """
        # Stop if we've reached max depth or visited this node
        if depth > max_depth or node_id in visited:
            return
        
        # Mark node as visited
        visited.add(node_id)
        
        # Get current node
        node = self.graph_builder.get_node(node_id)
        if not node:
            return
        
        # If this is a document node, update score
        if node.get("type") == "document":
            doc_scores[node_id] += base_score / (depth + 1)
        
        # Get neighbors
        neighbors = self.graph_builder.get_neighbors(node_id)
        
        # Calculate score decay for next level
        next_score = base_score * (0.7 ** (depth + 1))
        
        # Continue exploration
        for neighbor in neighbors:
            if neighbor and neighbor.get("id") not in visited:
                self._explore_graph_from_node(
                    neighbor.get("id"),
                    doc_scores,
                    depth + 1,
                    max_depth,
                    visited.copy(),
                    next_score
                )
    
    def combine_with_vector_results(
        self,
        graph_results: List[Dict[str, Any]],
        vector_results: List[Dict[str, Any]],
        alpha: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Combine graph-based results with vector-based results
        
        Args:
            graph_results: Results from graph-based retrieval
            vector_results: Results from vector-based retrieval
            alpha: Weight for graph results (1-alpha for vector)
            
        Returns:
            Combined results
        """
        # Create lookup dictionaries
        graph_dict = {r["id"]: r for r in graph_results}
        vector_dict = {r["id"]: r for r in vector_results}
        
        # Get all document IDs
        all_ids = set(graph_dict.keys()) | set(vector_dict.keys())
        
        # Combine scores
        combined_scores = {}
        for doc_id in all_ids:
            graph_score = graph_dict[doc_id]["score"] if doc_id in graph_dict else 0
            vector_score = vector_dict[doc_id]["score"] if doc_id in vector_dict else 0
            
            # Normalize to [0,1] if needed
            
            # Weighted combination
            combined_scores[doc_id] = alpha * graph_score + (1 - alpha) * vector_score
        
        # Create combined results
        combined_results = []
        for doc_id, score in combined_scores.items():
            # Use vector result if available, otherwise graph result
            base_result = vector_dict.get(doc_id, graph_dict.get(doc_id, {})).copy()
            base_result["score"] = score
            base_result["combined"] = True
            
            combined_results.append(base_result)
        
        # Sort by combined score
        combined_results.sort(key=lambda x: x["score"], reverse=True)
        
        return combined_results
