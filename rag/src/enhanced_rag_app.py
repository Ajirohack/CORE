#!/usr/bin/env python
"""
Enhanced RAG Application

This application provides a comprehensive interface to the RAG system with multiple LLM providers.
It sets up the necessary environment variables from the api_reference file and provides
a command-line and interactive interface to query the knowledge base.

Usage:
    python enhanced_rag_app.py --query "your question" --provider groq
    python enhanced_rag_app.py --interactive  # Start interactive mode
"""

import os
import sys
import argparse
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent))

# Import necessary modules
from config.rag_config import get_config
from core.rag_system.rag_system import RAGSystem
from core.rag_system.initialize_rag import initialize_rag_system
from core.rag_system.llm_integration import get_llm_provider

# Set up environment variables for API keys from api_reference
def setup_api_keys():
    """Configure environment variables for all LLM providers"""
    # Only set if not already set
    if not os.environ.get("GROQ_API_KEY"):
        os.environ["GROQ_API_KEY"] = "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"
        
    if not os.environ.get("OPENROUTER_API_KEY"):
        os.environ["OPENROUTER_API_KEY"] = "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"
        
    if not os.environ.get("GOOGLE_API_KEY"):
        os.environ["GOOGLE_API_KEY"] = "AIzaSyAWpkkOULORM_usfax9Hyb7EWRjJyto72w"
        
    if not os.environ.get("MISTRAL_API_KEY"):
        os.environ["MISTRAL_API_KEY"] = "sHZUS8HdhrFNODdsaxZH1xSckSn4ulXF"
        
    if not os.environ.get("COHERE_API_KEY"):
        os.environ["COHERE_API_KEY"] = "vDWl4kHEF8WND6m8gdCkEfttxeDsitrOEqXI90QE"
        
    if not os.environ.get("HUGGINGFACE_API_KEY"):
        os.environ["HUGGINGFACE_API_KEY"] = os.getenv("HUGGINGFACE_API_KEY", "")
        
    logger.info("API keys configured for all providers")


class EnhancedRAGApp:
    """Enhanced RAG Application with multi-provider support"""
    
    def __init__(self, environment: str = "development", initialize: bool = False):
        """
        Initialize the RAG application
        
        Args:
            environment: Configuration environment to use
            initialize: Whether to initialize the RAG system (index documents)
        """
        # Setup API keys
        setup_api_keys()
        
        # Get configuration
        self.config = get_config(environment)
        
        # Initialize or load RAG system
        if initialize:
            logger.info(f"Initializing RAG system with environment: {environment}")
            self.rag_system = initialize_rag_system(
                environment=environment,
                source_dir="data/knowledge",
                recursive=True,
                file_types=[".txt", ".md", ".pdf", ".csv", ".docx"],
                clean=True
            )
        else:
            logger.info(f"Loading existing RAG system with environment: {environment}")
            self.rag_system = RAGSystem(config=self.config)
            
        # Available LLM providers
        self.available_providers = [
            "groq",
            "openai",
            "anthropic",
            "ollama",
            "openrouter",
            "gemini",
            "mistral",
            "cohere"
        ]
        
        logger.info("Enhanced RAG Application initialized successfully")
    
    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """
        Search the knowledge base
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of search results
        """
        logger.info(f"Searching for: {query}")
        results = self.rag_system.search(query, k=k)
        return results
    
    def answer_question(
        self, 
        query: str, 
        provider: str = "groq",
        temperature: float = 0.0,
        search_results_count: int = 5
    ) -> Dict[str, Any]:
        """
        Answer a question using RAG and the specified LLM provider
        
        Args:
            query: Question to answer
            provider: LLM provider to use
            temperature: Temperature for response generation
            search_results_count: Number of search results to include
            
        Returns:
            Dictionary with answer, sources and other metadata
        """
        # Validate provider
        if provider not in self.available_providers:
            logger.warning(f"Provider {provider} not in available providers: {self.available_providers}")
            provider = "groq"  # Default to groq if provider not available
        
        logger.info(f"Answering question with provider: {provider}")
        
        try:
            # Get answer from the RAG system
            response = self.rag_system.answer_question(
                question=query,
                llm_provider=provider,
                temperature=temperature,
                max_tokens=1000,
                k=search_results_count
            )
            
            return response
        except Exception as e:
            logger.error(f"Error answering question: {str(e)}")
            return {
                "error": str(e),
                "answer": None,
                "sources": []
            }
    
    def run_interactive(self):
        """Run the RAG application in interactive mode"""
        print("\n===== Enhanced RAG Application =====")
        print("Enter 'exit' or 'quit' to exit.")
        print("Enter 'provider <name>' to change the LLM provider.")
        print(f"Available providers: {', '.join(self.available_providers)}")
        print("====================================\n")
        
        provider = "groq"  # Default provider
        
        while True:
            try:
                user_input = input(f"\n[{provider}] > ")
                
                if user_input.lower() in ["exit", "quit"]:
                    break
                
                # Change provider
                if user_input.lower().startswith("provider "):
                    new_provider = user_input.lower().split("provider ")[1].strip()
                    if new_provider in self.available_providers:
                        provider = new_provider
                        print(f"Provider changed to: {provider}")
                    else:
                        print(f"Invalid provider. Available providers: {', '.join(self.available_providers)}")
                    continue
                
                # Answer question
                print("\nSearching and generating answer...")
                response = self.answer_question(user_input, provider=provider)
                
                if "error" in response and response["error"]:
                    print(f"\nError: {response['error']}")
                    print("\nFalling back to search-only mode...")
                    
                    results = self.search(user_input)
                    print(f"\nFound {len(results)} documents\n")
                    
                    for i, result in enumerate(results):
                        print(f"Document {i+1}:")
                        print(f"Content: {result['content'][:300]}...")
                        if "metadata" in result and result["metadata"]:
                            print(f"Source: {result['metadata'].get('source', 'Unknown')}")
                        print()
                else:
                    print("\nAnswer:")
                    print(response.get("answer", "No answer generated"))
                    
                    if response.get("sources"):
                        print("\nSources:")
                        for source in response["sources"]:
                            print(f"- {source}")
            
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"Error: {str(e)}")


def main():
    """Main entry point for the application"""
    parser = argparse.ArgumentParser(description="Enhanced RAG Application")
    parser.add_argument(
        "--query", "-q",
        help="Question to answer"
    )
    parser.add_argument(
        "--provider", "-p",
        default="groq",
        choices=["groq", "openai", "anthropic", "ollama", "openrouter", "gemini", "mistral", "cohere"],
        help="LLM provider to use"
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Run in interactive mode"
    )
    parser.add_argument(
        "--initialize",
        action="store_true",
        help="Initialize the RAG system (index documents)"
    )
    parser.add_argument(
        "--env", "-e",
        choices=["development", "public_trial", "production"],
        default="development",
        help="Environment to use"
    )
    
    args = parser.parse_args()
    
    # Create RAG application
    app = EnhancedRAGApp(environment=args.env, initialize=args.initialize)
    
    if args.interactive:
        # Run in interactive mode
        app.run_interactive()
    elif args.query:
        # Answer single question
        response = app.answer_question(args.query, provider=args.provider)
        
        if "error" in response and response["error"]:
            print(f"\nError: {response['error']}")
            print("\nFalling back to search-only mode...")
            
            results = app.search(args.query)
            print(f"\nFound {len(results)} documents\n")
            
            for i, result in enumerate(results):
                print(f"Document {i+1}:")
                print(f"Content: {result['content'][:300]}...")
                if "metadata" in result and result["metadata"]:
                    print(f"Source: {result['metadata'].get('source', 'Unknown')}")
                print()
        else:
            print("\nQuestion:")
            print(args.query)
            
            print("\nAnswer:")
            print(response.get("answer", "No answer generated"))
            
            if response.get("sources"):
                print("\nSources:")
                for source in response["sources"]:
                    print(f"- {source}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()