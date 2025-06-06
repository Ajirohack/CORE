"""
Knowledge Retriever for RAG System
Connects to vector stores and provides retrieval functions
"""

import logging
from typing import Dict, List, Any, Optional, Union
import json

# Internal imports
from core.rag_system.rag_system import RAGSystem

# Setup logging
logger = logging.getLogger(__name__)

class KnowledgeRetriever:
    """
    Knowledge retriever interface for the RAG system
    Provides simplified access to the RAG system for other components
    """
    
    def __init__(self, rag_system: RAGSystem = None, config: Dict[str, Any] = None):
        """
        Initialize the knowledge retriever
        
        Args:
            rag_system: RAG system instance to use (or create a new one if None)
            config: Configuration for the knowledge retriever and RAG system
        """
        self.config = config or {}
        
        # Use provided RAG system or create a new one
        if rag_system is not None:
            self.rag_system = rag_system
            logger.info("Using provided RAG system")
        else:
            logger.info("Creating new RAG system")
            self.rag_system = RAGSystem(config=config)
    
    def get_relevant_context(
        self, 
        query: str, 
        max_documents: int = 5,
        max_tokens: int = 4000
    ) -> str:
        """
        Get relevant context for a query
        
        Args:
            query: The query to get context for
            max_documents: Maximum number of documents to retrieve
            max_tokens: Maximum number of tokens in the returned context
            
        Returns:
            Context as a formatted string
        """
        logger.info(f"Getting relevant context for: {query[:50]}...")
        
        # Use the RAG system to get context
        context = self.rag_system.get_context_for_query(
            query=query,
            k=max_documents,
            max_tokens=max_tokens
        )
        
        return context
    
    def search_knowledge_base(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Search the knowledge base for a query
        
        Args:
            query: The search query
            k: Number of results to return
            
        Returns:
            List of search results
        """
        logger.info(f"Searching knowledge base for: {query[:50]}...")
        
        # Use the RAG system to search
        results = self.rag_system.search(query=query, k=k)
        
        return results
    
    def get_context_as_json(self, query: str, k: int = 5) -> str:
        """
        Get context as a JSON string for use in API responses
        
        Args:
            query: The query to get context for
            k: Number of documents to retrieve
            
        Returns:
            JSON string with context
        """
        # Get search results
        results = self.rag_system.search(query=query, k=k)
        
        # Format as JSON
        context_data = {
            "query": query,
            "results": results,
            "result_count": len(results)
        }
        
        return json.dumps(context_data, indent=2)
    
    def add_text_to_knowledge_base(
        self, 
        text: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Add text to the knowledge base
        
        Args:
            text: Text to add
            metadata: Optional metadata to associate with the text
            
        Returns:
            List of document IDs
        """
        logger.info(f"Adding text to knowledge base: {text[:50]}...")
        
        # Use the RAG system to add text
        doc_ids = self.rag_system.process_and_add_text(text, metadata)
        
        return doc_ids