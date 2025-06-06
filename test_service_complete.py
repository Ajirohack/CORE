#!/usr/bin/env python3
"""
Complete service test for all core services.
"""
import sys
from pathlib import Path

# Add core to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_service_initialization():
    """Test all services can initialize."""
    results = {}
    
    # Test Engines Service
    try:
        from engines.engines_service import EnginesService
        service = EnginesService()
        results['engines'] = {
            'status': 'success',
            'name': service.service_name,
            'version': service.service_version,
            'id': service.service_id
        }
    except Exception as e:
        results['engines'] = {'status': 'failed', 'error': str(e)}
    
    # Test Packages Service
    try:
        from packages.packages_service import PackagesService
        service = PackagesService()
        results['packages'] = {
            'status': 'success',
            'name': service.service_name,
            'version': service.service_version,
            'id': service.service_id
        }
    except Exception as e:
        results['packages'] = {'status': 'failed', 'error': str(e)}
    
    # Test LLM Council Service
    try:
        sys.path.insert(0, str(Path(__file__).parent / 'llm-council'))
        from llm_council_service import LLMCouncilService
        service = LLMCouncilService()
        results['llm-council'] = {
            'status': 'success',
            'name': service.service_name,
            'version': service.service_version,
            'id': service.service_id
        }
    except Exception as e:
        results['llm-council'] = {'status': 'failed', 'error': str(e)}
    
    # Test RAG Service
    try:
        from rag.rag_service import RAGService
        service = RAGService()
        results['rag'] = {
            'status': 'success',
            'name': service.service_name,
            'version': service.service_version,
            'id': service.service_id
        }
    except Exception as e:
        results['rag'] = {'status': 'failed', 'error': str(e)}
    
    return results

def main():
    """Run complete service tests."""
    print("Core Services Initialization Test")
    print("=" * 50)
    
    results = test_service_initialization()
    
    success_count = 0
    total_count = len(results)
    
    for service_name, result in results.items():
        if result['status'] == 'success':
            print(f"✅ {service_name.upper()} Service")
            print(f"   Name: {result['name']}")
            print(f"   Version: {result['version']}")
            print(f"   ID: {result['id']}")
            success_count += 1
        else:
            print(f"❌ {service_name.upper()} Service")
            print(f"   Error: {result['error']}")
        print()
    
    print("=" * 50)
    print(f"Results: {success_count}/{total_count} services initialized successfully")
    
    if success_count == total_count:
        print("🎉 All core services are working!")
        print("\nNext steps:")
        print("- Test service runners (FastAPI endpoints)")
        print("- Test service-to-service communication")
        print("- Integration with Space API")
    else:
        print("⚠️  Some services need attention")
    
    return success_count == total_count

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
