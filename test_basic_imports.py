#!/usr/bin/env python3
"""
Basic import test for core services.
Tests if services can be imported without heavy dependencies.
"""
import sys
from pathlib import Path

# Add core to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_base_service():
    """Test BaseService import."""
    try:
        from base_service import BaseService
        print("✅ BaseService import: OK")
        return True
    except Exception as e:
        print(f"❌ BaseService import: {e}")
        return False

def test_engines_service():
    """Test Engines service import."""
    try:
        from engines.engines_service import EnginesService
        print("✅ EnginesService import: OK")
        return True
    except Exception as e:
        print(f"❌ EnginesService import: {e}")
        return False

def test_packages_service():
    """Test Packages service import."""
    try:
        from packages.packages_service import PackagesService
        print("✅ PackagesService import: OK")
        return True
    except Exception as e:
        print(f"❌ PackagesService import: {e}")
        return False

def test_llm_council_service():
    """Test LLM Council service import."""
    try:
        # Try the hyphenated directory first
        sys.path.insert(0, str(Path(__file__).parent / "llm-council"))
        from llm_council_service import LLMCouncilService
        print("✅ LLMCouncilService import: OK")
        return True
    except Exception as e:
        print(f"❌ LLMCouncilService import: {e}")
        return False

def test_rag_service():
    """Test RAG service import."""
    try:
        from rag.rag_service import RAGService
        print("✅ RAGService import: OK")
        return True
    except Exception as e:
        print(f"❌ RAGService import: {e}")
        return False

def main():
    """Run all import tests."""
    print("Running basic import tests for core services...")
    print("=" * 50)
    
    tests = [
        test_base_service,
        test_engines_service,
        test_packages_service,
        test_llm_council_service,
        test_rag_service
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("=" * 50)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All services can be imported successfully!")
    else:
        print("⚠️  Some services have import issues")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
