#!/usr/bin/env python3
"""
RAG System Functionality Test Script

This script tests the core functionality of the RAG system including:
- Document processing and indexing
- Vector store operations
- Search and retrieval
- Question answering with different LLM providers
"""

import os
import sys
import logging
import argparse
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent))

# Import RAG system components
from config.rag_config import get_config
from core.rag_system.rag_system import RAGSystem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("test_output.log", mode="w")
    ]
)
logger = logging.getLogger("rag-test")

# Test document content
TEST_DOCUMENT = """
# Space Project Knowledge Repository

## Membership Registration Process

The Space WH membership registration process consists of the following steps:
1. User completes the initial signup form on the landing page
2. System sends a verification email to the user
3. User verifies their email by clicking the link
4. User is directed to the onboarding questionnaire
5. After completing the questionnaire, the user selects a membership tier
6. Payment information is collected for paid tiers
7. User receives access to their dashboard
8. A welcome message is sent with next steps

## Main Features

The Space platform offers these core features:
- Interactive knowledge base with RAG capabilities
- AI-powered document analysis
- Collaboration tools for team projects
- Resource scheduling and management
- Integration with external tools and services
"""

def test_document_processing(rag_system):
    """Test document processing functionality"""
    logger.info("Testing document processing...")
    
    # Process test document
    doc_ids = rag_system.process_and_add_text(
        TEST_DOCUMENT,
        metadata={"source": "test_document", "title": "Space Project Test"}
    )
    
    if not doc_ids:
        logger.error("❌ Document processing failed: No document IDs returned")
        return False
    
    logger.info(f"✅ Document processing successful: {len(doc_ids)} chunks created")
    return doc_ids

def test_search_functionality(rag_system, doc_ids):
    """Test search functionality"""
    logger.info("Testing search functionality...")
    
    # Test queries
    test_queries = [
        "What is the membership registration process?",
        "What are the main features of Space platform?",
        "How does the onboarding process work?",
    ]
    
    success = True
    for query in test_queries:
        results = rag_system.search(query, k=2)
        
        if not results:
            logger.error(f"❌ Search failed for query: {query}")
            success = False
            continue
            
        logger.info(f"Query: {query}")
        logger.info(f"Found {len(results)} results")
        for i, result in enumerate(results):
            logger.info(f"Result {i+1}: {result['content'][:100]}...")
    
    if success:
        logger.info("✅ Search functionality test successful")
    return success

def test_qa_functionality(rag_system, llm_provider="groq"):
    """Test question answering functionality with a specified LLM provider"""
    logger.info(f"Testing QA functionality with {llm_provider}...")
    
    # Test questions
    test_questions = [
        "What is the process for membership registration?",
        "What features does the Space platform offer?",
        "How does the Space WH onboarding work?"
    ]
    
    success = True
    for question in test_questions:
        try:
            logger.info(f"Question: {question}")
            response = rag_system.answer_question(
                question=question,
                llm_provider=llm_provider,
                temperature=0.0
            )
            
            if "error" in response:
                logger.error(f"❌ QA failed for question: {question}")
                logger.error(f"Error: {response['error']}")
                success = False
                continue
                
            logger.info(f"Answer: {response['answer']}")
            logger.info(f"Sources: {response['sources']}")
            
        except Exception as e:
            logger.error(f"❌ Exception while generating answer: {str(e)}")
            success = False
    
    if success:
        logger.info(f"✅ QA functionality test with {llm_provider} successful")
    return success

def cleanup_test_data(rag_system, doc_ids):
    """Clean up test data from vector store"""
    logger.info("Cleaning up test data...")
    
    try:
        rag_system.delete_documents(doc_ids)
        logger.info("✅ Test data cleanup successful")
        return True
    except Exception as e:
        logger.error(f"❌ Test data cleanup failed: {str(e)}")
        return False

def main():
    """Main test execution function"""
    parser = argparse.ArgumentParser(description="Test RAG System functionality")
    parser.add_argument("--provider", type=str, default="groq", 
                        help="LLM provider to test (default: groq)")
    parser.add_argument("--config", type=str, default="development",
                       help="Configuration to use (default: development)")
    parser.add_argument("--cleanup", action="store_true",
                       help="Clean up test data after running tests")
    args = parser.parse_args()
    
    logger.info(f"Starting RAG system tests with {args.provider} provider and {args.config} configuration")
    
    # Get configuration
    config = get_config(args.config)
    
    # Ensure config uses the specified provider
    if "llm" in config:
        config["llm"]["provider"] = args.provider
    
    # Initialize RAG system
    try:
        logger.info("Initializing RAG system...")
        rag_system = RAGSystem(config=config)
        logger.info("RAG system initialized")
    except Exception as e:
        logger.error(f"Failed to initialize RAG system: {str(e)}")
        return 1
    
    # Run tests
    test_results = {
        "document_processing": False,
        "search": False,
        "qa": False,
        "cleanup": True  # Default to True if cleanup not performed
    }
    
    # Test document processing
    doc_ids = test_document_processing(rag_system)
    test_results["document_processing"] = bool(doc_ids)
    
    if doc_ids:
        # Test search functionality
        test_results["search"] = test_search_functionality(rag_system, doc_ids)
        
        # Test QA functionality with specified provider
        test_results["qa"] = test_qa_functionality(rag_system, args.provider)
        
        # Cleanup test data if requested
        if args.cleanup:
            test_results["cleanup"] = cleanup_test_data(rag_system, doc_ids)
    
    # Print test summary
    logger.info("\n--- Test Results Summary ---")
    all_passed = True
    for test_name, result in test_results.items():
        status = "PASSED" if result else "FAILED"
        if not result:
            all_passed = False
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nOverall test status: {'PASSED' if all_passed else 'FAILED'}")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())