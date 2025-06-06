# Core Services - Quick Start Guide

## 🚀 Starting All Services

### Option 1: Service Manager (Recommended)
```bash
cd "/Volumes/Project Disk/Project Z - The New Era/core"
python run_services.py
```

### Option 2: Individual Services
```bash
# Terminal 1 - Engines Service
cd "/Volumes/Project Disk/Project Z - The New Era/core"
python engines/run_engines.py

# Terminal 2 - LLM Council Service  
cd "/Volumes/Project Disk/Project Z - The New Era/core"
python llm-council/run_council.py

# Terminal 3 - Packages Service
cd "/Volumes/Project Disk/Project Z - The New Era/core"  
python packages/run_packages.py

# Terminal 4 - RAG Service
cd "/Volumes/Project Disk/Project Z - The New Era/core"
python rag/run_rag.py
```

## 🔍 Testing Service Health

After starting services, test health endpoints:

```bash
# Engines Service
curl http://localhost:8001/health

# LLM Council Service
curl http://localhost:8002/health

# Packages Service
curl http://localhost:8003/health

# RAG Service
curl http://localhost:8004/health
```

## 📊 Service URLs

- **Engines Service**: http://localhost:8001
  - Health: `/health`
  - API: `/api/v1/engines/process`
  - Docs: `/docs`

- **LLM Council Service**: http://localhost:8002
  - Health: `/health`
  - API: `/api/v1/council/process`
  - Docs: `/docs`

- **Packages Service**: http://localhost:8003
  - Health: `/health`
  - API: `/api/v1/packages/process`
  - Docs: `/docs`

- **RAG Service**: http://localhost:8004
  - Health: `/health`
  - API: `/api/v1/rag/process`
  - Docs: `/docs`

## 🛠️ Development Commands

### Run Tests
```bash
# Basic import tests
python test_basic_imports.py

# Integration readiness
python test_integration_ready.py

# Production readiness check
python production_readiness.py
```

### Install Dependencies
```bash
# Core dependencies
pip install -r requirements.txt

# Service-specific dependencies
pip install -r engines/requirements.txt
pip install -r packages/requirements.txt
pip install -r llm-council/requirements.txt
pip install -r rag/requirements.txt
```

## 🔧 Configuration

Edit `services_config.json` to modify:
- Service ports
- Enable/disable services
- Service paths
- API endpoints

## 🚀 Integration Steps

1. **Start Services**: Use service manager or individual runners
2. **Verify Health**: Check all health endpoints respond
3. **Test APIs**: Send test requests to service endpoints
4. **Space API Integration**: Connect services to main Space API
5. **Dashboard Integration**: Connect user dashboard to services

## 📁 Key Files

- `base_service.py` - Base service class
- `run_services.py` - Service manager
- `services_config.json` - Service configuration
- `services/` - Shared utilities (auth, communication, logging)
- `CORE_STATUS_REPORT.md` - Complete status report
