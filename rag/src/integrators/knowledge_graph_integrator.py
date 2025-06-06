"""
Knowledge Graph Integrator Module
Connects the knowledge graph with the RAG system for enhanced retrieval
"""

import logging
from typing import Dict, List, Any, Optional, Union
import uuid

from core.rag_system.knowledge_graph.graph_builder import GraphBuilder
from core.rag_system.knowledge_graph.graph_retriever import GraphRetriever

logger = logging.getLogger(__name__)

class KnowledgeGraphIntegrator:
    """
    Integrates knowledge graph capabilities with the RAG system
    
    Features:
    - Entity-based document retrieval
    - Relationship-aware context augmentation
    - Knowledge graph exploration for structured reasoning
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the knowledge graph integrator
        
        Args:
            config: Configuration for the integrator
        """
        self.config = config or {}
        
        # Initialize knowledge graph components
        self.graph_builder = GraphBuilder(config=config)
        self.graph_retriever = GraphRetriever(config=config)
        
        # Configure integration
        self.use_entity_extraction = self.config.get("use_entity_extraction", True)
        self.use_relationships = self.config.get("use_relationships", True)
        self.max_graph_results = self.config.get("max_graph_results", 5)
        
        # Settings for result combination
        self.kg_weight = self.config.get("kg_weight", 0.3)  # Weight for KG results in final ranking
        
        logger.info("Knowledge graph integrator initialized")
    
    def process_documents_for_kg(self, documents: List[Dict[str, Any]]) -> None:
        """
        Process documents to extract entities and relationships for the knowledge graph
        
        Args:
            documents: List of document dictionaries with 'content' and 'metadata'
        """
        if not self.use_entity_extraction:
            return
            
        logger.info(f"Processing {len(documents)} documents for knowledge graph")
        
        for doc in documents:
            # Extract entities and relationships
            entities = self.graph_builder.entity_extractor.extract_entities(doc.get("content", ""))
            
            # Add document to graph
            if entities:
                self.graph_builder.add_document_with_entities(
                    doc_id=doc.get("id", str(uuid.uuid4())),
                    content=doc.get("content", ""),
                    metadata=doc.get("metadata", {}),
                    entities=entities
                )
    
    def enhance_retrieval(self, query: str, base_results: List[Dict[str, Any]], k: int = 10) -> List[Dict[str, Any]]:
        """
        Enhance retrieval results using knowledge graph
        
        Args:
            query: User query
            base_results: Base retrieval results from vector search
            k: Number of results to return
            
        Returns:
            Enhanced results incorporating knowledge graph information
        """
        # Skip if disabled
        if not self.use_entity_extraction:
            return base_results
            
        # Step 1: Extract entities from query
        query_entities = self.graph_builder.entity_extractor.extract_entities(query)
        
        if not query_entities:
            logger.debug("No entities found in query, returning base results")
            return base_results
        
        # Step 2: Retrieve related documents from knowledge graph
        logger.debug(f"Found entities in query: {', '.join(e['text'] for e in query_entities)}")
        
        graph_results = self.graph_retriever.retrieve_by_entities(
            query_entities, 
            limit=self.max_graph_results
        )
        
        if not graph_results:
            logger.debug("No knowledge graph results found")
            return base_results
        
        # Step 3: Merge results
        return self._merge_results(query, base_results, graph_results, k)
    
    def get_entity_context(self, query: str) -> Dict[str, Any]:
        """
        Get contextual information about entities in a query
        
        Args:
            query: User query
            
        Returns:
            Dictionary with entity information and relationships
        """
        # Extract entities
        query_entities = self.graph_builder.entity_extractor.extract_entities(query)
        
        if not query_entities:
            return {"entities": []}
            
        # Get entity information and relationships
        entity_info = {}
        
        for entity in query_entities:
            entity_id = entity.get("id")
            if not entity_id:
                continue
                
            # Get node information
            node = self.graph_builder.get_node(entity_id)
            if not node:
                continue
                
            # Get relationships
            if self.use_relationships:
                relationships = self.graph_builder.get_relationships(entity_id)
            else:
                relationships = []
                
            entity_info[entity["text"]] = {
                "type": entity.get("type"),
                "attributes": node.get("attributes", {}),
                "relationships": [
                    {
                        "type": rel["type"],
                        "target": self.graph_builder.get_node_label(rel["target"]),
                        "confidence": rel.get("confidence", 1.0)
                    }
                    for rel in relationships
                ]
            }
            
        return {
            "entities": [
                {
                    "name": name,
                    "info": info
                }
                for name, info in entity_info.items()
            ]
        }
    
    def _merge_results(
        self,
        query: str,
        base_results: List[Dict[str, Any]],
        graph_results: List[Dict[str, Any]],
        k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Merge vector search and knowledge graph results
        
        Args:
            query: Original query
            base_results: Results from vector search
            graph_results: Results from knowledge graph
            k: Number of results to return
            
        Returns:
            Merged and re-ranked results
        """
        # Create lookup dictionaries
        base_lookup = {r["id"]: (i, r) for i, r in enumerate(base_results)}
        graph_lookup = {r["id"]: (i, r) for i, r in enumerate(graph_results)}
        
        # Get all unique document IDs
        all_ids = set(base_lookup.keys()) | set(graph_lookup.keys())
        
        # Calculate combined scores
        scored_results = []
        for doc_id in all_ids:
            # Calculate base score (normalize by position)
            base_score = 0.0
            if doc_id in base_lookup:
                i, doc = base_lookup[doc_id]
                base_score = 1.0 - (i / len(base_results))
            
            # Calculate graph score
            graph_score = 0.0
            if doc_id in graph_lookup:
                i, doc = graph_lookup[doc_id]
                graph_score = 1.0 - (i / len(graph_results))
                
            # Combined score
            combined_score = (
                (1 - self.kg_weight) * base_score +
                self.kg_weight * graph_score
            )
            
            # Get the document
            if doc_id in base_lookup:
                doc = base_lookup[doc_id][1]
            else:
                doc = graph_lookup[doc_id][1]
                
            # Add scores to document
            result = doc.copy()
            result.update({
                "base_score": base_score,
                "graph_score": graph_score,
                "combined_score": combined_score,
                "source": "both" if doc_id in base_lookup and doc_id in graph_lookup else 
                         "base" if doc_id in base_lookup else "graph"
            })
            
            scored_results.append(result)
            
        # Sort by combined score
        scored_results.sort(key=lambda x: x["combined_score"], reverse=True)
        
        # Take top k
        return scored_results[:k]
