"""
RAG (Retrieval Augmented Generation) System
Core component for knowledge retrieval in the Space project
"""

import os
import logging
from typing import List, Dict, Any, Optional, Union
from pathlib import Path

# Core imports
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores.base import VectorStore

# Updated imports for LangChain 0.2+
from langchain_community.embeddings import OpenAIEmbeddings, HuggingFaceEmbeddings

# Local imports
from core.rag_system.document_processors.document_processor import DocumentProcessor
from core.rag_system.vector_store.vector_store import (
    BaseVectorStore, 
    VectorStoreType, 
    create_vector_store,
    VectorStoreFactory
)
# Import TokenManager
from core.rag_system.utils.token_management import TokenManager
from core.rag_system.utils.cache import cached_search
from core.rag_system.utils.distributed import DistributedDocumentProcessor

# Setup logging
logger = logging.getLogger(__name__)

class RAGSystem:
    """
    Retrieval Augmented Generation system for the Space project.
    Manages document processing, embedding, storage, and retrieval.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the RAG System with configuration
        
        Args:
            config: Configuration dictionary for the RAG System
        """
        self.config = config or {}
        self.verbose = self.config.get("verbose", False)
        
        # Check for vector store path
        if "vector_store" not in self.config:
            self.config["vector_store"] = {}
            
        if "persist_directory" not in self.config["vector_store"]:
            vector_db_path = os.getenv("RAG_VECTOR_STORE_PATH", os.path.join(os.path.dirname(os.path.abspath(__file__)), "vector_db"))
            self.config["vector_store"]["persist_directory"] = vector_db_path
            if self.verbose:
                logger.info(f"Setting vector store path to {vector_db_path}")
        
        # Initialize components
        self._initialize_components()
        
        logger.info("RAG System initialized successfully")
    
    def _initialize_components(self):
        """Initialize all RAG system components"""
        # Initialize embedding model
        self._initialize_embeddings()
        
        # Initialize vector store
        self._initialize_vector_store()
        
        # Initialize document processor
        self._initialize_document_processor()
        
    def _initialize_embeddings(self):
        """Initialize the embedding model"""
        embedding_config = self.config.get("embeddings", {})
        # Fix: Access embedding_type instead of type
        embedding_type = embedding_config.get("embedding_type", "huggingface")
        
        if self.verbose:
            logger.info(f"Initializing {embedding_type} embeddings")
        
        try:
            if embedding_type.lower() == "openai":
                self.embedding_model = OpenAIEmbeddings(
                    # Fix: Access embedding_model instead of model
                    model=embedding_config.get("embedding_model", "text-embedding-ada-002"),
                    openai_api_key=embedding_config.get("api_key") or os.environ.get("OPENAI_API_KEY")
                )
            elif embedding_type.lower() == "huggingface":
                self.embedding_model = HuggingFaceEmbeddings(
                    # Fix: Access embedding_model instead of model
                    model_name=embedding_config.get("embedding_model", "sentence-transformers/all-MiniLM-L6-v2")
                )
            else:
                logger.warning(f"Unknown embedding type: {embedding_type}. Falling back to OpenAI.")
                self.embedding_model = OpenAIEmbeddings()
                
            if self.verbose:
                logger.info(f"Embedding model initialized: {embedding_type}")
        except Exception as e:
            logger.error(f"Error initializing embeddings: {str(e)}")
            # Fallback to OpenAI embeddings
            logger.warning("Falling back to default OpenAI embeddings")
            self.embedding_model = OpenAIEmbeddings()
    
    def _initialize_vector_store(self):
        """Initialize the vector store"""
        vector_store_config = self.config.get("vector_store", {})
        # Fix: Access store_type instead of type
        vector_store_type = vector_store_config.get("store_type", "faiss")
        
        if self.verbose:
            logger.info(f"Initializing {vector_store_type} vector store")
        
        self.vector_store = VectorStoreFactory.create_vector_store(
            store_type=vector_store_type,
            embedding_model=self.embedding_model,
            config=vector_store_config
        )
        
        # Load existing store if persist_directory is provided
        persist_dir = vector_store_config.get("persist_directory")
        if persist_dir:
            self._load_existing_vector_store(persist_dir)
    
    def _initialize_document_processor(self):
        """Initialize the document processor"""
        processor_config = self.config.get("document_processor", {})
        
        if self.verbose:
            logger.info("Initializing document processor")
        
        self.document_processor = DocumentProcessor(config=processor_config)
    
    def _load_existing_vector_store(self, path: str):
        """Load an existing vector store from disk"""
        if not os.path.exists(path):
            logger.warning(f"Vector store path does not exist: {path}")
            return
        
        try:
            # Implementation depends on vector store type
            if hasattr(self.vector_store, "load") and callable(getattr(self.vector_store, "load")):
                self.vector_store.load(path)
                if self.verbose:
                    logger.info(f"Loaded vector store from {path}")
            
            # Additional check for FAISS index file
            index_file = os.path.join(path, "index.faiss")
            documents_file = os.path.join(path, "documents.pkl")
            
            if os.path.exists(index_file) and os.path.exists(documents_file):
                logger.info(f"Found FAISS index file at {index_file}")
                self.vector_store.load_faiss_from_path(index_file, documents_file)
                logger.info(f"Loaded FAISS index with documents from {path}")
        except Exception as e:
            logger.error(f"Error loading vector store from {path}: {str(e)}")
    
    def add_documents(self, documents: List[Document]) -> List[str]:
        """
        Add documents to the RAG system
        
        Args:
            documents: List of Document objects to add
            
        Returns:
            List of document IDs
        """
        if not documents:
            logger.warning("No documents provided to add")
            return []
        
        if self.verbose:
            logger.info(f"Adding {len(documents)} documents to RAG system")
        
        # Add to vector store
        try:
            doc_ids = self.vector_store.add_documents(documents)
            if self.verbose:
                logger.info(f"Added {len(doc_ids)} documents to vector store")
            return doc_ids
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {str(e)}")
            return []
    
    def process_and_add_file(self, file_path: Union[str, Path]) -> List[str]:
        """
        Process a file and add it to the RAG system
        
        Args:
            file_path: Path to the file to process and add
            
        Returns:
            List of document IDs
        """
        if self.verbose:
            logger.info(f"Processing and adding file: {file_path}")
        
        # Process the file
        documents = self.document_processor.process_file(file_path)
        
        if not documents:
            logger.warning(f"No documents created from file: {file_path}")
            return []
        
        # Add the processed documents
        return self.add_documents(documents)
    
    def process_and_add_directory(
        self, 
        directory_path: Union[str, Path],
        recursive: bool = True
    ) -> List[str]:
        """
        Process all files in a directory and add them to the RAG system
        
        Args:
            directory_path: Path to the directory to process
            recursive: Whether to process subdirectories
            
        Returns:
            List of document IDs
        """
        if self.verbose:
            logger.info(f"Processing and adding directory: {directory_path}")
        
        # Process the directory
        documents = self.document_processor.process_directory(
            directory_path, recursive=recursive)
        
        if not documents:
            logger.warning(f"No documents created from directory: {directory_path}")
            return []
        
        # Add the processed documents
        return self.add_documents(documents)
    
    def process_and_add_directory_distributed(
        self,
        directory_path: str,
        num_workers: int = None,
        batch_size: int = 100
    ):
        """
        Process and add documents using distributed processing.
        Args:
            directory_path: Directory containing documents
            num_workers: Number of worker processes
            batch_size: Batch size for vector store additions
        """
        if self.verbose:
            logger.info(f"Processing directory in distributed mode: {directory_path}")
        
        distributed_processor = DistributedDocumentProcessor(
            config=self.document_processor.config,
            num_workers=num_workers
        )
        all_docs = distributed_processor.process_directory(directory_path)
        print(f"Processed {len(all_docs)} documents")
        for i in range(0, len(all_docs), batch_size):
            batch = all_docs[i:i+batch_size]
            texts = [doc.page_content for doc in batch]
            embeddings = self.embedding_model.embed_documents(texts)
            for j, doc in enumerate(batch):
                doc.embeddings = embeddings[j]
            self.vector_store.add_documents(batch)
            print(f"Added batch {i//batch_size + 1} ({len(batch)} documents)")
    
    def process_and_add_text(
        self, 
        text: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Process text and add it to the RAG system
        
        Args:
            text: Text to process and add
            metadata: Optional metadata to include with the document
            
        Returns:
            List of document IDs
        """
        if self.verbose:
            logger.info(f"Processing and adding text ({len(text)} chars)")
        
        # Process the text
        documents = self.document_processor.process_text(text, metadata)
        
        if not documents:
            logger.warning("No documents created from text")
            return []
        
        # Add the processed documents
        return self.add_documents(documents)
    
    @cached_search(cache_size=200, ttl_seconds=1800)
    def search(
        self, 
        query: str, 
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
        include_metadata: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Search the RAG system for documents matching a query
        
        Args:
            query: Search query
            k: Number of results to return
            filter: Optional filter to apply to results
            include_metadata: Whether to include document metadata in results
            
        Returns:
            List of search results (documents with optional metadata)
        """
        if self.verbose:
            logger.info(f"Searching for: {query[:50]}...")
        
        try:
            # Perform the search
            documents = self.vector_store.similarity_search(query, k=k, filter=filter)
            
            # Format results
            results = []
            for doc in documents:
                result = {
                    "content": doc.page_content,
                }
                if include_metadata:
                    result["metadata"] = doc.metadata
                results.append(result)
            
            if self.verbose:
                logger.info(f"Found {len(results)} matching documents")
            
            return results
        except Exception as e:
            logger.error(f"Error searching vector store: {str(e)}")
            return []
    
    def delete_documents(self, doc_ids: List[str]) -> bool:
        """
        Delete documents from the RAG system
        
        Args:
            doc_ids: List of document IDs to delete
            
        Returns:
            Success status
        """
        if self.verbose:
            logger.info(f"Deleting {len(doc_ids)} documents")
        
        try:
            self.vector_store.delete(doc_ids)
            return True
        except Exception as e:
            logger.error(f"Error deleting documents: {str(e)}")
            return False
    
    def save(self, path: Optional[str] = None) -> bool:
        """
        Save the RAG system's vector store to disk
        
        Args:
            path: Path to save the vector store
            
        Returns:
            Success status
        """
        vector_store_config = self.config.get("vector_store", {})
        save_path = path or vector_store_config.get("path", "./data/vector_store")
        
        if self.verbose:
            logger.info(f"Saving vector store to {save_path}")
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            # Save the vector store
            self.vector_store.persist(save_path)
            return True
        except Exception as e:
            logger.error(f"Error saving vector store: {str(e)}")
            return False
    
    def get_context_for_query(
        self,
        query: str,
        max_tokens: int = None,
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get formatted context for a query that can be sent to an LLM
        
        Args:
            query: The query to get context for
            max_tokens: Maximum number of tokens to include in the context
            k: Number of documents to retrieve
            filter: Optional filter criteria for document retrieval
            
        Returns:
            Dictionary with context string and sources metadata
        """
        # Search for documents
        results = self.search(query, k=k, filter=filter)
        
        if not results:
            logger.warning(f"No results found for query: {query}")
            return {"context": "", "sources": []}
        
        # Get LLM provider and model from config to determine context window
        llm_config = self.config.get('llm', {})
        llm_provider = llm_config.get('provider', 'openai')
        
        # Determine the appropriate model name based on provider
        model_mapping = {
            'openai': os.environ.get("OPENAI_MODEL", "gpt-4"),
            'anthropic': os.environ.get("ANTHROPIC_MODEL", "claude-3-haiku"),
            'ollama': os.environ.get("OLLAMA_MODEL", "llama3"),
            'groq': os.environ.get("GROQ_MODEL", "llama3-70b-8192"),
            'openrouter': os.environ.get("OPENROUTER_MODEL", "openai/gpt-4"),
        }
        
        model_name = model_mapping.get(llm_provider, "gpt-4")
        
        # Initialize token manager for the selected model
        token_manager = TokenManager(model_name=model_name)
        
        # Get max tokens for context if not specified
        if max_tokens is None:
            # Use config value if available, otherwise 1/3 of model's context window
            max_tokens = llm_config.get('max_context_tokens',
                                       token_manager.model_max_tokens // 3)
        
        # Get system message for token counting purposes
        system_message = llm_config.get('system_message', 
                                      "You are a helpful assistant. Answer based only on the provided context.")
        
        # Fit documents to context window
        fitted_docs = token_manager.fit_documents_to_context(
            docs=results,
            system_message=system_message,
            question=query,
            max_context_window=token_manager.model_max_tokens,
            buffer_tokens=llm_config.get('response_buffer_tokens', 1000)
        )
        
        # Format context with sources
        context_data = token_manager.format_context_with_sources(fitted_docs)
        
        if self.verbose:
            logger.info(f"Generated context with {len(fitted_docs)} documents")
            if len(fitted_docs) < len(results):
                logger.info(f"{len(results) - len(fitted_docs)} documents were omitted due to token limits")
        
        return context_data
    
    def answer_question(
        self, 
        question: str, 
        llm_provider: str = None, 
        system_message: str = None, 
        temperature: float = 0.0
    ) -> dict:
        """
        Answer a question using the RAG system and an integrated LLM provider
        
        Args:
            question: The question to answer
            llm_provider: Optional provider name (uses config default if not specified)
            system_message: Optional system message for the LLM
            temperature: Temperature setting for LLM response generation
            
        Returns:
            Dictionary containing the answer, sources, and metadata
        """
        try:
            from core.rag_system.llm_integration import get_llm_provider
            
            # Get context for the question
            context_data = self.get_context_for_query(
                query=question, 
                max_tokens=self.config.get('context', {}).get('max_tokens', 3000),
                k=self.config.get('context', {}).get('num_sources', 5)
            )
            
            context = context_data["context"]
            sources = context_data["sources"]
            
            # If no provider specified, use the one from config
            if not llm_provider:
                llm_provider = self.config.get('llm', {}).get('provider', 'openai')
                
            # Default system message if none provided
            if not system_message:
                system_message = (
                    "You are a helpful AI assistant integrated with a RAG (Retrieval Augmented Generation) system. "
                    "Answer questions based on the provided context. "
                    "If the context doesn't contain the information needed, admit that you don't know."
                )
            
            # Get the LLM provider
            llm = get_llm_provider(llm_provider)
            
            # Generate answer with context
            answer = llm.generate_with_context(
                prompt=question,
                context=context,
                system_message=system_message,
                temperature=temperature
            )
            
            return {
                "question": question,
                "answer": answer,
                "sources": [source["source"] for source in sources],
                "source_details": sources,  # Include full source details
                "provider": llm_provider
            }
        except ImportError:
            logger.error("LLM integration module not available")
            return {
                "error": "LLM integration module not available",
                "question": question
            }
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return {
                "error": f"Failed to generate answer: {str(e)}",
                "question": question
            }