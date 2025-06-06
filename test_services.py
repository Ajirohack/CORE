#!/usr/bin/env python3
"""
Test script to verify core services structure and imports.
"""
import sys
from pathlib import Path

# Add core to Python path
core_path = Path(__file__).parent
sys.path.insert(0, str(core_path))

def test_imports():
    """Test that all services can be imported"""
    print("Testing core services imports...")
    
    try:
        # Test base service import
        from base_service import BaseService, ServiceRequest, ServiceResponse
        print("✅ BaseService imported successfully")
        
        # Test service utilities
        from services.auth import ServiceAuth
        from services.communication import ServiceCommunication 
        from services.logging import ServiceLogger
        print("✅ Service utilities imported successfully")
        
        # Test engines service
        from engines.engines_service import EnginesService
        print("✅ EnginesService imported successfully")
        
        # Test llm-council service
        from llm_council.llm_council_service import LLMCouncilService
        print("✅ LLMCouncilService imported successfully")
        
        # Test packages service
        from packages.packages_service import PackagesService
        print("✅ PackagesService imported successfully")
        
        # Test rag service
        from rag.rag_service import RAGService
        print("✅ RAGService imported successfully")
        
        print("\n🎉 All imports successful!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_service_instantiation():
    """Test that services can be instantiated"""
    print("\nTesting service instantiation...")
    
    try:
        config = {
            'space_api_url': 'http://localhost:8000',
            'log_level': 'INFO'
        }
        
        # Test each service
        engines = EnginesService(config)
        print("✅ EnginesService instantiated")
        
        council = LLMCouncilService(config)  
        print("✅ LLMCouncilService instantiated")
        
        packages = PackagesService(config)
        print("✅ PackagesService instantiated")
        
        rag = RAGService(config)
        print("✅ RAGService instantiated")
        
        print("\n🎉 All services instantiated successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Instantiation error: {e}")
        return False

def test_service_info():
    """Test that services provide correct info"""
    print("\nTesting service information...")
    
    try:
        config = {'space_api_url': 'http://localhost:8000'}
        
        services = [
            ("engines", EnginesService(config)),
            ("llm-council", LLMCouncilService(config)),
            ("packages", PackagesService(config)),
            ("rag", RAGService(config))
        ]
        
        for name, service in services:
            info = service.service_info
            print(f"✅ {name}: {info.name} v{info.version}")
            print(f"   Description: {info.description}")
            print(f"   Capabilities: {len(info.capabilities)} items")
            print(f"   Endpoints: {len(info.endpoints)} endpoints")
        
        print("\n🎉 All service info retrieved successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Service info error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Core Services Structure Test\n")
    
    success = True
    success &= test_imports()
    success &= test_service_instantiation() 
    success &= test_service_info()
    
    if success:
        print("\n✅ All tests passed! Core services structure is ready.")
        return 0
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    # Import the required modules for testing
    from engines.engines_service import EnginesService
    from llm_council.llm_council_service import LLMCouncilService
    from packages.packages_service import PackagesService
    from rag.rag_service import RAGService
    
    sys.exit(main())
