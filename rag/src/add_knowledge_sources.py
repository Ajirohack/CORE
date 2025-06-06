#!/usr/bin/env python3
"""
Script for adding new knowledge sources to the existing RAG database.
This allows incremental updates to the vector database without reprocessing all documents.
"""

import os
import sys
import argparse
import logging
import warnings
import glob
import faiss
import pickle
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Import our RAG loader functions
from load_rag_database import read_file, split_text, get_embeddings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress warnings
warnings.filterwarnings("ignore")

# Constants
VECTOR_DB_PATH = os.path.join(project_root, "vector_db")
INDEX_FILE = os.path.join(VECTOR_DB_PATH, "index.faiss")
DOCUMENTS_FILE = os.path.join(VECTOR_DB_PATH, "documents.pkl")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Add new knowledge sources to the RAG database")
    parser.add_argument("--sources", nargs="+", required=True, 
                      help="File paths or glob patterns for new knowledge sources")
    parser.add_argument("--chunk-size", type=int, default=800,
                      help="Size of text chunks for embeddings (default: 800)")
    parser.add_argument("--chunk-overlap", type=int, default=150,
                      help="Overlap between text chunks (default: 150)")
    return parser.parse_args()

def read_files(patterns: List[str]) -> List[str]:
    """Read all files matching the patterns."""
    all_files = []
    for pattern in patterns:
        if "*" in pattern:
            all_files.extend(glob.glob(pattern))
        elif os.path.isfile(pattern):
            all_files.append(pattern)
    return all_files

def load_existing_database() -> tuple:
    """Load the existing FAISS index and documents."""
    try:
        logger.info(f"Loading existing index from {INDEX_FILE}")
        index = faiss.read_index(INDEX_FILE)
        
        logger.info(f"Loading existing documents from {DOCUMENTS_FILE}")
        with open(DOCUMENTS_FILE, 'rb') as f:
            documents = pickle.load(f)
            
        return index, documents
    except Exception as e:
        logger.error(f"Error loading existing database: {e}")
        logger.error("Make sure to run load_rag_database.py first to create the initial database")
        sys.exit(1)

def process_file(file_path: str, chunk_size: int = 800, chunk_overlap: int = 150) -> tuple:
    """Process a single file into chunks with embeddings."""
    logger.info(f"Processing {file_path}")
    content = read_file(file_path)
    if not content:
        return [], []
    
    metadata = {
        "source": file_path,
        "file_type": os.path.splitext(file_path)[1].lstrip('.') or "txt"
    }
    
    chunks = split_text(content, metadata, chunk_size, chunk_overlap)
    logger.info(f"Created {len(chunks)} chunks from {file_path}")
    
    # Get text content from chunks for embedding
    texts = [chunk.page_content for chunk in chunks]
    
    # Get embeddings in batches of 5
    all_embeddings = []
    for i in range(0, len(texts), 5):
        batch_texts = texts[i:i+5]
        batch_embeddings = get_embeddings(batch_texts)
        if batch_embeddings:
            all_embeddings.extend(batch_embeddings)
            logger.info(f"Generated embeddings for batch {i//5 + 1} of {len(texts)//5 + 1}")
        else:
            logger.error(f"Failed to get embeddings for batch {i//5 + 1}")
            return [], []
    
    return chunks, all_embeddings

def main():
    args = parse_args()
    
    # Verify vector database directory exists
    if not os.path.exists(VECTOR_DB_PATH):
        logger.error(f"Vector database directory not found: {VECTOR_DB_PATH}")
        logger.error("Run load_rag_database.py first to create the initial database")
        sys.exit(1)
    
    # Load existing database
    index, all_documents = load_existing_database()
    
    # Get dimension of embeddings
    dimension = index.d
    logger.info(f"Existing index has {index.ntotal} vectors with dimension {dimension}")
    logger.info(f"Existing documents: {len(all_documents)}")
    
    # Get all new files to process
    file_paths = read_files(args.sources)
    logger.info(f"Found {len(file_paths)} new files to process")
    
    if not file_paths:
        logger.warning("No files found matching the patterns provided")
        sys.exit(0)
    
    # Process files
    new_documents = []
    new_embeddings = []
    
    for file_path in file_paths:
        chunks, embeddings = process_file(file_path, args.chunk_size, args.chunk_overlap)
        if chunks and embeddings:
            new_documents.extend(chunks)
            new_embeddings.extend(embeddings)
    
    if not new_documents:
        logger.error("No new documents were created")
        return
    
    logger.info(f"Created {len(new_documents)} new chunks with embeddings")
    
    # Convert embeddings to numpy array for FAISS
    embeddings_array = np.array(new_embeddings).astype('float32')
    
    # Add new vectors to the index
    index.add(embeddings_array)
    
    # Add new documents to the documents list
    all_documents.extend(new_documents)
    
    # Save updated index and documents
    faiss.write_index(index, INDEX_FILE)
    with open(DOCUMENTS_FILE, 'wb') as f:
        pickle.dump(all_documents, f)
    
    logger.info(f"Updated FAISS index now contains {index.ntotal} vectors")
    logger.info(f"Saved {len(all_documents)} documents to {DOCUMENTS_FILE}")
    logger.info(f"Added {len(new_documents)} new documents to the database")

if __name__ == "__main__":
    main()