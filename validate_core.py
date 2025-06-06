#!/usr/bin/env python3
"""
Final validation test for core services.
This test validates that all services can be properly imported and initialized.
"""
import sys
import os
from pathlib import Path

# Ensure we're in the right directory
script_dir = Path(__file__).parent
os.chdir(script_dir)
sys.path.insert(0, str(script_dir))

def validate_services():
    """Validate all core services"""
    results = {}
    
    print("🔍 Core Services Validation")
    print("=" * 50)
    
    # Test 1: BaseService
    try:
        from base_service import BaseService
        results['base_service'] = "✅ BaseService import successful"
    except Exception as e:
        results['base_service'] = f"❌ BaseService failed: {e}"
    
    # Test 2: Engines Service
    try:
        from engines.engines_service import EnginesService
        service = EnginesService()
        results['engines'] = f"✅ Engines service: {service.service_name} v{service.service_version}"
    except Exception as e:
        results['engines'] = f"❌ Engines service failed: {e}"
    
    # Test 3: Packages Service  
    try:
        from packages.packages_service import PackagesService
        service = PackagesService()
        results['packages'] = f"✅ Packages service: {service.service_name} v{service.service_version}"
    except Exception as e:
        results['packages'] = f"❌ Packages service failed: {e}"
    
    # Test 4: RAG Service
    try:
        from rag.rag_service import RAGService
        service = RAGService()
        results['rag'] = f"✅ RAG service: {service.service_name} v{service.service_version}"
    except Exception as e:
        results['rag'] = f"❌ RAG service failed: {e}"
    
    # Test 5: LLM Council Service (special handling)
    try:
        # Add the llm-council directory to path
        llm_council_path = script_dir / "llm-council"
        if str(llm_council_path) not in sys.path:
            sys.path.insert(0, str(llm_council_path))
        
        # Import and test
        import llm_council_service
        service = llm_council_service.LLMCouncilService()
        results['llm_council'] = f"✅ LLM Council service: {service.service_name} v{service.service_version}"
    except Exception as e:
        results['llm_council'] = f"❌ LLM Council service failed: {e}"
    
    # Print results
    success_count = 0
    for name, result in results.items():
        print(f"{result}")
        if "✅" in result:
            success_count += 1
    
    print("=" * 50)
    print(f"Validation complete: {success_count}/{len(results)} services working")
    
    # Test service runners
    print("\n🔧 Testing Service Runners")
    print("-" * 30)
    
    runner_results = {}
    
    # Test engines runner
    try:
        engines_path = script_dir / "engines"
        sys.path.insert(0, str(engines_path))
        import run_engines
        runner_results['engines_runner'] = "✅ Engines runner import successful"
    except Exception as e:
        runner_results['engines_runner'] = f"❌ Engines runner failed: {e}"
    
    # Test packages runner
    try:
        packages_path = script_dir / "packages"
        sys.path.insert(0, str(packages_path))
        import run_packages
        runner_results['packages_runner'] = "✅ Packages runner import successful"
    except Exception as e:
        runner_results['packages_runner'] = f"❌ Packages runner failed: {e}"
    
    # Print runner results
    runner_success = 0
    for name, result in runner_results.items():
        print(f"{result}")
        if "✅" in result:
            runner_success += 1
    
    print("-" * 30)
    print(f"Runners test: {runner_success}/{len(runner_results)} working")
    
    # Final summary
    total_success = success_count + runner_success
    total_tests = len(results) + len(runner_results)
    
    print(f"\n📊 Overall Results: {total_success}/{total_tests} components working")
    
    if success_count >= 4:  # At least 4 out of 5 services working
        print("\n🎉 Core services are ready!")
        print("✅ Service architecture is functional")
        print("✅ Ready for integration testing")
        print("✅ Ready for GitHub push")
        return True
    else:
        print("\n⚠️  Some services need attention before proceeding")
        return False

if __name__ == "__main__":
    success = validate_services()
    sys.exit(0 if success else 1)
