"""
Document Processor Module for RAG System
Handles document loading, parsing, chunking and preparation for embedding
"""

import os
import re
import logging
from typing import List, Dict, Any, Optional, Union, Iterator, Callable
from pathlib import Path
from enum import Enum

# LangChain imports
from langchain.schema import Document
from langchain.text_splitter import (
    RecursiveCharacterTextSplitter,
    CharacterTextSplitter,
    TokenTextSplitter
)

# Updated imports for LangChain 0.2+
from langchain_community.document_loaders import (
    TextLoader,
    PDFMinerLoader,
    PyPDFLoader,
    Docx2txtLoader,
    CSVLoader,
    UnstructuredHTMLLoader,
    UnstructuredMarkdownLoader
)
from langchain_community.document_transformers import Html2TextTransformer

# Setup logging
logger = logging.getLogger(__name__)

class TextSplitterType(Enum):
    """Supported text splitter types"""
    RECURSIVE = "recursive"
    CHARACTER = "character"
    TOKEN = "token"
    
class DocumentType(Enum):
    """Supported document types"""
    TEXT = "text"
    PDF = "pdf"
    DOCX = "docx"
    CSV = "csv"
    HTML = "html" 
    MARKDOWN = "md"
    UNKNOWN = "unknown"

class DocumentProcessor:
    """
    Process documents for use in the RAG system.
    Handles loading, parsing, chunking and metadata extraction.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the document processor with configuration.
        
        Args:
            config: Configuration dictionary with processing parameters
        """
        self.config = config or {}
        
        # Configure chunk settings with defaults
        self.chunk_size = self.config.get("chunk_size", 1000)
        self.chunk_overlap = self.config.get("chunk_overlap", 200)
        self.splitter_type = self.config.get("splitter_type", TextSplitterType.RECURSIVE)
        
        # Initialize transformers if needed
        self.transformers = {}
        if self.config.get("use_html_transformer", True):
            self.transformers["html"] = Html2TextTransformer()
        
        logger.info(f"Document processor initialized with chunk size {self.chunk_size}, "
                   f"overlap {self.chunk_overlap}, splitter {self.splitter_type}")
    
    def process_file(self, file_path: Union[str, Path]) -> List[Document]:
        """
        Process a file into chunked documents ready for embedding.
        
        Args:
            file_path: Path to the file to process
            
        Returns:
            List of processed document chunks
        """
        file_path = Path(file_path)
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return []
        
        # Determine document type from extension
        doc_type = self._get_document_type(file_path)
        
        # Load the document
        try:
            documents = self._load_document(file_path, doc_type)
            logger.info(f"Loaded {len(documents)} documents from {file_path}")
        except Exception as e:
            logger.error(f"Error loading document {file_path}: {str(e)}")
            return []
        
        # Apply transformations if needed
        documents = self._apply_transformations(documents, doc_type)
        
        # Process metadata
        documents = self._process_metadata(documents, file_path)
        
        # Split into chunks
        chunked_docs = self._split_documents(documents)
        logger.info(f"Split into {len(chunked_docs)} chunks")
        
        return chunked_docs
    
    def process_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Document]:
        """
        Process raw text into chunked documents ready for embedding.
        
        Args:
            text: Raw text to process
            metadata: Optional metadata to include with the documents
            
        Returns:
            List of processed document chunks
        """
        metadata = metadata or {}
        
        # Create document
        document = Document(page_content=text, metadata=metadata)
        
        # Split into chunks
        chunked_docs = self._split_documents([document])
        logger.info(f"Split text ({len(text)} chars) into {len(chunked_docs)} chunks")
        
        return chunked_docs
    
    def process_directory(
        self, 
        directory_path: Union[str, Path],
        recursive: bool = True,
        file_filter: Optional[Callable[[Path], bool]] = None
    ) -> List[Document]:
        """
        Process all documents in a directory.
        
        Args:
            directory_path: Path to the directory to process
            recursive: Whether to process subdirectories
            file_filter: Optional filter function to select files
            
        Returns:
            List of processed document chunks
        """
        directory_path = Path(directory_path)
        if not directory_path.exists() or not directory_path.is_dir():
            logger.error(f"Directory not found: {directory_path}")
            return []
        
        all_documents = []
        
        # Build file list
        files = []
        if recursive:
            for path in directory_path.rglob("*"):
                if path.is_file() and (file_filter is None or file_filter(path)):
                    files.append(path)
        else:
            for path in directory_path.glob("*"):
                if path.is_file() and (file_filter is None or file_filter(path)):
                    files.append(path)
        
        logger.info(f"Found {len(files)} files to process in {directory_path}")
        
        # Process each file
        for file_path in files:
            try:
                documents = self.process_file(file_path)
                all_documents.extend(documents)
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {str(e)}")
                continue
        
        logger.info(f"Processed {len(files)} files into {len(all_documents)} chunks")
        return all_documents
    
    def process_directory_in_batches(
        self, 
        directory_path: str, 
        batch_size: int = 10,
        callback: Optional[callable] = None
    ) -> Iterator[List]:
        """
        Process files in a directory in batches to manage memory usage
        
        Args:
            directory_path: Path to directory
            batch_size: Number of files to process per batch
            callback: Optional callback function to handle processed batches
            
        Returns:
            Iterator of document batches
        """
        all_files = []
        for root, _, files in os.walk(directory_path):
            for file in files:
                all_files.append(os.path.join(root, file))
        logger.info(f"Found {len(all_files)} files to process")
        batch_count = 0
        current_batch = []
        for i, file_path in enumerate(all_files):
            try:
                documents = self.process_file(file_path)
                current_batch.extend(documents)
                if len(current_batch) >= batch_size or i == len(all_files) - 1:
                    batch_count += 1
                    logger.info(f"Completed batch {batch_count} with {len(current_batch)} documents")
                    if callback:
                        callback(current_batch)
                    yield current_batch
                    current_batch = []
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {str(e)}")
                continue
        
        # Process any remaining documents in the final batch
        if current_batch:
            batch_count += 1
            logger.info(f"Completed final batch {batch_count} with {len(current_batch)} documents")
            if callback:
                callback(current_batch)
            yield current_batch
    
    def _get_document_type(self, file_path: Path) -> DocumentType:
        """Determine document type from file extension"""
        extension = file_path.suffix.lower()
        
        if extension == ".txt":
            return DocumentType.TEXT
        elif extension == ".pdf":
            return DocumentType.PDF
        elif extension == ".docx":
            return DocumentType.DOCX
        elif extension == ".csv":
            return DocumentType.CSV
        elif extension in [".html", ".htm"]:
            return DocumentType.HTML
        elif extension in [".md", ".markdown"]:
            return DocumentType.MARKDOWN
        else:
            logger.warning(f"Unknown file type: {extension}")
            return DocumentType.UNKNOWN
    
    def _load_document(self, file_path: Path, doc_type: DocumentType) -> List[Document]:
        """Load document based on its type"""
        try:
            if doc_type == DocumentType.TEXT:
                loader = TextLoader(str(file_path))
            elif doc_type == DocumentType.PDF:
                # Use the preferred PDF loader
                if self.config.get("use_pyminer_pdf", True):
                    loader = PDFMinerLoader(str(file_path))
                else:
                    loader = PyPDFLoader(str(file_path))
            elif doc_type == DocumentType.DOCX:
                loader = Docx2txtLoader(str(file_path))
            elif doc_type == DocumentType.CSV:
                loader = CSVLoader(str(file_path))
            elif doc_type == DocumentType.HTML:
                loader = UnstructuredHTMLLoader(str(file_path))
            elif doc_type == DocumentType.MARKDOWN:
                loader = UnstructuredMarkdownLoader(str(file_path))
            else:
                # Default to text loader for unknown types
                logger.warning(f"Using default text loader for unknown type: {file_path}")
                loader = TextLoader(str(file_path))
            
            return loader.load()
        except Exception as e:
            logger.error(f"Error loading document {file_path}: {str(e)}")
            raise
    
    def _apply_transformations(self, documents: List[Document], doc_type: DocumentType) -> List[Document]:
        """Apply any transformations to the documents"""
        if doc_type == DocumentType.HTML and "html" in self.transformers:
            try:
                logger.info("Applying HTML transformation")
                transformer = self.transformers["html"]
                documents = transformer.transform_documents(documents)
            except Exception as e:
                logger.error(f"Error applying HTML transformation: {str(e)}")
        
        return documents
    
    def _process_metadata(self, documents: List[Document], file_path: Path) -> List[Document]:
        """Process and enhance document metadata"""
        for doc in documents:
            # Ensure we have a metadata dict
            if doc.metadata is None:
                doc.metadata = {}
            
            # Add basic file metadata if not present
            if "source" not in doc.metadata:
                doc.metadata["source"] = str(file_path)
            if "filename" not in doc.metadata:
                doc.metadata["filename"] = file_path.name
            if "filetype" not in doc.metadata:
                doc.metadata["filetype"] = file_path.suffix.lower().lstrip(".")
            if "file_path" not in doc.metadata:
                doc.metadata["file_path"] = str(file_path)
            
            # Add timestamp if requested
            if self.config.get("include_timestamp", True):
                if "creation_date" not in doc.metadata:
                    try:
                        doc.metadata["creation_date"] = os.path.getctime(file_path)
                    except:
                        pass
                if "modified_date" not in doc.metadata:
                    try:
                        doc.metadata["modified_date"] = os.path.getmtime(file_path)
                    except:
                        pass
        
        return documents
    
    def _split_documents(self, documents: List[Document]) -> List[Document]:
        """Split documents into chunks using the configured splitter"""
        # Create text splitter based on configuration
        if isinstance(self.splitter_type, str):
            try:
                self.splitter_type = TextSplitterType(self.splitter_type.lower())
            except ValueError:
                logger.warning(f"Unknown splitter type: {self.splitter_type}. Falling back to RECURSIVE.")
                self.splitter_type = TextSplitterType.RECURSIVE
        
        if self.splitter_type == TextSplitterType.RECURSIVE:
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap
            )
        elif self.splitter_type == TextSplitterType.CHARACTER:
            splitter = CharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap
            )
        elif self.splitter_type == TextSplitterType.TOKEN:
            splitter = TokenTextSplitter(
                chunk_size=self.chunk_size // 4,  # Tokens are roughly 4 chars
                chunk_overlap=self.chunk_overlap // 4
            )
        else:
            # Default to recursive splitter
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap
            )
        
        # Split the documents
        try:
            chunked_docs = splitter.split_documents(documents)
            return chunked_docs
        except Exception as e:
            logger.error(f"Error splitting documents: {str(e)}")
            return documents  # Return original documents if splitting fails

    def extract_metadata_from_content(self, document: Document) -> Document:
        """Extract metadata from document content using patterns"""
        content = document.page_content
        metadata = document.metadata.copy()
        
        # Example: Extract title pattern (e.g., # Title or Title =====)
        title_patterns = [
            r'^#\s+(.+)$',  # Markdown h1
            r'^(.+)\n=+$',   # Underlined header
            r'<title>(.*?)</title>'  # HTML title
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, content, re.MULTILINE)
            if match:
                metadata["title"] = match.group(1).strip()
                break
        
        # You could add more patterns here for other metadata
        # For example, extract authors, dates, etc.
        
        # Update document with new metadata
        document.metadata = metadata
        return document