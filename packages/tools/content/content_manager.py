"""Content management tool for the space project."""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from utils.logging import logger
from utils.metrics import collector
from utils.security import generate_secure_hash

class ContentManager:
    """Manages content operations across the system."""
    
    def __init__(
        self,
        storage_backend: Any,
        max_content_size: int = 10_000_000,  # 10MB
        supported_formats: Optional[List[str]] = None
    ):
        self.storage = storage_backend
        self.max_content_size = max_content_size
        self.supported_formats = supported_formats or ["text", "json", "html"]
        self.logger = logger
        self.metrics = collector
    
    async def store_content(
        self,
        content: Union[str, Dict[str, Any], bytes],
        content_type: str,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Store content with metadata and tags."""
        with self.metrics.measure_time("content_storage"):
            try:
                # Validate content
                if not self._validate_content(content, content_type):
                    raise ValueError("Invalid content or unsupported format")
                
                # Process content based on type
                processed_content = await self._process_content(
                    content,
                    content_type
                )
                
                # Generate content hash
                content_hash, salt = generate_secure_hash(
                    json.dumps(processed_content)
                )
                
                # Prepare storage object
                storage_object = {
                    "content": processed_content,
                    "content_type": content_type,
                    "metadata": {
                        "hash": content_hash,
                        "salt": salt,
                        "size": len(str(content)),
                        "created_at": datetime.utcnow().isoformat(),
                        "tags": tags or [],
                        **(metadata or {})
                    }
                }
                
                # Store content
                stored_id = await self.storage.store(storage_object)
                
                return {
                    "id": stored_id,
                    "hash": content_hash,
                    "metadata": storage_object["metadata"]
                }
                
            except Exception as e:
                self.logger.error(f"Error storing content: {e}")
                raise
    
    async def retrieve_content(
        self,
        content_id: str,
        include_metadata: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Retrieve stored content by ID."""
        with self.metrics.measure_time("content_retrieval"):
            try:
                stored_object = await self.storage.retrieve(content_id)
                
                if not stored_object:
                    return None
                
                if include_metadata:
                    return stored_object
                    
                return {
                    "content": stored_object["content"],
                    "content_type": stored_object["content_type"]
                }
                
            except Exception as e:
                self.logger.error(f"Error retrieving content: {e}")
                return None
    
    async def update_content(
        self,
        content_id: str,
        content: Union[str, Dict[str, Any], bytes],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update existing content."""
        with self.metrics.measure_time("content_update"):
            try:
                # Get existing content
                existing = await self.retrieve_content(content_id)
                if not existing:
                    return False
                
                # Process new content
                processed_content = await self._process_content(
                    content,
                    existing["content_type"]
                )
                
                # Generate new hash
                content_hash, salt = generate_secure_hash(
                    json.dumps(processed_content)
                )
                
                # Update storage object
                update_object = {
                    "content": processed_content,
                    "metadata": {
                        **existing["metadata"],
                        "hash": content_hash,
                        "salt": salt,
                        "updated_at": datetime.utcnow().isoformat(),
                        **(metadata or {})
                    }
                }
                
                # Store updated content
                success = await self.storage.update(content_id, update_object)
                return success
                
            except Exception as e:
                self.logger.error(f"Error updating content: {e}")
                return False
    
    async def delete_content(self, content_id: str) -> bool:
        """Delete stored content."""
        with self.metrics.measure_time("content_deletion"):
            try:
                return await self.storage.delete(content_id)
            except Exception as e:
                self.logger.error(f"Error deleting content: {e}")
                return False
    
    async def search_content(
        self,
        query: Dict[str, Any],
        limit: int = 10,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Search stored content."""
        with self.metrics.measure_time("content_search"):
            try:
                results = await self.storage.search(
                    query,
                    limit=limit,
                    offset=offset
                )
                
                return {
                    "total": results.get("total", 0),
                    "items": results.get("items", []),
                    "limit": limit,
                    "offset": offset
                }
                
            except Exception as e:
                self.logger.error(f"Error searching content: {e}")
                return {
                    "total": 0,
                    "items": [],
                    "limit": limit,
                    "offset": offset
                }
    
    def _validate_content(
        self,
        content: Union[str, Dict[str, Any], bytes],
        content_type: str
    ) -> bool:
        """Validate content format and size."""
        try:
            if content_type not in self.supported_formats:
                return False
                
            content_size = (
                len(content)
                if isinstance(content, (str, bytes))
                else len(json.dumps(content))
            )
            
            if content_size > self.max_content_size:
                return False
                
            return True
            
        except Exception:
            return False
    
    async def _process_content(
        self,
        content: Union[str, Dict[str, Any], bytes],
        content_type: str
    ) -> Union[str, Dict[str, Any], bytes]:
        """Process content based on its type."""
        try:
            if content_type == "json" and isinstance(content, str):
                return json.loads(content)
            elif content_type == "text" and isinstance(content, bytes):
                return content.decode('utf-8')
            return content
        except Exception as e:
            self.logger.error(f"Error processing content: {e}")
            raise