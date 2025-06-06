#!/usr/bin/env python3
"""
Simple test script to verify RAG database contents.
"""

import os
import sys
import faiss
import pickle
import numpy as np
from pathlib import Path
import argparse
from sentence_transformers import SentenceTransformer

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))

# Constants
VECTOR_DB_PATH = os.path.join(project_root, "vector_db")
INDEX_FILE = os.path.join(VECTOR_DB_PATH, "index.faiss")
DOCUMENTS_FILE = os.path.join(VECTOR_DB_PATH, "documents.pkl")

def get_embeddings(texts):
    """Generate embeddings using sentence-transformers."""
    try:
        model = SentenceTransformer('all-MiniLM-L6-v2')
        embeddings = model.encode(texts)
        return [emb.tolist() for emb in embeddings]
    except Exception as e:
        print(f"Error generating embeddings: {e}")
        # Fallback to random embeddings for testing
        print("Using random embeddings as fallback - FOR TESTING ONLY")
        return [np.random.rand(384).tolist() for _ in texts]

def test_query(index, documents, query, num_results=3):
    """Test a query against the RAG database."""
    print(f"\n--- Testing query: '{query}' ---")
    
    # Generate query embedding
    query_embedding = get_embeddings([query])[0]
    query_embedding_array = np.array([query_embedding]).astype('float32')
    
    # Search the index
    distances, indices = index.search(query_embedding_array, num_results)
    
    print(f"\nTop {num_results} results:")
    for i, doc_idx in enumerate(indices[0]):
        if doc_idx < len(documents):
            doc = documents[doc_idx]
            print(f"\nResult {i+1} (Score: {distances[0][i]:.4f}):")
            print(f"  - Source: {doc.metadata.get('source', 'Unknown')}")
            print(f"  - Content: {doc.page_content[:200]}...")

def parse_args():
    parser = argparse.ArgumentParser(description="Test RAG database")
    parser.add_argument("--query", type=str, help="Optional query to test")
    parser.add_argument("--num-results", type=int, default=3, help="Number of results to return")
    return parser.parse_args()

def main():
    args = parse_args()
    
    print(f"Checking RAG database at: {VECTOR_DB_PATH}")
    
    # Check if files exist
    print(f"\nChecking if database files exist:")
    print(f"  - Index file exists: {os.path.exists(INDEX_FILE)}")
    print(f"  - Documents file exists: {os.path.exists(DOCUMENTS_FILE)}")
    
    if not os.path.exists(INDEX_FILE) or not os.path.exists(DOCUMENTS_FILE):
        print("\nERROR: Database files are missing. Run load_rag_database.py first.")
        return
    
    try:
        # Load the index
        index = faiss.read_index(INDEX_FILE)
        print(f"\nFAISS index loaded successfully!")
        print(f"  - Total vectors: {index.ntotal}")
        print(f"  - Vector dimension: {index.d}")
        
        # Load the documents
        with open(DOCUMENTS_FILE, 'rb') as f:
            documents = pickle.load(f)
        print(f"\nDocument store loaded successfully!")
        print(f"  - Total documents: {len(documents)}")
        
        # Print sample documents
        print(f"\nSample documents (top 3):")
        for i, doc in enumerate(documents[:3]):
            print(f"\nDocument {i+1}:")
            print(f"  - Source: {doc.metadata.get('source', 'Unknown')}")
            print(f"  - Content: {doc.page_content[:150]}...")
        
        # If query was provided, test it
        if args.query:
            test_query(index, documents, args.query, args.num_results)
        else:
            # Run some sample queries
            test_queries = [
                "What is the SpaceWH project about?",
                "What are the main features of the Space platform?",
                "How does the AI council work?",
                "What clients are available in the Space project?"
            ]
            for query in test_queries:
                test_query(index, documents, query)
        
    except Exception as e:
        print(f"\nERROR: Failed to load database files: {e}")
        return
    
    print("\nRAG database verification complete!")

if __name__ == "__main__":
    main()