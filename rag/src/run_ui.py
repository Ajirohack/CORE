#!/usr/bin/env python3
"""
Wrapper script to run the RAG system UI with proper environment setup
"""
import os
import sys
import subprocess
import traceback

# Add the project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

print(f"Python executable: {sys.executable}")
print(f"Python path: {sys.path}")
print(f"Current directory: {os.getcwd()}")

# Install required dependencies if needed
print("Checking dependencies...")
try:
    import dotenv
    import pydantic
    import langchain
    import flask
    import qdrant_client
    import sentence_transformers
    print("All required dependencies are installed!")
except ImportError as e:
    missing_pkg = str(e).split("'")[-2]
    print(f"Missing required dependency: {missing_pkg}")
    print("Installing required dependencies...")
    
    dependencies = [
        "pydantic",
        "python-dotenv",
        "langchain",
        "langchain-community",
        "flask",
        "qdrant-client",
        "sentence-transformers",
        "faiss-cpu"
    ]
    
    for dep in dependencies:
        print(f"Installing {dep}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
            print(f"Successfully installed {dep}")
        except subprocess.CalledProcessError as e:
            print(f"Warning: Failed to install {dep}: {e}")

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Print active configuration
print("\nActive RAG System Configuration:")
print(f"- Embedding: {os.getenv('RAG_EMBEDDING_TYPE', 'huggingface')} - {os.getenv('RAG_EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')}")
print(f"- Vector Store: {os.getenv('RAG_VECTOR_STORE_TYPE', 'faiss')} - {os.getenv('RAG_COLLECTION_NAME', 'space_documents')}")
print(f"- LLM Provider: {os.getenv('LLM_PROVIDER', 'groq')}")
print(f"- LLM Model: {os.getenv('GROQ_MODEL', 'llama3-70b-8192') if os.getenv('LLM_PROVIDER') == 'groq' else '(check config)'}")

print("\nStarting RAG System Test UI...")
try:
    # First import the config to check if our fix worked
    from config.rag_config import get_config
    config = get_config()
    
    # Make sure the embedding configuration get() method works
    embedding_config = config.embeddings
    embedding_type = embedding_config.get("embedding_type", "default")
    print(f"Successfully loaded configuration. Embedding type: {embedding_type}")
    
    # Set environment variable for vector store path
    os.environ["RAG_VECTOR_STORE_PATH"] = os.path.join(project_root, "vector_db")
    print(f"Setting RAG vector store path to: {os.environ['RAG_VECTOR_STORE_PATH']}")
    
    # Now import the app and run it
    from core.rag_system.test_ui import app
    print("UI started successfully!")
    print("Open your web browser and go to: http://127.0.0.1:5001")
    # Use port 5001 instead of 5000 to avoid conflicts with AirPlay on macOS
    app.run(debug=True, host='0.0.0.0', port=5001)
except Exception as e:
    print(f"Error starting UI: {e}")
    traceback.print_exc()
    
    # Create a basic Flask app to show the error
    from flask import Flask, render_template_string
    error_app = Flask(__name__)
    
    @error_app.route('/')
    def index():
        return render_template_string("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>RAG System - Error</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; }
                    h1 { color: #333; }
                    .error { color: #f44336; white-space: pre-wrap; }
                    pre { background-color: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto; }
                </style>
            </head>
            <body>
                <h1>RAG System - Error</h1>
                <p>There was an error starting the RAG system:</p>
                <div class="error">{{ error }}</div>
                <h2>Traceback:</h2>
                <pre>{{ traceback }}</pre>
                
                <h2>Fix Suggestions:</h2>
                <ul>
                    <li>Check that all required API keys are set in the .env file</li>
                    <li>Ensure all dependencies are installed correctly</li>
                    <li>Check the Python path and virtual environment activation</li>
                </ul>
            </body>
            </html>
        """, error=str(e), traceback=traceback.format_exc())
    
    print("Starting error display UI...")
    print("Open your web browser and go to: http://127.0.0.1:5001")
    error_app.run(debug=True, host='0.0.0.0', port=5001)