# Start /Run Script

---

```bash
#!/bin/bash

# Superior RAG System Start Script
# This script starts all the required services and the API server

set -e  # Exit on any error

# Print colorful messages
function print_header() {
    echo -e "\033[1;36m$1\033[0m"
}

function print_success() {
    echo -e "\033[1;32m$1\033[0m"
}

function print_error() {
    echo -e "\033[1;31m$1\033[0m"
}

function print_warning() {
    echo -e "\033[1;33m$1\033[0m"
}

# Ensure we're in the project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
cd "$SCRIPT_DIR/.."

# Check if .env file exists
if [ ! -f .env ]; then
    print_warning "No .env file found. Please run setup.sh first."
    exit 1
fi

# Source the .env file to get environment variables
set -a  # Automatically export all variables
source .env
set +a

# Check if Docker services are running
print_header "Checking Docker services..."
if ! docker ps | grep -q "superior-rag_qdrant"; then
    print_warning "Docker services not running. Starting them now..."
    docker-compose -f docker/docker-compose.yml up -d
    sleep 5
    print_success "Docker services started."
else
    print_success "Docker services are already running."
fi

# Start the API server
print_header "Starting the Superior RAG API server..."

# Check if port 8000 is already in use
if lsof -Pi :8000 -sT#!/bin/bash

# Superior RAG System Start Script
# This script starts all the required services and the API server

set -e  # Exit on any error

# Print colorful messages
function print_header() {
    echo -e "\033[1;36m$1\033[0m"
}

function print_success() {
    echo -e "\033[1;32m$1\033[0m"
}

function print_error() {
    echo -e "\033[1;31m$1\033[0m"
}

function print_warning() {
    echo -e "\033[1;33m$1\033[0m"
}

# Ensure we're in the project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
cd "$SCRIPT_DIR/.."

# Check if .env file exists
if [ ! -f .env ]; then
    print_warning "No .env file found. Please run setup.sh first."
    exit 1
fi

# Source the .env file to get environment variables
set -a  # Automatically export all variables
source .env
set +a

# Check if Docker services are running
print_header "Checking Docker services..."
if ! docker ps | grep -q "superior-rag_qdrant"; then
    print_warning "Docker services not running. Starting them now..."
    docker-compose -f docker/docker-compose.yml up -d
    sleep 5
    print_success "Docker services started."
else
    print_success "Docker services are already running."
fi

# Start the API server
print_header "Starting the Superior RAG API server..."

# Check if port 8000 is already in use
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
    print_error "Port 8000 is already in use. Please stop the service using port 8000 and try again."
    exit 1
fi

# Check which environment to start
ENVIRONMENT=${ENVIRONMENT:-development}
print_header "Starting in $ENVIRONMENT environment..."

# Create log directory if it doesn't exist
mkdir -p logs

# Start the API server with appropriate settings
if [ "$ENVIRONMENT" = "production" ]; then
    # Production mode - use Gunicorn with more workers
    print_header "Starting in PRODUCTION mode with Gunicorn..."
    
    # Calculate worker count based on CPU cores
    WORKERS=$(python -c "import multiprocessing as mp; print(min(mp.cpu_count() * 2 + 1, 8))")
    
    # Start with Gunicorn
    exec gunicorn src.api.app:app \
        --workers $WORKERS \
        --worker-class uvicorn.workers.UvicornWorker \
        --bind 0.0.0.0:8000 \
        --log-level info \
        --access-logfile logs/access.log \
        --error-logfile logs/error.log
else
    # Development mode - use Uvicorn with auto-reload
    print_header "Starting in DEVELOPMENT mode with Uvicorn and auto-reload..."
    
    # Start with Uvicorn
    exec uvicorn src.api.app:app \
        --host 0.0.0.0 \
        --port 8000 \
        --reload \
        --log-level debug
fi

```