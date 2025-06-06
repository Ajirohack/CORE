"""
RAG System Usage Example

This script demonstrates how to use the RAG system in an application:
1. Initialize the RAG system 
2. Search for information using natural language queries
3. Get context for LLM prompts

Usage:
    python rag_example.py --query "your search query" [--llm-provider openai|anthropic|ollama|openrouter|groq|openwebui]
"""

import os
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path to import our modules
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from config.rag_config import get_config
from core.rag_system.rag_system import RAGSystem
from core.rag_system.initialize_rag import initialize_rag_system
from core.rag_system.llm_integration import get_llm_provider, BaseLLMProvider


def search_knowledge_base(query: str, environment: str = "public_trial", k: int = 5) -> List[Dict[str, Any]]:
    """
    Search the knowledge base using the RAG system
    
    Args:
        query: The search query
        environment: Environment to use
        k: Number of results to return
        
    Returns:
        List of search results
    """
    # Get configuration and initialize RAG system
    config = get_config(environment)
    rag_system = RAGSystem(config=config)
    
    # Search for documents
    results = rag_system.search(query, k=k)
    
    return results


def get_answer_with_rag(query: str, environment: str = "public_trial", llm_provider: str = None) -> Dict[str, Any]:
    """
    Get an answer to a question using the RAG system and an LLM
    
    Args:
        query: The question to answer
        environment: Environment to use
        llm_provider: LLM provider to use (openai, anthropic, ollama, openrouter, groq, openwebui)
        
    Returns:
        Dictionary containing the answer and sources
    """
    # Get configuration and initialize RAG system
    config = get_config(environment)
    rag_system = RAGSystem(config=config)
    
    # Get context for the query
    context = rag_system.get_context_for_query(query, max_tokens=3000, k=5)
    
    # Initialize the LLM provider
    try:
        llm = get_llm_provider(llm_provider)
        
        # Get answer from LLM with context
        answer = llm.generate_with_context(
            prompt=query,
            context=context,
            system_message="You are a helpful assistant that answers questions based only on the provided context.",
            temperature=0.0,
            max_tokens=500
        )
        
    except ImportError as e:
        return {
            "error": f"Required package not installed: {str(e)}"
        }
    except Exception as e:
        return {
            "error": f"Error generating answer: {str(e)}"
        }
    
    # Extract sources from context
    sources = []
    for i, line in enumerate(context.split("\n")):
        if line.startswith("[Document ") and "Source:" in line:
            source = line.split("Source:")[1].strip().rstrip("]")
            sources.append(source)
    
    return {
        "query": query,
        "answer": answer,
        "sources": sources
    }


def main():
    """Command line interface for RAG example"""
    parser = argparse.ArgumentParser(description="RAG System Example")
    parser.add_argument(
        "--query", "-q",
        required=True,
        help="Search query or question"
    )
    parser.add_argument(
        "--env", "-e",
        choices=["development", "public_trial", "production"],
        default="development",
        help="Environment to use"
    )
    parser.add_argument(
        "--search-only",
        action="store_true",
        help="Only perform search without LLM response"
    )
    parser.add_argument(
        "--llm-provider",
        choices=["openai", "anthropic", "ollama", "openrouter", "groq", "openwebui"],
        default=os.environ.get("LLM_PROVIDER", "openai"),
        help="LLM provider to use for generating responses"
    )
    
    args = parser.parse_args()
    
    if args.search_only:
        # Just search for documents
        results = search_knowledge_base(args.query, args.env)
        
        print(f"\nSearch results for: {args.query}\n")
        print(f"Found {len(results)} documents\n")
        
        for i, result in enumerate(results):
            print(f"Document {i+1}:")
            print(f"Content: {result['content'][:300]}...")
            if "metadata" in result:
                print(f"Source: {result['metadata'].get('source', 'Unknown')}")
            print()
    else:
        # Get answer using RAG + LLM
        response = get_answer_with_rag(args.query, args.env, args.llm_provider)
        
        if "error" in response:
            print(f"\nError: {response['error']}")
            print("\nFalling back to search-only mode...\n")
            results = search_knowledge_base(args.query, args.env)
            
            print(f"Found {len(results)} documents\n")
            for i, result in enumerate(results):
                print(f"Document {i+1}:")
                print(f"Content: {result['content'][:300]}...")
                if "metadata" in result:
                    print(f"Source: {result['metadata'].get('source', 'Unknown')}")
                print()
        else:
            print(f"\nQuestion: {response['query']}\n")
            print(f"Answer: {response['answer']}\n")
            
            if response["sources"]:
                print("Sources:")
                for source in response["sources"]:
                    print(f"- {source}")


if __name__ == "__main__":
    main()