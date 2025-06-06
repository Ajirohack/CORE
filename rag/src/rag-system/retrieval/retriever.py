"""
Knowledge Retrieval System for the Space Project
Provides retrieval capabilities for the RAG system
"""

import logging
from typing import List, Dict, Any, Optional, Tuple, Union
from enum import Enum

# Langchain imports
from langchain.embeddings.base import Embeddings
from langchain.docstore.document import Document
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import DocumentCompressorPipeline
from langchain.retrievers.document_compressors import (
    EmbeddingsFilter,
    LLMChainFilter
)

# Local imports
from core.rag_system.vector_store.vector_store import (
    VectorStoreFactory,
    BaseVectorStore,
    VectorStoreType
)

# Setup logging
logger = logging.getLogger(__name__)

class RetrievalStrategy(Enum):
    """Supported retrieval strategies"""
    BASIC = "basic"                  # Basic similarity search
    FILTERED = "filtered"            # Similarity search + metadata filtering
    RERANKED = "reranked"            # Rerank results after retrieval 
    HYBRID = "hybrid"                # Combine dense and sparse retrieval
    CONTEXTUAL = "contextual"        # Apply contextual compression


class KnowledgeRetriever:
    """
    Knowledge retrieval system that integrates with vector stores
    and provides various retrieval strategies
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the knowledge retriever
        
        Args:
            config: Configuration for the retriever
        """
        self.config = config or {}
        self.vector_store = None
        self.embedding_model = None
        self.default_k = self.config.get("default_k", 4)
        self.default_strategy = RetrievalStrategy(
            self.config.get("default_strategy", "basic").lower()
        )
        logger.info("Knowledge retriever initialized")
    
    def initialize(
        self,
        embedding_model: Embeddings,
        vector_store_type: Union[str, VectorStoreType] = "faiss",
        vector_store_config: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Initialize the knowledge retriever with embedding model and vector store
        
        Args:
            embedding_model: Embedding model to use
            vector_store_type: Type of vector store to use
            vector_store_config: Configuration for the vector store
        """
        self.embedding_model = embedding_model
        self.vector_store = VectorStoreFactory.create_vector_store(
            store_type=vector_store_type,
            embedding_model=embedding_model,
            config=vector_store_config
        )
        logger.info(f"Knowledge retriever initialized with {vector_store_type} vector store")
    
    def set_vector_store(self, vector_store: BaseVectorStore) -> None:
        """
        Set an existing vector store for the retriever
        
        Args:
            vector_store: Vector store to use
        """
        self.vector_store = vector_store
        logger.info("Set existing vector store for knowledge retriever")
    
    def add_documents(self, documents: List[Document]) -> List[str]:
        """
        Add documents to the vector store
        
        Args:
            documents: Documents to add
            
        Returns:
            List of document IDs
        """
        if self.vector_store is None:
            raise ValueError("Vector store not initialized. Call initialize() first.")
        
        logger.info(f"Adding {len(documents)} documents to knowledge base")
        return self.vector_store.add_documents(documents)
    
    def retrieve(
        self,
        query: str,
        k: int = None,
        strategy: Union[str, RetrievalStrategy] = None,
        filter_criteria: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Retrieve documents based on a query
        
        Args:
            query: Query string
            k: Number of documents to retrieve
            strategy: Retrieval strategy to use
            filter_criteria: Filter criteria for metadata filtering
            
        Returns:
            List of retrieved documents
        """
        if self.vector_store is None:
            logger.error("Vector store not initialized. Call initialize() first.")
            return []
        
        k = k or self.default_k
        
        # Determine strategy
        if strategy is None:
            strategy = self.default_strategy
        elif isinstance(strategy, str):
            try:
                strategy = RetrievalStrategy(strategy.lower())
            except ValueError:
                logger.warning(f"Unknown strategy: {strategy}. Using default.")
                strategy = self.default_strategy
        
        logger.info(f"Retrieving documents for query using {strategy.value} strategy")
        
        # Apply different retrieval strategies
        if strategy == RetrievalStrategy.BASIC:
            return self._basic_retrieval(query, k, filter_criteria)
        elif strategy == RetrievalStrategy.FILTERED:
            return self._filtered_retrieval(query, k, filter_criteria)
        elif strategy == RetrievalStrategy.RERANKED:
            return self._reranked_retrieval(query, k, filter_criteria)
        elif strategy == RetrievalStrategy.HYBRID:
            return self._hybrid_retrieval(query, k, filter_criteria)
        elif strategy == RetrievalStrategy.CONTEXTUAL:
            return self._contextual_retrieval(query, k, filter_criteria)
        else:
            logger.warning(f"Unknown strategy: {strategy}. Using basic retrieval.")
            return self._basic_retrieval(query, k, filter_criteria)
    
    def _basic_retrieval(
        self,
        query: str,
        k: int,
        filter_criteria: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Basic similarity search retrieval
        
        Args:
            query: Query string
            k: Number of documents to retrieve
            filter_criteria: Filter criteria for metadata filtering
            
        Returns:
            Retrieved documents
        """
        return self.vector_store.similarity_search(query, k=k, filter=filter_criteria)
    
    def _filtered_retrieval(
        self,
        query: str,
        k: int,
        filter_criteria: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Filtered retrieval with metadata filtering
        
        Args:
            query: Query string
            k: Number of documents to retrieve
            filter_criteria: Filter criteria for metadata filtering
            
        Returns:
            Retrieved documents
        """
        # Ensure we have filter criteria
        if not filter_criteria:
            logger.warning("No filter criteria provided for filtered retrieval. Using basic retrieval.")
            return self._basic_retrieval(query, k)
        
        # Get more documents than needed, then apply filters
        raw_docs = self.vector_store.similarity_search(
            query,
            k=k*2,  # Get more to allow for filtering
            filter=filter_criteria
        )
        
        # Further refine results (in a real implementation, this would do more sophisticated filtering)
        # For now, just return the first k
        return raw_docs[:k]
    
    def _reranked_retrieval(
        self,
        query: str,
        k: int,
        filter_criteria: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Reranked retrieval that applies a second ranking pass
        
        Args:
            query: Query string
            k: Number of documents to retrieve
            filter_criteria: Filter criteria for metadata filtering
            
        Returns:
            Retrieved documents
        """
        # In a full implementation, this would use a reranker model
        # For now, it's a placeholder that just does basic retrieval
        
        logger.info("Reranking not fully implemented. Using basic retrieval.")
        raw_docs = self._basic_retrieval(query, k*2, filter_criteria)
        
        # Placeholder for reranking logic
        # In a real implementation, we would apply a reranker model here
        
        # Return the top k after reranking (currently just the first k)
        return raw_docs[:k]
    
    def _hybrid_retrieval(
        self,
        query: str,
        k: int,
        filter_criteria: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Hybrid retrieval combining dense and sparse methods
        
        Args:
            query: Query string
            k: Number of documents to retrieve
            filter_criteria: Filter criteria for metadata filtering
            
        Returns:
            Retrieved documents
        """
        # In a full implementation, this would combine dense and sparse retrieval
        # For now, it's a placeholder that just does basic retrieval
        
        logger.info("Hybrid retrieval not fully implemented. Using basic retrieval.")
        return self._basic_retrieval(query, k, filter_criteria)
    
    def _contextual_retrieval(
        self,
        query: str,
        k: int,
        filter_criteria: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Contextual compression retrieval
        
        Args:
            query: Query string
            k: Number of documents to retrieve
            filter_criteria: Filter criteria for metadata filtering
            
        Returns:
            Retrieved documents
        """
        # In a full implementation, this would use contextual compression
        # For now, it's a placeholder that just does basic retrieval
        
        logger.info("Contextual compression not fully implemented. Using basic retrieval.")
        
        # Get raw documents first
        raw_docs = self._basic_retrieval(query, k*2, filter_criteria)
        
        # In a real implementation, we would apply compression here
        # Using LLMChainFilter or similar to extract the most relevant parts
        
        # Return the compressed results (currently just the first k)
        return raw_docs[:k]


class RetrievalService:
    """
    High-level service for knowledge retrieval that integrates with document processing
    and provides a complete RAG pipeline
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the retrieval service
        
        Args:
            config: Configuration for the service
        """
        self.config = config or {}
        self.retriever = KnowledgeRetriever(self.config.get("retriever_config"))
        self.is_initialized = False
        logger.info("Retrieval service initialized")
    
    def initialize(
        self,
        embedding_model: Embeddings,
        vector_store_type: Union[str, VectorStoreType] = "faiss",
        vector_store_config: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Initialize the retrieval service
        
        Args:
            embedding_model: Embedding model to use
            vector_store_type: Type of vector store to use
            vector_store_config: Configuration for the vector store
        """
        self.retriever.initialize(
            embedding_model=embedding_model,
            vector_store_type=vector_store_type,
            vector_store_config=vector_store_config
        )
        self.is_initialized = True
        logger.info("Retrieval service fully initialized")
    
    def query(
        self,
        query: str,
        k: int = None,
        strategy: Union[str, RetrievalStrategy] = None,
        filter_criteria: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Document], Dict[str, Any]]:
        """
        Query the knowledge base
        
        Args:
            query: Query string
            k: Number of documents to retrieve
            strategy: Retrieval strategy to use
            filter_criteria: Filter criteria for metadata filtering
            
        Returns:
            Retrieved documents and metadata
        """
        if not self.is_initialized:
            raise ValueError("Retrieval service not initialized. Call initialize() first.")
        
        # Log query for analytics
        logger.info(f"Processing query: {query[:50]}...")
        
        # Retrieve documents
        start_time = __import__("time").time()
        documents = self.retriever.retrieve(query, k, strategy, filter_criteria)
        retrieval_time = __import__("time").time() - start_time
        
        # Prepare metadata
        metadata = {
            "document_count": len(documents),
            "retrieval_time": retrieval_time,
            "strategy": strategy.value if isinstance(strategy, RetrievalStrategy) else strategy
        }
        
        logger.info(f"Retrieved {len(documents)} documents in {retrieval_time:.3f} seconds")
        return documents, metadata