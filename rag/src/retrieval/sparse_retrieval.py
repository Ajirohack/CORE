"""
Sparse Retrieval Module for RAG System
Implements BM25 retrieval for sparse keyword-based search
"""

import logging
from typing import Dict, List, Any, Optional, Union
import re
import numpy as np
import math
from collections import Counter, defaultdict

logger = logging.getLogger(__name__)

class SparseRetriever:
    """
    Sparse retrieval using BM25 algorithm for keyword-based document retrieval
    
    This implementation uses BM25 for term-based relevance scoring, which is effective
    for capturing exact keyword matches that semantic search might miss.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the sparse retriever
        
        Args:
            config: Configuration for the sparse retriever
        """
        self.config = config or {}
        
        # BM25 parameters
        self.k1 = self.config.get("bm25_k1", 1.5)  # Term frequency saturation
        self.b = self.config.get("bm25_b", 0.75)   # Document length normalization
        
        # Document store
        self.documents = {}  # doc_id -> document dict
        
        # Inverted index: term -> {doc_id -> term_freq}
        self.index = defaultdict(dict)
        
        # Document lengths
        self.doc_lengths = {}  # doc_id -> length
        self.avg_doc_length = 0
        self.total_docs = 0
        
        # Tokenization
        self.tokenizer = SimpleTokenizer()
        
        logger.info("Sparse retriever initialized with BM25")
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        """
        Add documents to the sparse index
        
        Args:
            documents: List of document dictionaries with 'content' and 'metadata'
        """
        logger.info(f"Adding {len(documents)} documents to sparse index")
        
        for doc in documents:
            doc_id = doc.get("id") or str(len(self.documents))
            content = doc.get("content", "")
            
            # Skip if already indexed
            if doc_id in self.documents:
                continue
            
            # Store document
            self.documents[doc_id] = doc.copy()
            
            # Tokenize and count terms
            tokens = self.tokenizer.tokenize(content)
            term_counts = Counter(tokens)
            
            # Update document length
            doc_length = len(tokens)
            self.doc_lengths[doc_id] = doc_length
            
            # Update inverted index
            for term, count in term_counts.items():
                self.index[term][doc_id] = count
            
            self.total_docs += 1
        
        # Update average document length
        if self.total_docs > 0:
            self.avg_doc_length = sum(self.doc_lengths.values()) / self.total_docs
    
    def search(self, query: str, k: int = 10) -> List[Dict[str, Any]]:
        """
        Search for documents using BM25 algorithm
        
        Args:
            query: The search query
            k: Number of results to return
            
        Returns:
            List of search results
        """
        logger.info(f"Performing sparse BM25 search for: {query[:50]}...")
        
        if not self.documents:
            logger.warning("No documents in sparse index")
            return []
        
        # Tokenize query
        query_tokens = self.tokenizer.tokenize(query)
        query_terms = Counter(query_tokens)
        
        # Score documents
        scores = defaultdict(float)
        
        for term, query_term_freq in query_terms.items():
            if term not in self.index:
                continue
                
            # Calculate IDF (Inverse Document Frequency)
            df = len(self.index[term])  # Document frequency
            idf = math.log((self.total_docs - df + 0.5) / (df + 0.5) + 1.0)
            
            # Score each document that contains this term
            for doc_id, term_freq in self.index[term].items():
                doc_length = self.doc_lengths[doc_id]
                
                # BM25 score formula
                numerator = term_freq * (self.k1 + 1)
                denominator = term_freq + self.k1 * (
                    1 - self.b + self.b * doc_length / self.avg_doc_length
                )
                
                term_score = idf * numerator / denominator
                scores[doc_id] += term_score
        
        # Sort by score
        sorted_doc_ids = sorted(
            scores.keys(),
            key=lambda x: scores[x],
            reverse=True
        )
        
        # Create result list
        results = []
        for doc_id in sorted_doc_ids[:k]:
            doc = self.documents[doc_id].copy()
            doc["score"] = scores[doc_id]
            results.append(doc)
        
        return results


class SimpleTokenizer:
    """
    Simple tokenizer for sparse retrieval
    
    Splits text into tokens, removes punctuation and converts to lowercase
    """
    
    def __init__(self):
        """Initialize tokenizer with basic stopwords"""
        self.stopwords = {
            "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
            "with", "by", "about", "as", "of", "from", "into", "after", "before"
        }
    
    def tokenize(self, text: str) -> List[str]:
        """
        Tokenize text into words, removing punctuation and stopwords
        
        Args:
            text: String to tokenize
            
        Returns:
            List of tokens
        """
        # Convert to lowercase
        text = text.lower()
        
        # Remove punctuation and split into words
        words = re.findall(r'\w+', text)
        
        # Filter stopwords
        tokens = [w for w in words if w not in self.stopwords and len(w) > 1]
        
        return tokens
