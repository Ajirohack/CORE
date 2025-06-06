"""
Hybrid Retrieval Module for RAG System
Combines dense vector retrieval and sparse BM25 retrieval for improved results
"""

import logging
from typing import Dict, List, Any, Optional, Union
import numpy as np
from collections import defaultdict

# Internal imports
from core.rag_system.rag_system import RAGSystem
from core.rag_system.retrieval.sparse_retrieval import SparseRetriever

logger = logging.getLogger(__name__)

class HybridRetriever:
    """
    Hybrid retrieval combines dense vector search with sparse BM25 search
    for more comprehensive and accurate document retrieval
    
    This implementation uses Reciprocal Rank Fusion (RRF) to combine results
    from both retrieval methods.
    """
    
    def __init__(
        self,
        rag_system: RAGSystem = None,
        config: Dict[str, Any] = None,
        sparse_retriever: SparseRetriever = None
    ):
        """
        Initialize the hybrid retriever
        
        Args:
            rag_system: RAG system instance for dense retrieval
            config: Configuration for the retrievers
            sparse_retriever: Optional pre-configured sparse retriever
        """
        self.config = config or {}
        self.rag_system = rag_system
        
        # RRF constant (typical range 60-100)
        self.rrf_k = self.config.get("rrf_k", 60)
        
        # Weight for dense vs sparse results (higher means more weight to dense)
        self.dense_weight = self.config.get("dense_weight", 0.7)
        self.sparse_weight = 1.0 - self.dense_weight
        
        # Advanced features
        self.use_dynamic_weighting = self.config.get("use_dynamic_weighting", True)
        self.query_analysis_enabled = self.config.get("query_analysis_enabled", True)
        self.reranking_enabled = self.config.get("reranking_enabled", True)
        
        # Initialize sparse retriever if not provided
        if sparse_retriever is None:
            logger.info("Initializing sparse retriever")
            self.sparse_retriever = SparseRetriever(config=config)
        else:
            self.sparse_retriever = sparse_retriever
    
    def retrieve(self, query: str, k: int = 10, **kwargs) -> List[Dict[str, Any]]:
        """
        Perform hybrid retrieval combining dense and sparse results
        
        Args:
            query: The search query
            k: Number of results to return
            **kwargs: Additional arguments passed to retrievers
            
        Returns:
            Combined and re-ranked search results
        """
        logger.info(f"Performing hybrid retrieval for: {query[:50]}...")
        
        # Analyze query to determine optimal weights
        if self.use_dynamic_weighting and self.query_analysis_enabled:
            self._adjust_weights_for_query(query)
        
        # Get results from both retrievers
        dense_results = self.rag_system.search(query, k=k*2)
        sparse_results = self.sparse_retriever.search(query, k=k*2)
        
        # Combine results using RRF
        combined_results = self._combine_results(
            query, dense_results, sparse_results, k
        )
        
        # Apply advanced reranking if enabled
        if self.reranking_enabled and len(combined_results) > 1:
            combined_results = self._apply_reranking(query, combined_results)
        
        return combined_results[:k]
        
    def _adjust_weights_for_query(self, query: str) -> None:
        """
        Dynamically adjust weights based on query characteristics
        
        Args:
            query: The search query
        """
        query_lower = query.lower()
        
        # Adjust for specific query types
        if any(term in query_lower for term in ["who", "when", "where", "definition", "explain"]):
            # Fact-based queries benefit from higher dense retrieval weight
            self.dense_weight = min(0.85, self.dense_weight + 0.15)
            logger.debug(f"Adjusted weights for fact query: dense={self.dense_weight:.2f}")
        elif any(term in query_lower for term in ["how", "why", "compare", "difference", "example"]):
            # Conceptual queries benefit from balanced retrieval
            self.dense_weight = 0.65
            logger.debug(f"Adjusted weights for conceptual query: dense={self.dense_weight:.2f}")
        elif len(query.split()) > 10:
            # Longer, more detailed queries benefit from higher sparse weight
            self.dense_weight = max(0.55, self.dense_weight - 0.15)
            logger.debug(f"Adjusted weights for long query: dense={self.dense_weight:.2f}")
            
        # Update sparse weight to complement dense weight
        self.sparse_weight = 1.0 - self.dense_weight
    
    def _apply_reranking(self, query: str, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply advanced reranking to the combined results
        
        Args:
            query: Original query
            results: Combined results to rerank
            
        Returns:
            Reranked results
        """
        # For now, implement a simple diversity-based reranking
        # This helps avoid all results being too similar
        
        reranked = []
        remaining = results.copy()
        
        # Always include the top result
        reranked.append(remaining.pop(0))
        
        while remaining and len(reranked) < len(results):
            # Find the most diverse document compared to already selected
            most_diverse_idx = self._find_most_diverse(remaining, reranked)
            if most_diverse_idx < len(remaining):
                reranked.append(remaining.pop(most_diverse_idx))
            else:
                # Fallback to adding the next best result
                reranked.append(remaining.pop(0))
                
        return reranked
        
    def _find_most_diverse(self, candidates: List[Dict[str, Any]], selected: List[Dict[str, Any]]) -> int:
        """Find index of most diverse document in candidates compared to already selected docs"""
        if not candidates or not selected:
            return 0
            
        max_diversity = -1
        most_diverse_idx = 0
        
        for i, candidate in enumerate(candidates):
            # Simple diversity measure based on content difference
            min_similarity = float('inf')
            
            for selected_doc in selected:
                # Skip if comparing same document
                if candidate["id"] == selected_doc["id"]:
                    min_similarity = 0
                    break
                    
                # Compute simple text overlap similarity
                similarity = self._text_similarity(candidate["content"], selected_doc["content"])
                min_similarity = min(min_similarity, similarity)
                
            diversity = 1.0 - (0.0 if min_similarity == float('inf') else min_similarity)
            
            if diversity > max_diversity:
                max_diversity = diversity
                most_diverse_idx = i
                
        return most_diverse_idx
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """Simple text similarity based on word overlap"""
        if not text1 or not text2:
            return 0.0
            
        # Simple implementation using word overlap
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
            
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)

    def _combine_results(
        self,
        query: str,
        dense_results: List[Dict[str, Any]],
        sparse_results: List[Dict[str, Any]],
        k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Combine dense and sparse results using Reciprocal Rank Fusion
        
        Args:
            query: Original query
            dense_results: Results from dense retriever
            sparse_results: Results from sparse retriever
            k: Number of results to return
            
        Returns:
            Combined and re-ranked results
        """
        # Create dictionaries mapping document IDs to their ranks
        dense_ranks = {
            result["id"]: idx + 1
            for idx, result in enumerate(dense_results)
        }
        
        sparse_ranks = {
            result["id"]: idx + 1
            for idx, result in enumerate(sparse_results)
        }
        
        # Get all unique document IDs
        all_ids = set(dense_ranks.keys()) | set(sparse_ranks.keys())
        
        # Calculate RRF scores
        document_scores = {}
        for doc_id in all_ids:
            # RRF score = 1 / (rank + k)
            dense_score = 0
            if doc_id in dense_ranks:
                dense_score = 1.0 / (dense_ranks[doc_id] + self.rrf_k)
                
            sparse_score = 0
            if doc_id in sparse_ranks:
                sparse_score = 1.0 / (sparse_ranks[doc_id] + self.rrf_k)
            
            # Weighted combination
            document_scores[doc_id] = (
                self.dense_weight * dense_score + 
                self.sparse_weight * sparse_score
            )
        
        # Sort by score
        sorted_doc_ids = sorted(
            document_scores.keys(),
            key=lambda x: document_scores[x],
            reverse=True
        )
        
        # Create final result list
        combined_results = []
        doc_lookup = {r["id"]: r for r in dense_results + sparse_results}
        
        for doc_id in sorted_doc_ids[:k]:
            if doc_id in doc_lookup:
                doc = doc_lookup[doc_id].copy()
                # Add hybrid score to result
                doc["hybrid_score"] = document_scores[doc_id]
                combined_results.append(doc)
        
        return combined_results
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        """
        Add documents to both dense and sparse indexes
        
        Args:
            documents: List of document dictionaries with 'content' and 'metadata'
        """
        logger.info(f"Adding {len(documents)} documents to hybrid retriever")
        
        # Add to sparse index
        self.sparse_retriever.add_documents(documents)
        
        # Dense index should be updated through RAG system directly
