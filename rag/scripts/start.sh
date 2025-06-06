#!/bin/bash

# Start script for Superior RAG system

echo "Starting Superior RAG System..."

# Determine the root directory
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# Set environment variables
export PYTHONPATH=$ROOT_DIR

# Default settings
HOST="0.0.0.0"
PORT="8000"
WORKERS=1
RELOAD=true

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --port=*)
            PORT="${1#*=}"
            ;;
        --host=*)
            HOST="${1#*=}"
            ;;
        --workers=*)
            WORKERS="${1#*=}"
            ;;
        --no-reload)
            RELOAD=false
            ;;
        --production)
            export CONFIG_MODE="production"
            RELOAD=false
            WORKERS=4
            ;;
        --development)
            export CONFIG_MODE="development"
            RELOAD=true
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--port=8000] [--host=0.0.0.0] [--workers=1] [--no-reload] [--production|--development]"
            exit 1
            ;;
    esac
    shift
done

# Check if running in development or production mode
if [ "$CONFIG_MODE" = "production" ]; then
    echo "Running in PRODUCTION mode with $WORKERS workers"
else
    echo "Running in DEVELOPMENT mode with hot-reload enabled"
fi

# Set reload flag for uvicorn
if [ "$RELOAD" = true ]; then
    RELOAD_FLAG="--reload"
else
    RELOAD_FLAG=""
fi

# Run the API server
echo "Starting server on $HOST:$PORT..."
python -m uvicorn src.api.app:app --host $HOST --port $PORT --workers $WORKERS $RELOAD_FLAG

# Exit with the same code as the uvicorn process
exit $?
