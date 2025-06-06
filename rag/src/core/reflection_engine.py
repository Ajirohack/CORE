"""
Reflection Engine for Superior RAG System.

This module analyzes retrieval results, identifies knowledge gaps,
and improves responses through recursive retrieval and reflection.
"""

import logging
import asyncio
import time
from typing import Dict, List, Any, Optional, Union, TypedDict, Tuple
from dataclasses import dataclass
import re
import json

from src.utils.config import load_config
from src.retrieval.retriever import get_retriever

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("superior_rag.core.reflection_engine")

# Load configuration
config = load_config()

@dataclass
class RetrievalResult:
    """Data class for retrieval results with reflection metadata."""
    
    # Original query and results
    query: str
    results: List[Dict[str, Any]]
    
    # Reflection data
    has_reflected: bool = False
    reflection_queries: List[str] = None
    reflection_results: List[List[Dict[str, Any]]] = None
    knowledge_gaps: List[str] = None
    
    # Analysis results
    has_sufficient_info: bool = False
    relevance_score: float = 0.0
    coverage_score: float = 0.0
    
    # Final processed context
    ranked_chunks: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        """Initialize optional lists."""
        if self.reflection_queries is None:
            self.reflection_queries = []
        if self.reflection_results is None:
            self.reflection_results = []
        if self.knowledge_gaps is None:
            self.knowledge_gaps = []
        if self.ranked_chunks is None:
            self.ranked_chunks = []


class ReflectionEngine:
    """
    Reflection Engine for analyzing retrieval results.
    
    This component:
    1. Analyzes initial retrieval results for relevance and coverage
    2. Identifies knowledge gaps or missing information
    3. Generates follow-up queries to fill these gaps
    4. Integrates new information into the final context
    """
    
    def __init__(self):
        """Initialize the reflection engine."""
        # Load configuration
        self.reflection_config = config.get("retrieval", {}).get("reflection", {})
        
        # Configuration parameters
        self.enabled = self.reflection_config.get("enabled", True)
        self.max_iterations = self.reflection_config.get("max_iterations", 2)
        self.min_relevance_threshold = self.reflection_config.get("min_relevance_threshold", 0.6)
        self.min_coverage_threshold = self.reflection_config.get("min_coverage_threshold", 0.7)
        self.max_gap_queries = self.reflection_config.get("max_gap_queries", 3)
        
        logger.info("Reflection engine initialized")
        
    async def reflect(
        self,
        query: str,
        initial_results: List[Dict[str, Any]]
    ) -> RetrievalResult:
        """
        Perform reflection on retrieval results.
        
        Args:
            query: Original user query
            initial_results: Initial retrieval results
            
        Returns:
            RetrievalResult: Results with reflection data and final context
        """
        # Create initial retrieval result object
        result = RetrievalResult(
            query=query,
            results=initial_results,
        )
        
        # Skip if reflection is disabled or no results
        if not self.enabled or not initial_results:
            # Still perform basic analysis
            result.has_sufficient_info = len(initial_results) > 0
            result.relevance_score = 0.7 if initial_results else 0.0
            result.coverage_score = 0.7 if initial_results else 0.0
            result.ranked_chunks = initial_results
            return result
            
        # Analyze initial results
        relevance, coverage, gaps = await self._analyze_results(query, initial_results)
        
        result.relevance_score = relevance
        result.coverage_score = coverage
        result.knowledge_gaps = gaps
        
        # Determine if we have sufficient information
        has_sufficient_info = (
            relevance >= self.min_relevance_threshold and 
            coverage >= self.min_coverage_threshold
        )
        
        # If we have sufficient information, skip reflection
        if has_sufficient_info:
            result.has_sufficient_info = True
            result.ranked_chunks = initial_results
            return result
            
        # Mark that we performed reflection
        result.has_reflected = True
        
        # Generate follow-up queries for identified gaps
        follow_up_queries = await self._generate_follow_up_queries(query, gaps)
        result.reflection_queries = follow_up_queries
        
        # Limit number of queries to avoid excessive computation
        if len(follow_up_queries) > self.max_gap_queries:
            follow_up_queries = follow_up_queries[:self.max_gap_queries]
            
        # Execute follow-up queries
        reflection_results = []
        
        # Get retriever instance
        retriever = get_retriever()
        
        # Execute each follow-up query
        for follow_up_query in follow_up_queries:
            # Execute query
            additional_results = await retriever.retrieve(
                query=follow_up_query,
                top_k=5,  # Smaller top_k for follow-up queries
                cache_key=f"reflection:{follow_up_query}"
            )
            
            reflection_results.append(additional_results)
            
        # Store reflection results
        result.reflection_results = reflection_results
        
        # Merge and rank all results
        all_chunks = await self._merge_and_rank_results(
            query,
            initial_results,
            reflection_results,
            follow_up_queries
        )
        
        # Update final result object
        result.ranked_chunks = all_chunks
        result.has_sufficient_info = True  # Assume we have sufficient info now
        
        return result
        
    async def _analyze_results(
        self,
        query: str,
        results: List[Dict[str, Any]]
    ) -> Tuple[float, float, List[str]]:
        """
        Analyze retrieval results for relevance, coverage, and knowledge gaps.
        
        Args:
            query: User query
            results: Retrieval results
            
        Returns:
            Tuple[float, float, List[str]]: Relevance score, coverage score, and knowledge gaps
        """
        # In a full implementation, we would use an LLM to analyze the results
        # against the query to determine relevance, coverage, and identify gaps
        
        # This is a simplified version that:
        # 1. Calculates a basic relevance score based on result counts and scores
        # 2. Estimates coverage based on unique terms
        # 3. Identifies potential knowledge gaps based on query analysis
        
        # Simple relevance calculation
        relevance = 0.0
        if results:
            # Calculate average score, assuming scores are between 0-1
            avg_score = sum(r.get("score", 0) for r in results) / len(results)
            
            # Adjust based on number of results
            count_factor = min(len(results) / 5, 1.0)  # Normalize to max 1.0
            
            relevance = avg_score * 0.7 + count_factor * 0.3
            
        # Basic coverage estimation using term overlap
        coverage = 0.0
        if results:
            # Extract query terms (simplified)
            query_terms = set(self._extract_key_terms(query))
            
            # Count terms in results
            result_terms = set()
            for r in results:
                content = r.get("content", "")
                result_terms.update(self._extract_key_terms(content))
                
            # Calculate overlap
            if query_terms:
                overlap = len(query_terms.intersection(result_terms)) / len(query_terms)
                coverage = overlap
                
            # Ensure coverage is at least proportional to result count
            min_coverage = min(len(results) / 10, 0.7)  # Max 0.7 from count alone
            coverage = max(coverage, min_coverage)
        
        # Identify potential knowledge gaps
        gaps = []
        
        # Low relevance or coverage indicates potential gaps
        if relevance < self.min_relevance_threshold or coverage < self.min_coverage_threshold:
            # Extract topics from query that might not be covered
            query_topics = self._extract_query_topics(query)
            
            # In a real implementation, we would analyze which topics are not covered
            # Here we'll just use them all as potential gaps
            gaps = query_topics
            
        return relevance, coverage, gaps
        
    def _extract_key_terms(self, text: str) -> List[str]:
        """
        Extract key terms from text for analysis.
        
        Args:
            text: Input text
            
        Returns:
            List[str]: Key terms
        """
        # This is a simplified extraction - in a real implementation,
        # we would use NLP techniques to extract meaningful terms
        
        # Convert to lowercase and split on non-alphanumeric chars
        words = re.findall(r'\w+', text.lower())
        
        # Remove common stop words (abbreviated list)
        stop_words = {
            'a', 'an', 'the', 'and', 'or', 'but', 'is', 'are', 'was', 'were',
            'be', 'been', 'being', 'to', 'of', 'for', 'with', 'by', 'about',
            'against', 'between', 'into', 'through', 'during', 'before', 'after',
            'above', 'below', 'from', 'up', 'down', 'in', 'out', 'on', 'off',
            'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there',
            'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few',
            'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only',
            'own', 'same', 'so', 'than', 'too', 'very', 'can', 'will', 'just',
            'should', 'now'
        }
        
        terms = [w for w in words if w not in stop_words and len(w) > 2]
        return terms
        
    def _extract_query_topics(self, query: str) -> List[str]:
        """
        Extract potential topics from a query.
        
        Args:
            query: User query
            
        Returns:
            List[str]: List of potential topics
        """
        # This is a simplified extraction - in a real implementation,
        # we would use NLP techniques to extract topics and entities
        
        # For demonstration, we'll extract noun phrases using simple patterns
        # This can be replaced with proper NLP in production
        
        topics = []
        
        # Basic pattern to match potential 1-3 word topics
        # This is a very simplified approach
        patterns = [
            r'(?:the\s+)?([A-Z][a-z]+(?:\s+[a-z]+){0,2})',  # Capitalized 1-3 words
            r'(?:the\s+)?([a-z]+\s+[a-z]+(?:\s+[a-z]+)?)'   # 2-3 lowercase words
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, query)
            topics.extend(matches)
            
        # Deduplicate
        topics = list(set(topics))
        
        # If no topics found with patterns, fall back to key terms
        if not topics:
            terms = self._extract_key_terms(query)
            topics = terms[:3]  # Limit to top 3 terms
            
        return topics
        
    async def _generate_follow_up_queries(
        self,
        original_query: str,
        gaps: List[str]
    ) -> List[str]:
        """
        Generate follow-up queries based on identified knowledge gaps.
        
        Args:
            original_query: Original user query
            gaps: Identified knowledge gaps
            
        Returns:
            List[str]: Follow-up queries
        """
        # In a full implementation, we would use an LLM to generate better follow-up queries
        # based on the original query and the identified gaps
        
        # For this simplified version, we'll create template-based follow-up queries
        follow_up_queries = []
        
        # If we have specific gaps, create targeted queries
        if gaps:
            # Create a query for each gap
            for gap in gaps:
                # Skip if gap is too short
                if len(gap) <= 3:
                    continue
                    
                # Create query variants
                queries = [
                    f"{original_query} regarding {gap}",
                    f"What is {gap} in context of {original_query}",
                    f"{gap} information related to {original_query}"
                ]
                
                # Add one of the variants
                follow_up_queries.append(queries[0])
        
        # If no gaps or we couldn't create queries, create general follow-ups
        if not follow_up_queries:
            follow_up_queries = [
                f"more details about {original_query}",
                f"additional information on {original_query}",
                f"extended explanation of {original_query}"
            ]
            
        # Deduplicate and limit
        unique_queries = list(dict.fromkeys(follow_up_queries))
        
        return unique_queries[:self.max_gap_queries]
        
    async def _merge_and_rank_results(
        self,
        original_query: str,
        initial_results: List[Dict[str, Any]],
        reflection_results: List[List[Dict[str, Any]]],
        reflection_queries: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Merge and rank results from initial query and reflection queries.
        
        Args:
            original_query: Original user query
            initial_results: Results from original query
            reflection_results: Results from reflection queries (list per query)
            reflection_queries: Reflection queries that generated results
            
        Returns:
            List[Dict[str, Any]]: Merged and ranked results
        """
        # Combine all results
        all_results = {}
        
        # Add initial results
        for result in initial_results:
            key = f"{result.get('document_id')}:{result.get('chunk_index')}"
            
            if key not in all_results:
                # Copy result and add source
                result_copy = result.copy()
                result_copy["source"] = "initial"
                result_copy["queries"] = [original_query]
                
                all_results[key] = result_copy
                
        # Add reflection results
        for i, (query_results, query) in enumerate(zip(reflection_results, reflection_queries)):
            for result in query_results:
                key = f"{result.get('document_id')}:{result.get('chunk_index')}"
                
                if key in all_results:
                    # Update existing result
                    all_results[key]["reflection_score"] = max(
                        all_results[key].get("reflection_score", 0),
                        result.get("score", 0)
                    )
                    all_results[key]["queries"].append(query)
                else:
                    # Add new result
                    result_copy = result.copy()
                    result_copy["source"] = f"reflection_{i+1}"
                    result_copy["reflection_score"] = result.get("score", 0)
                    result_copy["queries"] = [query]
                    
                    all_results[key] = result_copy
                    
        # Convert to list
        merged_results = list(all_results.values())
        
        # Calculate combined scores
        for result in merged_results:
            # Base score is the initial or reflection score
            base_score = result.get("score", 0)
            
            # If it's from reflection, use reflection score
            if result.get("source") != "initial":
                base_score = result.get("reflection_score", 0)
                
            # Bonus for results from multiple queries
            query_bonus = min(len(result.get("queries", [])) * 0.05, 0.15)
            
            # Bonus for initial results (prioritize them slightly)
            initial_bonus = 0.1 if result.get("source") == "initial" else 0
            
            # Calculate final score
            final_score = base_score + query_bonus + initial_bonus
            
            # Update result score
            result["final_score"] = final_score
            
        # Sort by final score
        merged_results.sort(key=lambda x: x.get("final_score", 0), reverse=True)
        
        # Clean up internal fields
        for result in merged_results:
            if "reflection_score" in result:
                del result["reflection_score"]
            if "queries" in result:
                del result["queries"]
            if "source" in result:
                del result["source"]
            if "final_score" in result:
                # Rename to score for consistency
                result["score"] = result["final_score"]
                del result["final_score"]
                
        return merged_results

# Singleton instance
_reflection_engine = None

def get_reflection_engine() -> ReflectionEngine:
    """Get or create the reflection engine singleton."""
    global _reflection_engine
    if _reflection_engine is None:
        _reflection_engine = ReflectionEngine()
    return _reflection_engine