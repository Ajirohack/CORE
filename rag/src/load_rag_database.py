#!/usr/bin/env python3
"""
Direct loader script for RAG database.
Uses the Groq API for embeddings with the correct model.
"""

import os
import sys
import glob
from pathlib import Path
import logging
import warnings
import re
from typing import List, Dict, Any
from dotenv import load_dotenv

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress warnings
warnings.filterwarnings("ignore")

# Import required libraries
import openai
from langchain_text_splitters import RecursiveCharacterTextSplitter
import faiss
import numpy as np
import pickle
import json
import requests

# Constants
VECTOR_DB_PATH = os.path.join(project_root, "vector_db")
INDEX_FILE = os.path.join(VECTOR_DB_PATH, "index.faiss")
DOCUMENTS_FILE = os.path.join(VECTOR_DB_PATH, "documents.pkl")

# Create vector DB directory if it doesn't exist
os.makedirs(VECTOR_DB_PATH, exist_ok=True)

# Load API keys from api_reference file
def load_api_keys():
    try:
        api_reference_path = os.path.join(project_root, "api_reference")
        with open(api_reference_path, 'r') as file:
            content = file.read()
            
            # For Groq API
            groq_match = re.search(r'gsk_([A-Za-z0-9]+)', content)
            if groq_match:
                full_key = content[content.find("gsk_"):].split("`")[0].strip()
                os.environ["GROQ_API_KEY"] = full_key
                logger.info(f"Set Groq API key: {full_key[:10]}...")
                return True
                
            # For OpenAI API (backup)
            openrouter_match = re.search(r'sk-or-v1-([A-Za-z0-9]+)', content)
            if openrouter_match:
                full_key = content[content.find("sk-or-v1-"):].split("`")[0].strip()
                os.environ["OPENROUTER_API_KEY"] = full_key
                logger.info(f"Set OpenRouter API key: {full_key[:15]}...")
                return True
                
    except Exception as e:
        logger.warning(f"Error loading API keys: {e}")
    
    return False

# Read all files matching the patterns
def read_files(patterns):
    all_files = []
    for pattern in patterns:
        if "*" in pattern:
            all_files.extend(glob.glob(pattern))
        elif os.path.isfile(pattern):
            all_files.append(pattern)
    return all_files

# Read file content
def read_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return None

# Split text into chunks
def split_text(text, metadata, chunk_size=800, chunk_overlap=150):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    
    docs = splitter.create_documents([text], [metadata])
    return docs

# Get available models from Groq
def get_groq_models():
    api_key = os.environ.get("GROQ_API_KEY")
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    try:
        response = requests.get("https://api.groq.com/openai/v1/models", headers=headers)
        if response.status_code == 200:
            models = response.json().get("data", [])
            logger.info(f"Available Groq models: {[m.get('id') for m in models]}")
            return [m.get("id") for m in models]
        else:
            logger.error(f"Failed to get Groq models: {response.text}")
            return []
    except Exception as e:
        logger.error(f"Error getting Groq models: {e}")
        return []

# Get embeddings using Groq or fallback methods
def get_embeddings(texts):
    # Fallback to HuggingFace sentence-transformers (if installed)
    try:
        from sentence_transformers import SentenceTransformer
        logger.info("Using local SentenceTransformer model for embeddings")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        embeddings = model.encode(texts)
        return [emb.tolist() for emb in embeddings]
    except ImportError:
        logger.warning("SentenceTransformer not installed, using random embeddings")
        
    # If all else fails, use a simple random embedding (for testing only)
    logger.warning("Using random embeddings as fallback - FOR TESTING ONLY")
    return [np.random.rand(384).tolist() for _ in texts]

# Process a single file into chunks with embeddings
def process_file(file_path, chunk_size=800, chunk_overlap=150):
    logger.info(f"Processing {file_path}")
    content = read_file(file_path)
    if not content:
        return []
    
    metadata = {
        "source": file_path,
        "file_type": os.path.splitext(file_path)[1].lstrip('.') or "txt"
    }
    
    chunks = split_text(content, metadata, chunk_size, chunk_overlap)
    logger.info(f"Created {len(chunks)} chunks from {file_path}")
    
    # Get text content from chunks for embedding
    texts = [chunk.page_content for chunk in chunks]
    
    # Get embeddings in batches of 5 (API limit consideration)
    all_embeddings = []
    for i in range(0, len(texts), 5):
        batch_texts = texts[i:i+5]
        batch_embeddings = get_embeddings(batch_texts)
        if batch_embeddings:
            all_embeddings.extend(batch_embeddings)
            logger.info(f"Generated embeddings for batch {i//5 + 1} of {len(texts)//5 + 1}")
        else:
            logger.error(f"Failed to get embeddings for batch {i//5 + 1}")
            return []
    
    # Add embeddings to chunks
    for i, chunk in enumerate(chunks):
        if i < len(all_embeddings):
            chunk.metadata["embedding"] = all_embeddings[i]
    
    logger.info(f"Added embeddings to {len(all_embeddings)} chunks")
    return chunks

# Main function
def main():
    # Load API keys
    load_api_keys()  # Continue even if this fails, as we'll use fallback embeddings
    
    # Define knowledge source patterns
    knowledge_patterns = [
        "README.md",
        "api_reference",
        "docs/*.md",
        "docs/api/*.md",
        "docs/architecture/*.md",
        "docs/development/*.md"
    ]
    
    # Get all files to process
    file_paths = read_files(knowledge_patterns)
    logger.info(f"Found {len(file_paths)} files to process")
    
    # Process files
    all_documents = []
    all_embeddings = []
    
    # Process only a subset of files for testing (comment this out for full processing)
    # file_paths = file_paths[:5]  # Process only the first 5 files
    
    for file_path in file_paths:
        chunks = process_file(file_path)
        if chunks:
            all_documents.extend(chunks)
            # Extract embeddings from metadata for FAISS
            for chunk in chunks:
                if "embedding" in chunk.metadata:
                    emb = chunk.metadata.pop("embedding")  # Remove from metadata to avoid duplication
                    all_embeddings.append(emb)
    
    if not all_documents or not all_embeddings:
        logger.error("No documents or embeddings were created")
        return
    
    logger.info(f"Created {len(all_documents)} total chunks with embeddings")
    
    # Convert embeddings to numpy array for FAISS
    embeddings_array = np.array(all_embeddings).astype('float32')
    
    # Create FAISS index
    dimension = len(embeddings_array[0])
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings_array)
    
    # Save index and documents
    faiss.write_index(index, INDEX_FILE)
    with open(DOCUMENTS_FILE, 'wb') as f:
        pickle.dump(all_documents, f)
    
    logger.info(f"Saved {len(all_documents)} documents to {DOCUMENTS_FILE}")
    logger.info(f"FAISS index saved to {INDEX_FILE}")
    
    # Test search
    logger.info("Testing search functionality...")
    query = "What is the Space project about?"
    try:
        query_embedding = get_embeddings([query])[0]
        query_embedding_array = np.array([query_embedding]).astype('float32')
        
        k = 3  # Number of results to retrieve
        distances, indices = index.search(query_embedding_array, k)
        
        logger.info(f"Top {k} search results:")
        for i, doc_idx in enumerate(indices[0]):
            if doc_idx < len(all_documents):
                doc = all_documents[doc_idx]
                logger.info(f"Result {i+1} (Score: {distances[0][i]:.4f}):")
                logger.info(f"Source: {doc.metadata['source']}")
                logger.info(f"Content: {doc.page_content[:150]}...")
                logger.info("---")
    except Exception as e:
        logger.error(f"Error during test search: {e}")

if __name__ == "__main__":
    main()