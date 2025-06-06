"""Retrieval manager for the RAG system."""

from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from utils.logging import logger
from utils.metrics import collector

class RetrievalManager:
    """Manages document retrieval and ranking in the RAG system."""
    
    def __init__(
        self,
        vector_store,
        reranker=None,
        top_k: int = 5,
        similarity_threshold: float = 0.7
    ):
        self.vector_store = vector_store
        self.reranker = reranker
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold
        self.logger = logger
        self.metrics = collector
    
    async def retrieve(
        self,
        query_vector: np.ndarray,
        filter_criteria: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve relevant documents based on vector similarity."""
        with self.metrics.measure_time("document_retrieval"):
            try:
                # Get initial candidates from vector store
                candidates = await self.vector_store.search(
                    query_vector,
                    k=self.top_k,
                    filter_criteria=filter_criteria
                )
                
                # Filter by similarity threshold
                filtered_candidates = [
                    (id, score, meta) for id, score, meta in candidates
                    if score >= self.similarity_threshold
                ]
                
                if not filtered_candidates:
                    self.logger.warning("No documents met similarity threshold")
                    return []
                
                # Rerank if reranker is available
                if self.reranker and filtered_candidates:
                    reranked = await self._rerank_candidates(
                        filtered_candidates,
                        context
                    )
                else:
                    reranked = [
                        {
                            "id": id,
                            "score": score,
                            "metadata": meta,
                            "rank": i
                        }
                        for i, (id, score, meta) in enumerate(filtered_candidates)
                    ]
                
                return reranked
                
            except Exception as e:
                self.logger.error(f"Error in document retrieval: {e}")
                return []
    
    async def _rerank_candidates(
        self,
        candidates: List[Tuple[str, float, Dict[str, Any]]],
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Rerank candidates using the reranker model."""
        with self.metrics.measure_time("candidate_reranking"):
            try:
                reranked_scores = await self.reranker.rerank(
                    candidates,
                    context=context
                )
                
                # Combine original and reranked scores
                results = []
                for i, (id, orig_score, meta) in enumerate(candidates):
                    results.append({
                        "id": id,
                        "score": reranked_scores[i],
                        "original_score": orig_score,
                        "metadata": meta,
                        "rank": i
                    })
                
                # Sort by reranked scores
                results.sort(key=lambda x: x["score"], reverse=True)
                
                return results
                
            except Exception as e:
                self.logger.error(f"Error in candidate reranking: {e}")
                # Fall back to original ranking
                return [
                    {
                        "id": id,
                        "score": score,
                        "metadata": meta,
                        "rank": i
                    }
                    for i, (id, score, meta) in enumerate(candidates)
                ]
    
    async def retrieve_with_feedback(
        self,
        query_vector: np.ndarray,
        feedback: Dict[str, Any],
        filter_criteria: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve documents with relevance feedback."""
        # Incorporate feedback into retrieval context
        context = {
            "feedback": feedback,
            "timestamp": feedback.get("timestamp")
        }
        
        # Perform retrieval with feedback context
        results = await self.retrieve(
            query_vector,
            filter_criteria=filter_criteria,
            context=context
        )
        
        return results