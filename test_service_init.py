#!/usr/bin/env python3
"""
Service initialization test for core services.
Tests if services can be initialized without crashing.
"""
import sys
from pathlib import Path

# Add core to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_service_initialization():
    """Test service initialization."""
    print("Testing service initialization...")
    print("=" * 50)
    
    results = {}
    
    # Test BaseService
    try:
        from base_service import BaseService
        # BaseService is abstract, so we can't instantiate it directly
        print("✅ BaseService: Abstract class loaded OK")
        results['BaseService'] = True
    except Exception as e:
        print(f"❌ BaseService: {e}")
        results['BaseService'] = False
    
    # Test EnginesService
    try:
        from engines.engines_service import EnginesService
        service = EnginesService()
        print("✅ EnginesService: Initialized OK")
        results['EnginesService'] = True
    except Exception as e:
        print(f"❌ EnginesService: {e}")
        results['EnginesService'] = False
    
    # Test PackagesService
    try:
        from packages.packages_service import PackagesService
        service = PackagesService()
        print("✅ PackagesService: Initialized OK")
        results['PackagesService'] = True
    except Exception as e:
        print(f"❌ PackagesService: {e}")
        results['PackagesService'] = False
    
    # Test LLMCouncilService
    try:
        sys.path.insert(0, str(Path(__file__).parent / "llm-council"))
        from llm_council_service import LLMCouncilService
        service = LLMCouncilService()
        print("✅ LLMCouncilService: Initialized OK")
        results['LLMCouncilService'] = True
    except Exception as e:
        print(f"❌ LLMCouncilService: {e}")
        results['LLMCouncilService'] = False
    
    # Test RAGService
    try:
        from rag.rag_service import RAGService
        service = RAGService()
        print("✅ RAGService: Initialized OK")
        results['RAGService'] = True
    except Exception as e:
        print(f"❌ RAGService: {e}")
        results['RAGService'] = False
    
    print("=" * 50)
    passed = sum(results.values())
    total = len(results)
    print(f"Results: {passed}/{total} services initialized successfully")
    
    if passed == total:
        print("🎉 All services initialized successfully!")
    else:
        print("⚠️  Some services have initialization issues")
        for service, success in results.items():
            if not success:
                print(f"   - {service}: Failed")
    
    return passed == total

if __name__ == "__main__":
    success = test_service_initialization()
    sys.exit(0 if success else 1)
