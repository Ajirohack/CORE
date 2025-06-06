"""
Document Processor for RAG System
Handles document loading, splitting, and processing
"""

import os
import logging
from typing import List, Dict, Any, Optional, Union, Tuple
import hashlib
from enum import Enum

# Langchain imports
from langchain.document_loaders import (
    TextLoader, PyPDFLoader, CSVLoader, 
    UnstructuredMarkdownLoader, UnstructuredHTMLLoader
)
from langchain.document_loaders.base import BaseLoader
from langchain.text_splitter import (
    RecursiveCharacterTextSplitter, 
    CharacterTextSplitter,
    TokenTextSplitter
)
from langchain.docstore.document import Document
from langchain.schema import BaseDocumentTransformer

# Setup logging
logger = logging.getLogger(__name__)

class DocumentType(Enum):
    """Supported document types"""
    TEXT = "text"
    PDF = "pdf"
    CSV = "csv"
    MARKDOWN = "markdown"
    HTML = "html"
    UNKNOWN = "unknown"


class SplitterType(Enum):
    """Supported text splitter types"""
    RECURSIVE = "recursive"
    CHARACTER = "character"
    TOKEN = "token"


class DocumentProcessor:
    """
    Processes documents for the RAG system, including loading,
    splitting, and optional transformations
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the document processor
        
        Args:
            config: Configuration for the document processor
        """
        self.config = config or {}
        self.default_chunk_size = self.config.get("chunk_size", 1000)
        self.default_chunk_overlap = self.config.get("chunk_overlap", 200)
        self.default_splitter_type = SplitterType(self.config.get("splitter_type", "recursive").lower())
        self.transformers = []
        logger.info("Document processor initialized")
    
    def add_transformer(self, transformer: BaseDocumentTransformer) -> None:
        """
        Add a document transformer to the processing pipeline
        
        Args:
            transformer: The transformer to add
        """
        self.transformers.append(transformer)
        logger.info(f"Added transformer: {transformer.__class__.__name__}")
    
    def process_file(
        self,
        file_path: str,
        document_type: Optional[Union[str, DocumentType]] = None,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        splitter_type: Optional[Union[str, SplitterType]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Process a file, including loading, splitting, and transformations
        
        Args:
            file_path: Path to the file to process
            document_type: Type of document (auto-detected if not specified)
            chunk_size: Size of chunks for splitting (default from config)
            chunk_overlap: Overlap between chunks (default from config)
            splitter_type: Type of splitter to use (default from config)
            metadata: Additional metadata to add to documents
            
        Returns:
            List of processed document chunks
        """
        logger.info(f"Processing file: {file_path}")
        
        # Detect document type if not specified
        if document_type is None:
            document_type = self._detect_document_type(file_path)
        elif isinstance(document_type, str):
            try:
                document_type = DocumentType(document_type.lower())
            except ValueError:
                logger.warning(f"Unknown document type: {document_type}. Auto-detecting.")
                document_type = self._detect_document_type(file_path)
        
        # Load the document
        documents = self._load_document(file_path, document_type)
        
        if not documents:
            logger.warning(f"No content loaded from file: {file_path}")
            return []
        
        # Add file metadata
        base_metadata = {
            "source": file_path,
            "file_type": document_type.value,
            "file_name": os.path.basename(file_path)
        }
        
        if metadata:
            base_metadata.update(metadata)
        
        for doc in documents:
            if doc.metadata:
                doc.metadata.update(base_metadata)
            else:
                doc.metadata = base_metadata
        
        # Split the document
        chunk_size = chunk_size or self.default_chunk_size
        chunk_overlap = chunk_overlap or self.default_chunk_overlap
        splitter_type = splitter_type or self.default_splitter_type
        
        if isinstance(splitter_type, str):
            try:
                splitter_type = SplitterType(splitter_type.lower())
            except ValueError:
                logger.warning(f"Unknown splitter type: {splitter_type}. Using default.")
                splitter_type = self.default_splitter_type
        
        chunked_documents = self._split_documents(
            documents, chunk_size, chunk_overlap, splitter_type
        )
        
        # Apply transformations
        processed_documents = self._apply_transformations(chunked_documents)
        
        # Generate IDs for documents
        for doc in processed_documents:
            doc.metadata["id"] = self._generate_document_id(doc)
        
        logger.info(f"Processed {len(processed_documents)} chunks from file: {file_path}")
        return processed_documents
    
    def process_text(
        self,
        text: str,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        splitter_type: Optional[Union[str, SplitterType]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Document]:
        """
        Process text directly, including splitting and transformations
        
        Args:
            text: Text to process
            chunk_size: Size of chunks for splitting (default from config)
            chunk_overlap: Overlap between chunks (default from config)
            splitter_type: Type of splitter to use (default from config)
            metadata: Additional metadata to add to documents
            
        Returns:
            List of processed document chunks
        """
        logger.info(f"Processing text of length: {len(text)}")
        
        # Create document
        documents = [Document(page_content=text, metadata=metadata or {})]
        
        # Split the document
        chunk_size = chunk_size or self.default_chunk_size
        chunk_overlap = chunk_overlap or self.default_chunk_overlap
        splitter_type = splitter_type or self.default_splitter_type
        
        if isinstance(splitter_type, str):
            try:
                splitter_type = SplitterType(splitter_type.lower())
            except ValueError:
                logger.warning(f"Unknown splitter type: {splitter_type}. Using default.")
                splitter_type = self.default_splitter_type
        
        chunked_documents = self._split_documents(
            documents, chunk_size, chunk_overlap, splitter_type
        )
        
        # Apply transformations
        processed_documents = self._apply_transformations(chunked_documents)
        
        # Generate IDs for documents
        for doc in processed_documents:
            doc.metadata["id"] = self._generate_document_id(doc)
        
        logger.info(f"Processed {len(processed_documents)} chunks from text")
        return processed_documents
    
    def _detect_document_type(self, file_path: str) -> DocumentType:
        """
        Detect the document type from the file extension
        
        Args:
            file_path: Path to the file
            
        Returns:
            Detected document type
        """
        _, ext = os.path.splitext(file_path.lower())
        
        if ext in ['.txt']:
            return DocumentType.TEXT
        elif ext in ['.pdf']:
            return DocumentType.PDF
        elif ext in ['.csv']:
            return DocumentType.CSV
        elif ext in ['.md', '.markdown']:
            return DocumentType.MARKDOWN
        elif ext in ['.html', '.htm']:
            return DocumentType.HTML
        else:
            logger.warning(f"Unknown file extension: {ext}. Treating as text.")
            return DocumentType.UNKNOWN
    
    def _load_document(
        self, 
        file_path: str, 
        document_type: DocumentType
    ) -> List[Document]:
        """
        Load a document using the appropriate loader
        
        Args:
            file_path: Path to the file
            document_type: Type of document
            
        Returns:
            List of loaded documents
        """
        loader = self._get_loader(file_path, document_type)
        
        try:
            documents = loader.load()
            logger.info(f"Loaded {len(documents)} documents from {file_path}")
            return documents
        except Exception as e:
            logger.error(f"Error loading document {file_path}: {str(e)}")
            return []
    
    def _get_loader(self, file_path: str, document_type: DocumentType) -> BaseLoader:
        """
        Get the appropriate document loader for the file type
        
        Args:
            file_path: Path to the file
            document_type: Type of document
            
        Returns:
            Document loader
        """
        if document_type == DocumentType.TEXT or document_type == DocumentType.UNKNOWN:
            return TextLoader(file_path)
        elif document_type == DocumentType.PDF:
            return PyPDFLoader(file_path)
        elif document_type == DocumentType.CSV:
            return CSVLoader(file_path)
        elif document_type == DocumentType.MARKDOWN:
            return UnstructuredMarkdownLoader(file_path)
        elif document_type == DocumentType.HTML:
            return UnstructuredHTMLLoader(file_path)
        else:
            logger.warning(f"No specific loader for {document_type.value}. Using TextLoader.")
            return TextLoader(file_path)
    
    def _split_documents(
        self,
        documents: List[Document],
        chunk_size: int,
        chunk_overlap: int,
        splitter_type: SplitterType
    ) -> List[Document]:
        """
        Split documents into chunks
        
        Args:
            documents: Documents to split
            chunk_size: Size of chunks
            chunk_overlap: Overlap between chunks
            splitter_type: Type of splitter to use
            
        Returns:
            List of document chunks
        """
        splitter = self._get_splitter(chunk_size, chunk_overlap, splitter_type)
        chunks = splitter.split_documents(documents)
        logger.info(f"Split documents into {len(chunks)} chunks")
        return chunks
    
    def _get_splitter(
        self,
        chunk_size: int,
        chunk_overlap: int,
        splitter_type: SplitterType
    ):
        """
        Get the appropriate text splitter
        
        Args:
            chunk_size: Size of chunks
            chunk_overlap: Overlap between chunks
            splitter_type: Type of splitter to use
            
        Returns:
            Text splitter
        """
        if splitter_type == SplitterType.RECURSIVE:
            return RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
        elif splitter_type == SplitterType.CHARACTER:
            return CharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
        elif splitter_type == SplitterType.TOKEN:
            return TokenTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
        else:
            logger.warning(f"Unknown splitter type: {splitter_type}. Using RecursiveCharacterTextSplitter.")
            return RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
    
    def _apply_transformations(self, documents: List[Document]) -> List[Document]:
        """
        Apply transformations to documents
        
        Args:
            documents: Documents to transform
            
        Returns:
            Transformed documents
        """
        transformed_docs = documents
        
        for transformer in self.transformers:
            try:
                transformed_docs = transformer.transform_documents(transformed_docs)
                logger.info(f"Applied transformer: {transformer.__class__.__name__}")
            except Exception as e:
                logger.error(f"Error applying transformer {transformer.__class__.__name__}: {str(e)}")
        
        return transformed_docs
    
    def _generate_document_id(self, document: Document) -> str:
        """
        Generate a unique ID for a document based on its content and metadata
        
        Args:
            document: Document to generate ID for
            
        Returns:
            Unique document ID
        """
        # Create a string combining content and key metadata
        content = document.page_content
        metadata_str = ""
        
        if document.metadata:
            # Include source in the ID if available
            if "source" in document.metadata:
                metadata_str += document.metadata["source"]
            
            # Include page number in the ID if available
            if "page" in document.metadata:
                metadata_str += f"_p{document.metadata['page']}"
        
        # Generate a hash of the combined string
        combined = f"{content}{metadata_str}"
        return hashlib.md5(combined.encode()).hexdigest()