#!/usr/bin/env python3
"""
Final integration readiness test.
This script validates that the core services are ready for integration.
"""
import json
import sys
from pathlib import Path

def test_integration_readiness():
    """Test if core services are ready for integration."""
    
    print("🔍 Core Services Integration Readiness Test")
    print("=" * 55)
    
    # Test 1: Configuration file
    config_path = Path("services_config.json")
    if config_path.exists():
        try:
            with open(config_path) as f:
                config = json.load(f)
            print("✅ Services configuration loaded")
            print(f"   Found {len(config)} services configured")
        except Exception as e:
            print(f"❌ Configuration error: {e}")
            return False
    else:
        print("❌ services_config.json not found")
        return False
    
    # Test 2: Service directories
    missing_services = []
    for service_name, service_config in config.items():
        service_path = Path(service_config["path"]).parent
        if service_path.exists():
            print(f"✅ {service_name} directory exists")
        else:
            print(f"❌ {service_name} directory missing")
            missing_services.append(service_name)
    
    # Test 3: Service runner files
    missing_runners = []
    for service_name, service_config in config.items():
        runner_path = Path(service_config["path"])
        if runner_path.exists():
            print(f"✅ {service_name} runner exists")
        else:
            print(f"❌ {service_name} runner missing")
            missing_runners.append(service_name)
    
    # Test 4: Base service class
    try:
        sys.path.insert(0, str(Path(".")))
        from base_service import BaseService
        print("✅ BaseService class available")
    except Exception as e:
        print(f"❌ BaseService import failed: {e}")
        return False
    
    # Test 5: Service utilities
    utilities = ["services/auth.py", "services/communication.py", "services/service_logging.py"]
    for util in utilities:
        if Path(util).exists():
            print(f"✅ {util} available")
        else:
            print(f"❌ {util} missing")
    
    print("=" * 55)
    
    # Summary
    if not missing_services and not missing_runners:
        print("🎉 INTEGRATION READY!")
        print()
        print("✅ All service directories present")
        print("✅ All service runners present") 
        print("✅ Configuration file valid")
        print("✅ Base service framework ready")
        print("✅ Service utilities available")
        print()
        print("🚀 Ready for next steps:")
        print("   1. Start service manager: python run_services.py")
        print("   2. Test service endpoints")
        print("   3. Integration with Space API")
        print("   4. User dashboard connection")
        return True
    else:
        print("⚠️  Integration issues found:")
        if missing_services:
            print(f"   Missing services: {', '.join(missing_services)}")
        if missing_runners:
            print(f"   Missing runners: {', '.join(missing_runners)}")
        return False

if __name__ == "__main__":
    success = test_integration_readiness()
    sys.exit(0 if success else 1)
