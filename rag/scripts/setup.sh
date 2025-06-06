#!/bin/bash

# Superior RAG System Setup Script
# This script initializes the system, including databases and required dependencies

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

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker before running this script."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose before running this script."
    exit 1
fi

# Ensure we're in the project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
cd "$SCRIPT_DIR/.."

# Check if .env file exists
if [ ! -f .env ]; then
    print_warning "No .env file found. Creating from example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        print_success "Created .env file from example. Please edit it with your configuration."
    else
        print_error "No .env.example file found. Please create a .env file manually."
        exit 1
    fi
fi

# Source the .env file to get environment variables
set -a  # Automatically export all variables
source .env
set +a

print_header "Setting up Superior RAG System..."

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
python_major_version=$(echo $python_version | cut -d '.' -f 1)
python_minor_version=$(echo $python_version | cut -d '.' -f 2)

if [ "$python_major_version" -lt 3 ] || ([ "$python_major_version" -eq 3 ] && [ "$python_minor_version" -lt 8 ]); then
    print_error "Python 3.8 or higher is required. Found Python $python_version"
    exit 1
fi

print_success "Python $python_version detected."

# Create required directories
print_header "Creating required directories..."
mkdir -p logs
mkdir -p data/uploads
mkdir -p data/temp
mkdir -p data/models
chmod -R 755 data

print_success "Directories created."

# Install Python dependencies
print_header "Installing Python dependencies..."
pip install -r requirements.txt
print_success "Python dependencies installed."

# Download spaCy model if needed
print_header "Checking spaCy model..."
if ! python -c "import spacy; spacy.load('en_core_web_sm')" &> /dev/null; then
    print_warning "Downloading spaCy model..."
    python -m spacy download en_core_web_sm
    print_success "spaCy model downloaded."
else
    print_success "spaCy model already installed."
fi

# Start Docker services
print_header "Starting Docker services..."
docker-compose -f docker/docker-compose.yml up -d
print_success "Docker services started."

# Wait for services to be ready
print_header "Waiting for services to be ready..."
sleep 10

# Initialize vector database collection
print_header "Initializing vector database collection..."
python -c "
import asyncio
from src.storage.vector_store import init_vector_store

async def init():
    vector_store = await init_vector_store()
    print('Vector store initialized successfully')

asyncio.run(init())
"
print_success "Vector database collection initialized."

# Initialize relational database schema
print_header "Initializing relational database schema..."
python -c "
import asyncio
from src.storage.relational_store import init_relational_store

async def init():
    relational_store = await init_relational_store()
    print('Relational database schema initialized successfully')

asyncio.run(init())
"
print_success "Relational database schema initialized."

# Initialize graph database schema
print_header "Initializing graph database schema..."
python -c "
import asyncio
from src.storage.graph_store import init_graph_store

async def init():
    graph_store = await init_graph_store()
    print('Graph database schema initialized successfully')

asyncio.run(init())
"
print_success "Graph database schema initialized."

# Create API key for testing
print_header "Setting up test API key..."
API_KEY=${API_KEY:-$(openssl rand -hex 16)}
echo "Using API key: $API_KEY"
python -c "
import asyncio
from src.storage.relational_store import init_relational_store

async def setup_api_key():
    from src.storage.relational_store import get_relational_store
    relational_store = await init_relational_store()
    
    # Get relational store instance
    store = get_relational_store()
    
    # Create API key record
    await store.execute_query('''
        INSERT INTO api_keys (key, name, created_at)
        VALUES ('$API_KEY', 'Test Key', CURRENT_TIMESTAMP)
        ON CONFLICT (key) DO NOTHING;
    ''')
    
    print('Test API key stored successfully')

asyncio.run(setup_api_key())
"
print_success "Test API key set up: $API_KEY"

# Print success message
print_header "Setup complete!"
print_success "The Superior RAG System has been successfully set up."
print_success "You can now start the API server with:"
print_success "  uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload"
print_success "API Documentation will be available at: http://localhost:8000/docs"
