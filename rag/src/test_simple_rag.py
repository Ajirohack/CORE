#!/usr/bin/env python3
"""
Simplified test script for the RAG database.
This script doesn't require sentence-transformers and uses the existing vectors.
"""

import os
import sys
import faiss
import pickle
import numpy as np
import random

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))

# Constants
VECTOR_DB_PATH = os.path.join(project_root, "vector_db")
INDEX_FILE = os.path.join(VECTOR_DB_PATH, "index.faiss")
DOCUMENTS_FILE = os.path.join(VECTOR_DB_PATH, "documents.pkl")

def main():
    """Main function to test the RAG database."""
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
            print(f"  - Content preview: {doc.page_content[:100]}...")
        
        # Random sampling for browsing
        print("\n\nRandom sample of 3 documents for browsing:")
        random_indices = random.sample(range(len(documents)), min(3, len(documents)))
        for i, idx in enumerate(random_indices):
            doc = documents[idx]
            print(f"\nRandom Document {i+1}:")
            print(f"  - Source: {doc.metadata.get('source', 'Unknown')}")
            print(f"  - Content preview: {doc.page_content[:100]}...")
            
        # Test search with a random vector
        print("\n\nTesting vector search capability:")
        if len(documents) > 0:
            # Create a random query vector with the same dimension as the index
            dimension = index.d
            query_vector = np.random.rand(dimension).astype('float32').reshape(1, dimension)
            
            # Search the index
            k = 5  # Number of results to retrieve
            distances, indices = index.search(query_vector, k)
            
            # Show results
            print(f"\nTop {k} results for random vector query:")
            for i, doc_idx in enumerate(indices[0]):
                if doc_idx < len(documents):
                    doc = documents[doc_idx]
                    print(f"\nResult {i+1} (Score: {distances[0][i]:.4f}):")
                    print(f"  - Source: {doc.metadata.get('source', 'Unknown')}")
                    print(f"  - Content preview: {doc.page_content[:100]}...")
            
            # Test with keyword search
            print("\n\nTesting keyword search:")
            keywords = ["Space", "AI", "client", "user", "platform"]
            for keyword in keywords:
                # Find documents containing the keyword
                matching_docs = []
                for i, doc in enumerate(documents):
                    if keyword.lower() in doc.page_content.lower():
                        matching_docs.append((i, doc))
                
                if matching_docs:
                    print(f"\nFound {len(matching_docs)} documents containing '{keyword}'")
                    # Show a sample
                    sample_idx = random.randint(0, len(matching_docs) - 1)
                    sample_doc = matching_docs[sample_idx][1]
                    print(f"Sample document from '{sample_doc.metadata.get('source', 'Unknown')}':")
                    # Find the keyword in context
                    content = sample_doc.page_content.lower()
                    keyword_pos = content.find(keyword.lower())
                    start = max(0, keyword_pos - 40)
                    end = min(len(content), keyword_pos + len(keyword) + 40)
                    context = "..." + content[start:end] + "..."
                    print(f"  Context: {context}")
                else:
                    print(f"\nNo documents found containing '{keyword}'")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return
    
    print("\nRAG database verification complete!")

if __name__ == "__main__":
    main()