"""Document processing tool for the space project."""

import json
from typing import Any, Dict, List, Optional, Union

from langchain.text_splitter import RecursiveCharacterTextSplitter
from utils.logging import logger
from utils.metrics import collector

class DocumentProcessor:
    """Processes and prepares documents for the system."""
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        max_doc_size: int = 1000000
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.max_doc_size = max_doc_size
        self.logger = logger
        self.metrics = collector
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
    
    async def process_document(
        self,
        content: Union[str, Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None,
        split: bool = True
    ) -> List[Dict[str, Any]]:
        """Process a document and prepare it for indexing."""
        with self.metrics.measure_time("document_processing"):
            try:
                # Handle dictionary input
                if isinstance(content, dict):
                    text = self._extract_text_from_dict(content)
                else:
                    text = content
                
                # Validate document size
                if len(text) > self.max_doc_size:
                    self.logger.warning(
                        f"Document exceeds max size: {len(text)} > {self.max_doc_size}"
                    )
                    text = text[:self.max_doc_size]
                
                # Split if requested
                if split:
                    chunks = await self._split_text(text)
                else:
                    chunks = [text]
                
                # Prepare document chunks
                processed_chunks = []
                for i, chunk in enumerate(chunks):
                    chunk_metadata = {
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                        **(metadata or {})
                    }
                    
                    processed_chunk = {
                        "text": chunk,
                        "metadata": chunk_metadata
                    }
                    
                    processed_chunks.append(processed_chunk)
                
                return processed_chunks
                
            except Exception as e:
                self.logger.error(f"Error processing document: {e}")
                return []
    
    async def batch_process(
        self,
        documents: List[Union[str, Dict[str, Any]]],
        metadata_list: Optional[List[Dict[str, Any]]] = None,
        split: bool = True
    ) -> List[List[Dict[str, Any]]]:
        """Process multiple documents in batch."""
        results = []
        metadata_list = metadata_list or [None] * len(documents)
        
        for doc, meta in zip(documents, metadata_list):
            with self.metrics.measure_time("batch_document_processing"):
                try:
                    processed = await self.process_document(
                        doc,
                        metadata=meta,
                        split=split
                    )
                    results.append(processed)
                except Exception as e:
                    self.logger.error(f"Error in batch processing: {e}")
                    results.append([])
        
        return results
    
    def _extract_text_from_dict(self, content: Dict[str, Any]) -> str:
        """Extract text content from a dictionary structure."""
        try:
            # Handle common document formats
            if "text" in content:
                return content["text"]
            elif "content" in content:
                return content["content"]
            else:
                # Fallback to JSON string
                return json.dumps(content, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Error extracting text from dict: {e}")
            return ""
    
    async def _split_text(self, text: str) -> List[str]:
        """Split text into chunks using the text splitter."""
        try:
            return self.text_splitter.split_text(text)
        except Exception as e:
            self.logger.error(f"Error splitting text: {e}")
            return [text]  # Return original text as single chunk
            
    async def extract_metadata(
        self,
        text: str,
        extractors: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Extract metadata from document text."""
        metadata = {}
        
        # Default extractors if none specified
        extractors = extractors or ["language", "length", "keywords"]
        
        for extractor in extractors:
            with self.metrics.measure_time(f"metadata_extraction_{extractor}"):
                try:
                    if extractor == "language":
                        # TODO: Implement language detection
                        metadata["language"] = "en"
                    elif extractor == "length":
                        metadata["length"] = len(text)
                    elif extractor == "keywords":
                        # TODO: Implement keyword extraction
                        metadata["keywords"] = []
                except Exception as e:
                    self.logger.error(f"Error in metadata extraction: {e}")
        
        return metadata