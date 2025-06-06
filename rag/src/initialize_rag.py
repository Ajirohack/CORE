"""
RAG System Initialization Script
Prepares the RAG system for use in public trials by:
1. Setting up vector stores
2. Loading initial knowledge data
3. Creating embedding models
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent directory to path to import from config
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from config.rag_config import get_config
from core.rag_system.rag_system import RAGSystem

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("rag-init")


def initialize_rag_system(
    environment: str = "public_trial", 
    knowledge_dirs: Optional[List[str]] = None,
    clear_existing: bool = False
) -> RAGSystem:
    """
    Initialize the RAG system for the specified environment
    
    Args:
        environment: Environment to initialize for ('development', 'public_trial', 'production')
        knowledge_dirs: Additional knowledge directories to load
        clear_existing: Whether to clear existing vector store data
        
    Returns:
        Initialized RAG system instance
    """
    logger.info(f"Initializing RAG system for {environment} environment")
    
    # Get configuration for the specified environment
    config = get_config(environment)
    
    # Create RAG system
    rag_system = RAGSystem(config=config)
    
    # Get base directories
    base_dir = Path(__file__).resolve().parent.parent.parent
    data_dir = base_dir / "data"
    
    # Create data directories if they don't exist
    (data_dir / "knowledge").mkdir(parents=True, exist_ok=True)
    (data_dir / "vector_store").mkdir(parents=True, exist_ok=True)
    
    # Clear existing vector store if requested
    if clear_existing:
        logger.warning("Clearing existing vector store data")
        # Fix: Access persist_directory instead of path
        vector_store_path = config.vector_store.get("persist_directory")
        if vector_store_path:
            vector_store_path = Path(vector_store_path)
            if vector_store_path.exists():
                logger.info(f"Removing existing vector store at {vector_store_path}")
                import shutil
                shutil.rmtree(vector_store_path, ignore_errors=True)
    
    # Process knowledge directories from configuration
    # Fix: Use config if it has knowledge_sources attribute, otherwise empty dict
    knowledge_sources = getattr(config, "knowledge_sources", {}) if hasattr(config, "knowledge_sources") else {}
    # Fix: Use get method correctly with knowledge_sources
    local_file_sources = knowledge_sources.get("local_files", []) if isinstance(knowledge_sources, dict) else []
    
    # Add additional knowledge directories
    if knowledge_dirs:
        for dir_path in knowledge_dirs:
            path = Path(dir_path)
            if path.exists() and path.is_dir():
                local_file_sources.append({
                    "path": str(path),
                    "recursive": True,
                    "description": f"Additional knowledge from {path.name}"
                })
    
    # Process each knowledge source
    doc_count = 0
    for source in local_file_sources:
        source_path = source["path"]
        recursive = source.get("recursive", False)
        
        logger.info(f"Processing knowledge source: {source_path} (recursive={recursive})")
        
        try:
            # Add documents from the directory
            ids = rag_system.process_and_add_directory(source_path, recursive=recursive)
            logger.info(f"Added {len(ids)} documents from {source_path}")
            doc_count += len(ids)
        except Exception as e:
            logger.error(f"Error processing {source_path}: {str(e)}")
    
    # Save the vector store
    logger.info(f"Saving vector store with {doc_count} total documents")
    rag_system.save()
    
    logger.info("RAG system initialization complete")
    return rag_system


def main():
    """Command line interface for RAG system initialization"""
    parser = argparse.ArgumentParser(description="Initialize the RAG system")
    parser.add_argument(
        "--env", "-e",
        choices=["development", "public_trial", "production"],
        default="public_trial",
        help="Environment to initialize for"
    )
    parser.add_argument(
        "--knowledge", "-k",
        nargs="+",
        help="Additional knowledge directories to process"
    )
    parser.add_argument(
        "--clear", "-c",
        action="store_true",
        help="Clear existing vector store data"
    )
    
    args = parser.parse_args()
    initialize_rag_system(
        environment=args.env,
        knowledge_dirs=args.knowledge,
        clear_existing=args.clear
    )


if __name__ == "__main__":
    main()