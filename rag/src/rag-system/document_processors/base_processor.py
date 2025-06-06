"""Base document processor for the RAG system."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from utils.logging import logger
from utils.metrics import collector

class BaseDocumentProcessor(ABC):
    """Abstract base class for document processors."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logger
        self.metrics = collector
    
    @abstractmethod
    async def process(self, content: str) -> Dict[str, Any]:
        """Process a document and return structured data."""
        pass
    
    @abstractmethod
    async def extract_metadata(self, content: str) -> Dict[str, Any]:
        """Extract metadata from document content."""
        pass
    
    async def preprocess(self, content: str) -> str:
        """Perform any necessary preprocessing on the content."""
        with self.metrics.measure_time("document_preprocessing"):
            # Basic preprocessing - override for specific needs
            cleaned = content.strip()
            return cleaned
    
    async def validate(self, processed_data: Dict[str, Any]) -> bool:
        """Validate processed document data."""
        required_fields = {"text", "metadata"}
        return all(field in processed_data for field in required_fields)
    
    async def process_batch(
        self,
        documents: List[str],
        batch_size: int = 10
    ) -> List[Dict[str, Any]]:
        """Process multiple documents in batches."""
        results = []
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            with self.metrics.measure_time(
                "batch_processing",
                {"batch_size": str(len(batch))}
            ):
                for doc in batch:
                    try:
                        result = await self.process(doc)
                        if await self.validate(result):
                            results.append(result)
                    except Exception as e:
                        self.logger.error(f"Error processing document: {e}")
        return results