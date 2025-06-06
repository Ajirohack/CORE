# CORE - Space Project Core Services 🚀

A clean, modular microservices architecture for the Space project, providing independent services for workflow processing, multi-agent orchestration, tool execution, and retrieval-augmented generation.

## 🏗️ Architecture Overview

The CORE provides a foundation of independent services that communicate with the main Space API:

```
Space API (Main)
├── Engines Service (8001) - Workflow processing
├── LLM Council Service (8002) - Multi-agent orchestration  
├── Packages Service (8003) - Tool registry and execution
└── RAG Service (8004) - Retrieval-augmented generation
```

## ✨ Features

- **🔄 Independent Services**: Each service runs as a separate FastAPI application
- **🔧 Modular Design**: Easy to add, remove, or modify services
- **📡 Service Communication**: Standardized HTTP APIs between services
- **🔐 Authentication**: JWT-based service authentication
- **📊 Monitoring**: Health endpoints and structured logging
- **🐳 Container Ready**: Docker-friendly architecture
- **🧪 Comprehensive Testing**: Full test suite for all components

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- pip or conda for package management

### Installation

1. **Clone the repository:**

```bash
git clone https://github.com/Ajirohack/CORE.git
cd CORE
```

2. **Install dependencies:**

```bash
# Core dependencies
pip install -r requirements.txt

# Service-specific dependencies
pip install -r engines/requirements.txt
pip install -r packages/requirements.txt
pip install -r llm-council/requirements.txt
pip install -r rag/requirements.txt
```

3. **Start all services:**

```bash
python run_services.py
```

### Alternative: Start Individual Services

```bash
# Terminal 1 - Engines Service
python engines/run_engines.py

# Terminal 2 - LLM Council Service  
python llm-council/run_council.py

# Terminal 3 - Packages Service
python packages/run_packages.py

# Terminal 4 - RAG Service
python rag/run_rag.py
```

## 🔍 Service Details

### 🔧 Engines Service (Port 8001)

- **Purpose**: Pluggable workflow processing engines
- **Endpoints**: `/health`, `/api/v1/engines/process`
- **Features**: Custom workflow execution, engine registry

### 🤖 LLM Council Service (Port 8002)

- **Purpose**: Multi-agent orchestration and specialist reasoning
- **Endpoints**: `/health`, `/api/v1/council/process`
- **Features**: Agent coordination, specialist prompts, collaborative decision-making

### 📦 Packages Service (Port 8003)

- **Purpose**: Tool registry and execution system
- **Endpoints**: `/health`, `/api/v1/packages/process`
- **Features**: Tool management, execution environment, access control

### 🔍 RAG Service (Port 8004)

- **Purpose**: Retrieval-Augmented Generation with multi-modal storage
- **Endpoints**: `/health`, `/api/v1/rag/process`
- **Features**: Vector storage, knowledge retrieval, multi-modal support

## 🧪 Testing

### Run All Tests

```bash
# Basic import tests
python test_basic_imports.py

# Service initialization tests
python test_service_init.py

# Integration readiness tests
python test_integration_ready.py

# Production readiness check
python production_readiness.py
```

### Health Checks

```bash
# Check all services are running
curl http://localhost:8001/health  # Engines
curl http://localhost:8002/health  # LLM Council
curl http://localhost:8003/health  # Packages
curl http://localhost:8004/health  # RAG
```

## 📁 Project Structure

```
CORE/
├── base_service.py              # Base service class
├── run_services.py              # Service orchestrator
├── services_config.json         # Service configuration
├── requirements.txt             # Core dependencies
├── services/                    # Shared utilities
│   ├── auth.py                 # Authentication utilities
│   ├── communication.py        # Service communication
│   └── service_logging.py      # Structured logging
├── engines/                     # Engines service
│   ├── engines_service.py
│   ├── run_engines.py
│   └── requirements.txt
├── llm-council/                 # LLM Council service
│   ├── llm_council_service.py
│   ├── run_council.py
│   └── requirements.txt
├── packages/                    # Packages service
│   ├── packages_service.py
│   ├── run_packages.py
│   └── requirements.txt
├── rag/                        # RAG service
│   ├── rag_service.py
│   ├── run_rag.py
│   ├── requirements.txt
│   └── src/                    # RAG implementation
└── archived_archivist_components/ # Legacy components
```

## ⚙️ Configuration

Edit `services_config.json` to customize:

- Service ports
- Enable/disable services  
- API endpoints
- Service descriptions

Example configuration:

```json
{
  "engines": {
    "port": 8001,
    "enabled": true,
    "description": "Workflow processing engines"
  }
}
```

## 🔧 Development

### Adding a New Service

1. Create service directory: `mkdir new-service`
2. Implement service class extending `BaseService`
3. Create FastAPI runner: `new-service/run_new_service.py`
4. Add to `services_config.json`
5. Update service manager in `run_services.py`

### Service Interface

All services inherit from `BaseService` and provide:

- Health endpoints
- Standardized request/response format
- Authentication integration
- Structured logging

## 🐳 Docker Support

```dockerfile
# Example Dockerfile for a service
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "run_services.py"]
```

## 📊 Monitoring & Logging

- **Health Endpoints**: `/health` on each service
- **Structured Logging**: JSON format with correlation IDs
- **Service Registry**: Automatic service discovery
- **Error Handling**: Comprehensive error tracking

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Make your changes
4. Add tests for new functionality
5. Run the test suite: `python test_basic_imports.py`
6. Commit your changes: `git commit -m "Add new feature"`
7. Push to the branch: `git push origin feature/new-feature`
8. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: See `QUICK_START.md` and `CORE_STATUS_REPORT.md`
- **Issues**: Submit issues on GitHub
- **Discussions**: Use GitHub Discussions for questions

## 🎉 Acknowledgments

- Built with FastAPI for high-performance APIs
- Modular architecture inspired by microservices patterns
- Independent service design for scalability and maintainability

---

**Ready to build the future of AI orchestration!** 🚀
