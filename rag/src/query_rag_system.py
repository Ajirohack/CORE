#!/usr/bin/env python3
"""
Script for testing the RAG system's retrieval capabilities.
This tool helps validate that the vector database is working correctly.
"""

import os
import sys
import argparse
import logging
import warnings
import faiss
import pickle
import numpy as np
from pathlib import Path
import json

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Import our RAG functions
from load_rag_database import get_embeddings

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
    parser = argparse.ArgumentParser(description="Query the RAG system")
    parser.add_argument("--query", type=str, required=True, 
                      help="The question or query to search for")
    parser.add_argument("--num-results", type=int, default=5,
                      help="Number of results to return (default: 5)")
    parser.add_argument("--format", choices=["text", "json"], default="text",
                      help="Output format (default: text)")
    return parser.parse_args()

def load_database():
    """Load the FAISS index and documents."""
    try:
        logger.info(f"Loading index from {INDEX_FILE}")
        index = faiss.read_index(INDEX_FILE)
        
        logger.info(f"Loading documents from {DOCUMENTS_FILE}")
        with open(DOCUMENTS_FILE, 'rb') as f:
            documents = pickle.load(f)
            
        return index, documents
    except Exception as e:
        logger.error(f"Error loading database: {e}")
        sys.exit(1)

def search(query, index, documents, num_results=5):
    """Search the RAG system with a query."""
    try:
        # Get embedding for the query
        query_embedding = get_embeddings([query])[0]
        query_embedding_array = np.array([query_embedding]).astype('float32')
        
        # Search the index
        distances, indices = index.search(query_embedding_array, num_results)
        
        results = []
        for i, doc_idx in enumerate(indices[0]):
            if doc_idx < len(documents):
                doc = documents[doc_idx]
                results.append({
                    "rank": i + 1,
                    "score": float(distances[0][i]),
                    "source": doc.metadata.get('source', 'Unknown'),
                    "content": doc.page_content.strip(),
                })
        
        return results
    except Exception as e:
        logger.error(f"Error during search: {e}")
        return []

def format_results_text(results):
    """Format results as text."""
    if not results:
        return "No results found."
    
    output = []
    output.append("\n===== RAG SEARCH RESULTS =====\n")
    
    for result in results:
        output.append(f"--- Result {result['rank']} (Score: {result['score']:.4f}) ---")
        output.append(f"Source: {result['source']}")
        output.append("Content:")
        output.append(result['content'])
        output.append("")  # Empty line
    
    return "\n".join(output)

def format_results_json(results):
    """Format results as JSON."""
    return json.dumps(results, indent=2)

def main():
    args = parse_args()
    
    # Verify vector database directory exists
    if not os.path.exists(VECTOR_DB_PATH):
        logger.error(f"Vector database directory not found: {VECTOR_DB_PATH}")
        sys.exit(1)
    
    # Load database
    index, documents = load_database()
    
    # Log database info
    logger.info(f"Loaded index with {index.ntotal} vectors of dimension {index.d}")
    logger.info(f"Loaded {len(documents)} documents")
    
    # Execute search
    logger.info(f"Searching for: '{args.query}'")
    results = search(args.query, index, documents, args.num_results)
    
    # Format and output results
    if args.format == "json":
        print(format_results_json(results))
    else:
        print(format_results_text(results))

if __name__ == "__main__":
    main()