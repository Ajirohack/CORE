"""
Document Processor for Superior RAG System.

This module handles the parsing, chunking, and processing of documents
before they are stored in the system's databases.
"""

import logging
import asyncio
import uuid
import os
import tempfile
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple, BinaryIO, Set
import hashlib
import re
from pathlib import Path

from src.utils.config import load_config
from src.utils.embeddings import get_embedding_model
from src.storage.vector_store import get_vector_store
from src.storage.relational_store import get_relational_store
from src.storage.graph_store import get_graph_store

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("superior_rag.core.document_processor")

# Load configuration
config = load_config()


class DocumentProcessor:
    """
    Document Processor for handling document ingestion.
    
    This component:
    1. Parses different document formats (PDF, DOCX, TXT, etc.)
    2. Chunks documents using intelligent strategies
    3. Extracts metadata and entities
    4. Generates embeddings for chunks
    5. Stores document data in appropriate databases
    """
    
    def __init__(self):
        """Initialize the document processor."""
        # Load document processing configuration
        self.doc_config = config.get("document_processing", {})
        
        # Configuration parameters for chunking
        self.default_chunk_size = self.doc_config.get("chunking", {}).get("default_chunk_size", 1000)
        self.default_chunk_overlap = self.doc_config.get("chunking", {}).get("default_overlap", 200)
        self.adaptive_chunking = self.doc_config.get("chunking", {}).get("adaptive", True)
        
        # Configuration for entity extraction
        self.entity_extraction_enabled = self.doc_config.get("entity_extraction", {}).get("enabled", True)
        self.entity_extraction_model = self.doc_config.get("entity_extraction", {}).get("spacy_model", "en_core_web_sm")
        
        # Temporary directory for processing files
        self.temp_dir = config.get("document_processing", {}).get("temp_dir", "data/temp")
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Maximum file size (100MB default)
        self.max_file_size = config.get("document_processing", {}).get("max_file_size_mb", 100) * 1024 * 1024
        
        # Supported file extensions
        self.supported_extensions = {
            ".pdf", ".docx", ".doc", ".txt", ".md", ".rtf", 
            ".csv", ".json", ".html", ".htm", ".pptx", ".xlsx"
        }
        
        # Initialize NLP components if entity extraction is enabled
        self.nlp = None
        if self.entity_extraction_enabled:
            self._init_nlp()
            
        logger.info("Document processor initialized")
        
    def _init_nlp(self):
        """Initialize NLP components for entity extraction."""
        try:
            import spacy
            self.nlp = spacy.load(self.entity_extraction_model)
            logger.info(f"Loaded spaCy model: {self.entity_extraction_model}")
        except ImportError:
            logger.warning("spaCy not installed. Entity extraction disabled.")
            self.entity_extraction_enabled = False
        except OSError:
            logger.warning(f"Could not load spaCy model: {self.entity_extraction_model}. "
                          "Run 'python -m spacy download en_core_web_sm'")
            self.entity_extraction_enabled = False
        
    async def process_document(
        self,
        file_content: Union[str, bytes, BinaryIO],
        filename: str,
        metadata: Optional[Dict[str, Any]] = None,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ) -> str:
        """
        Process a document and store it in the system.
        
        Args:
            file_content: Content of the file (string, bytes, or file-like object)
            filename: Name of the file
            metadata: Additional metadata about the document
            chunk_size: Size of chunks to create (in characters)
            chunk_overlap: Overlap between chunks (in characters)
            
        Returns:
            str: The document ID
        """
        # Generate document ID
        document_id = str(uuid.uuid4())
        
        # Get file extension
        _, ext = os.path.splitext(filename.lower())
        
        # Validate file extension
        if ext not in self.supported_extensions:
            supported_ext_list = ", ".join(self.supported_extensions)
            raise ValueError(f"Unsupported file extension: {ext}. "
                            f"Supported extensions: {supported_ext_list}")
        
        # Set default metadata if not provided
        if metadata is None:
            metadata = {}
            
        # Add basic metadata
        metadata.update({
            "filename": filename,
            "file_extension": ext,
            "processed_at": datetime.utcnow().isoformat(),
            "document_id": document_id,
        })
        
        logger.info(f"Processing document: {filename} (ID: {document_id})")
        
        # Use default chunking parameters if not specified
        if chunk_size is None:
            chunk_size = self.default_chunk_size
        if chunk_overlap is None:
            chunk_overlap = self.default_chunk_overlap
            
        # Parse the document content
        raw_text = await self._parse_document(file_content, filename)
        
        # Add text stats to metadata
        metadata["character_count"] = len(raw_text)
        metadata["word_count"] = len(raw_text.split())
        
        # Extract document-level entities if enabled
        if self.entity_extraction_enabled:
            entities = await self._extract_entities(raw_text)
            metadata["entities"] = entities
        
        # Create chunks from the document
        chunks = await self._create_chunks(
            raw_text, 
            chunk_size, 
            chunk_overlap,
            adaptive=self.adaptive_chunking
        )
        
        # Store document metadata in relational database
        relational_store = get_relational_store()
        await relational_store.store_document_metadata(document_id, metadata)
        
        # Process and store each chunk
        embedding_model = get_embedding_model()
        vector_store = get_vector_store()
        graph_store = get_graph_store()
        
        # Prepare chunks for batch processing
        chunk_data = []
        
        for i, chunk in enumerate(chunks):
            # Create chunk metadata
            chunk_id = f"{document_id}_chunk_{i}"
            chunk_metadata = {
                "document_id": document_id,
                "chunk_index": i,
                "chunk_id": chunk_id,
                "start_char": chunk["start_char"],
                "end_char": chunk["end_char"],
                "chunk_size": len(chunk["text"]),
            }
            
            # Extract entities for this chunk
            if self.entity_extraction_enabled and len(chunk["text"]) > 0:
                chunk_entities = await self._extract_entities(chunk["text"])
                chunk_metadata["entities"] = chunk_entities
            
            # Generate embedding for this chunk
            embedding = await embedding_model.get_text_embedding(chunk["text"])
            
            # Add to batch data
            chunk_data.append({
                "id": chunk_id,
                "document_id": document_id,
                "chunk_index": i,
                "text": chunk["text"],
                "embedding": embedding,
                "metadata": {**metadata, **chunk_metadata}
            })
        
        # Store chunks in vector database
        await vector_store.store_documents(chunk_data)
        
        # Store chunk metadata in relational database
        for chunk in chunk_data:
            await relational_store.store_chunk_metadata(
                document_id=chunk["document_id"],
                chunk_id=chunk["id"],
                chunk_index=chunk["chunk_index"],
                metadata=chunk["metadata"],
                text=chunk["text"],
                embedding=None  # We don't store embeddings in relational DB
            )
        
        # Store entity relationships in graph database if enabled
        if self.entity_extraction_enabled:
            await self._store_entity_relationships(document_id, metadata, chunk_data)
        
        logger.info(f"Document processing complete: {filename} (ID: {document_id})")
        logger.info(f"Created {len(chunks)} chunks")
        
        return document_id
        
    async def _parse_document(
        self,
        file_content: Union[str, bytes, BinaryIO],
        filename: str
    ) -> str:
        """
        Parse the document content based on file type.
        
        Args:
            file_content: Content of the file
            filename: Name of the file
            
        Returns:
            str: The parsed text content
        """
        # Get file extension
        _, ext = os.path.splitext(filename.lower())
        
        # Create a temporary file if needed
        if isinstance(file_content, (bytes, BinaryIO)):
            with tempfile.NamedTemporaryFile(delete=False, dir=self.temp_dir, suffix=ext) as temp_file:
                if isinstance(file_content, bytes):
                    temp_file.write(file_content)
                else:
                    # Copy file-like object content
                    file_content.seek(0)
                    temp_file.write(file_content.read())
                    
                temp_path = temp_file.name
                
            try:
                # Parse based on file type
                if ext == ".pdf":
                    text = await self._parse_pdf(temp_path)
                elif ext in {".docx", ".doc"}:
                    text = await self._parse_docx(temp_path)
                elif ext == ".txt":
                    text = await self._parse_text_file(temp_path)
                elif ext == ".md":
                    text = await self._parse_text_file(temp_path)
                elif ext == ".html" or ext == ".htm":
                    text = await self._parse_html(temp_path)
                elif ext in {".csv", ".xlsx"}:
                    text = await self._parse_tabular(temp_path, ext)
                else:
                    # Attempt generic text extraction
                    text = await self._parse_text_file(temp_path)
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_path)
                except:
                    pass
        else:
            # Direct string content
            text = file_content
            
        return text
    
    async def _parse_pdf(self, file_path: str) -> str:
        """Parse a PDF file."""
        try:
            from pypdf import PdfReader
            
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n\n"
                
            return text
        except ImportError:
            logger.error("pypdf not installed. Cannot parse PDF.")
            raise ImportError("pypdf library is required to parse PDF files")
    
    async def _parse_docx(self, file_path: str) -> str:
        """Parse a DOCX/DOC file."""
        try:
            import docx
            
            doc = docx.Document(file_path)
            text = "\n\n".join([para.text for para in doc.paragraphs])
            return text
        except ImportError:
            logger.error("python-docx not installed. Cannot parse DOCX.")
            raise ImportError("python-docx library is required to parse DOCX files")
    
    async def _parse_text_file(self, file_path: str) -> str:
        """Parse a plain text file."""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    
    async def _parse_html(self, file_path: str) -> str:
        """Parse an HTML file."""
        try:
            from bs4 import BeautifulSoup
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                soup = BeautifulSoup(f, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.extract()
                    
                # Get text
                text = soup.get_text()
                
                # Break into lines and remove leading and trailing space
                lines = (line.strip() for line in text.splitlines())
                
                # Break multi-headlines into a line each
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                
                # Drop blank lines
                text = '\n'.join(chunk for chunk in chunks if chunk)
                
                return text
        except ImportError:
            logger.error("beautifulsoup4 not installed. Cannot parse HTML.")
            raise ImportError("beautifulsoup4 library is required to parse HTML files")
    
    async def _parse_tabular(self, file_path: str, ext: str) -> str:
        """Parse a tabular file (CSV, Excel)."""
        try:
            import pandas as pd
            
            # Read based on file type
            if ext == ".csv":
                df = pd.read_csv(file_path)
            elif ext == ".xlsx":
                df = pd.read_excel(file_path)
                
            # Convert to a text representation
            buffer = []
            
            # Add column names
            buffer.append(", ".join(df.columns))
            
            # Add rows
            for _, row in df.iterrows():
                buffer.append(", ".join(str(val) for val in row.values))
                
            return "\n".join(buffer)
        except ImportError:
            logger.error("pandas not installed. Cannot parse tabular data.")
            raise ImportError("pandas library is required to parse tabular files")
    
    async def _create_chunks(
        self,
        text: str,
        chunk_size: int,
        chunk_overlap: int,
        adaptive: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Create chunks from document text.
        
        Args:
            text: The document text
            chunk_size: Size of chunks (in characters)
            chunk_overlap: Overlap between chunks (in characters)
            adaptive: Whether to use adaptive chunking
            
        Returns:
            List[Dict[str, Any]]: List of chunks with metadata
        """
        if adaptive:
            return await self._create_adaptive_chunks(text, chunk_size, chunk_overlap)
        else:
            return await self._create_fixed_chunks(text, chunk_size, chunk_overlap)
    
    async def _create_fixed_chunks(
        self,
        text: str,
        chunk_size: int,
        chunk_overlap: int
    ) -> List[Dict[str, Any]]:
        """Create fixed-size chunks from text."""
        chunks = []
        
        # If text is smaller than chunk size, return as single chunk
        if len(text) <= chunk_size:
            chunks.append({
                "text": text,
                "start_char": 0,
                "end_char": len(text)
            })
            return chunks
        
        # Create overlapping chunks
        start = 0
        while start < len(text):
            # Get chunk end position
            end = start + chunk_size
            
            # Adjust end to break at sentence if possible
            if end < len(text):
                # Try to find sentence boundary
                sentence_end = text.rfind('. ', start, end) + 1
                
                if sentence_end > start + chunk_size // 2:
                    end = sentence_end
            else:
                end = len(text)
                
            # Add chunk
            chunks.append({
                "text": text[start:end],
                "start_char": start,
                "end_char": end
            })
            
            # Update start position for next chunk
            start = end - chunk_overlap
            
            # If overlap would create a tiny chunk at the end, adjust
            if start + chunk_size > len(text) and len(text) - start < chunk_size // 2:
                break
                
        return chunks
    
    async def _create_adaptive_chunks(
        self,
        text: str,
        chunk_size: int,
        chunk_overlap: int
    ) -> List[Dict[str, Any]]:
        """
        Create chunks adaptively based on document structure.
        
        This method tries to respect document structure (paragraphs, sections)
        when creating chunks.
        """
        chunks = []
        
        # Split text into paragraphs
        paragraphs = re.split(r'\n\s*\n', text)
        
        current_chunk = []
        current_size = 0
        current_start = 0
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
                
            paragraph_size = len(paragraph)
            
            # If adding this paragraph exceeds the chunk size and we already have content,
            # finalize the current chunk
            if current_size + paragraph_size > chunk_size and current_size > 0:
                # Create chunk
                chunk_text = "\n\n".join(current_chunk)
                chunks.append({
                    "text": chunk_text,
                    "start_char": current_start,
                    "end_char": current_start + len(chunk_text)
                })
                
                # Start a new chunk with overlap
                overlap_start = max(0, len(current_chunk) - 2)  # Keep last 2 paragraphs for context
                current_chunk = current_chunk[overlap_start:]
                current_size = sum(len(p) for p in current_chunk) + len(current_chunk) - 1
                current_start = current_start + len(chunk_text) - current_size
            
            # Add paragraph to current chunk
            current_chunk.append(paragraph)
            current_size += paragraph_size + 2  # +2 for the newlines
            
            # If a single paragraph is larger than chunk size, split it further
            if paragraph_size > chunk_size:
                # Create fixed chunks from this paragraph
                para_chunks = await self._create_fixed_chunks(
                    paragraph,
                    chunk_size,
                    chunk_overlap
                )
                
                # Add all but the first chunk (which is included in current_chunk)
                for i, para_chunk in enumerate(para_chunks):
                    if i == 0:
                        continue
                        
                    chunks.append({
                        "text": para_chunk["text"],
                        "start_char": current_start + para_chunk["start_char"],
                        "end_char": current_start + para_chunk["end_char"]
                    })
                
                # Reset current chunk
                current_chunk = []
                current_size = 0
                current_start += paragraph_size
        
        # Add the final chunk if there's anything left
        if current_chunk:
            chunk_text = "\n\n".join(current_chunk)
            chunks.append({
                "text": chunk_text,
                "start_char": current_start,
                "end_char": current_start + len(chunk_text)
            })
            
        return chunks
    
    async def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract entities from text using NLP.
        
        Args:
            text: Text to analyze
            
        Returns:
            List[Dict[str, Any]]: List of entities with metadata
        """
        if not self.entity_extraction_enabled or not self.nlp:
            return []
            
        # Skip if text is too long to process efficiently
        if len(text) > 100000:  # 100K character limit for NLP processing
            logger.warning("Text too long for entity extraction")
            return []
            
        try:
            # Process with spaCy
            doc = self.nlp(text[:100000])  # Limit to first 100K chars
            
            # Extract entities
            entities = []
            for ent in doc.ents:
                entities.append({
                    "text": ent.text,
                    "label": ent.label_,
                    "start_char": ent.start_char,
                    "end_char": ent.end_char
                })
                
            return entities
        except Exception as e:
            logger.error(f"Error during entity extraction: {e}")
            return []
    
    async def _store_entity_relationships(
        self,
        document_id: str,
        document_metadata: Dict[str, Any],
        chunks: List[Dict[str, Any]]
    ) -> None:
        """
        Store entity relationships in the graph database.
        
        Args:
            document_id: Document ID
            document_metadata: Document metadata
            chunks: Processed chunks with entity information
        """
        if not self.entity_extraction_enabled:
            return
            
        # Get graph store
        graph_store = get_graph_store()
        
        # Create document node
        await graph_store.create_document_node(
            document_id=document_id,
            properties=document_metadata
        )
        
        # Process each chunk
        for chunk in chunks:
            chunk_id = chunk["id"]
            chunk_index = chunk["chunk_index"]
            
            # Create chunk node
            await graph_store.create_chunk_node(
                chunk_id=chunk_id,
                document_id=document_id,
                chunk_index=chunk_index,
                properties={
                    "text_snippet": chunk["text"][:200] + "...",
                    "chunk_length": len(chunk["text"])
                }
            )
            
            # Process entities in the chunk
            if "entities" in chunk["metadata"]:
                entities = chunk["metadata"]["entities"]
                
                # Track entities we've processed for this chunk
                processed_entities = set()
                
                for entity in entities:
                    entity_text = entity["text"]
                    entity_type = entity["label"]
                    
                    # Skip duplicate entities in the same chunk
                    entity_key = f"{entity_text.lower()}:{entity_type}"
                    if entity_key in processed_entities:
                        continue
                        
                    processed_entities.add(entity_key)
                    
                    # Create entity node if it doesn't exist
                    await graph_store.create_entity_node(
                        entity_text=entity_text,
                        entity_type=entity_type
                    )
                    
                    # Create relationship between chunk and entity
                    await graph_store.create_chunk_entity_relation(
                        chunk_id=chunk_id,
                        entity_text=entity_text,
                        entity_type=entity_type
                    )
                    
        # Find relationships between entities
        await graph_store.analyze_entity_relationships(document_id)
    
    async def delete_document(self, document_id: str) -> bool:
        """
        Delete a document and all its chunks from the system.
        
        Args:
            document_id: ID of the document to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info(f"Deleting document: {document_id}")
        
        try:
            # Delete from vector store
            vector_store = get_vector_store()
            await vector_store.delete_by_filter({"document_id": document_id})
            
            # Delete from relational store
            relational_store = get_relational_store()
            await relational_store.delete_document_metadata(document_id)
            
            # Delete from graph store
            graph_store = get_graph_store()
            await graph_store.delete_document(document_id)
            
            logger.info(f"Document deleted: {document_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {e}")
            return False
    
    async def update_document(
        self,
        document_id: str,
        file_content: Union[str, bytes, BinaryIO],
        filename: str,
        metadata: Optional[Dict[str, Any]] = None,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ) -> bool:
        """
        Update an existing document.
        
        This method deletes the existing document and replaces it with
        the new version.
        
        Args:
            document_id: ID of the document to update
            file_content: New file content
            filename: New filename
            metadata: New metadata (will be merged with existing)
            chunk_size: Size of chunks to create
            chunk_overlap: Overlap between chunks
            
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info(f"Updating document: {document_id}")
        
        try:
            # Get existing metadata
            relational_store = get_relational_store()
            existing_metadata = await relational_store.get_document_metadata(document_id)
            
            if existing_metadata is None:
                logger.error(f"Document not found: {document_id}")
                return False
                
            # Merge metadata if provided
            if metadata:
                existing_metadata.update(metadata)
                
            # Delete existing document
            await self.delete_document(document_id)
            
            # Process new document with the same ID
            await self.process_document(
                file_content=file_content,
                filename=filename,
                metadata=existing_metadata,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
            
            logger.info(f"Document updated: {document_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating document {document_id}: {e}")
            return False

# Singleton instance
_document_processor = None

async def init_document_processor():
    """Initialize the document processor singleton."""
    global _document_processor
    if _document_processor is None:
        _document_processor = DocumentProcessor()
    return _document_processor

def get_document_processor() -> DocumentProcessor:
    """Get the document processor singleton instance."""
    global _document_processor
    if _document_processor is None:
        raise RuntimeError("Document processor not initialized. Call init_document_processor() first")
    return _document_processor