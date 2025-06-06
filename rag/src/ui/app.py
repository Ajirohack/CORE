"""
RAG UI Interface - Test different LLM providers with the RAG system
"""

import os
import sys
import logging
from pathlib import Path
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

# Add parent directories to import path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

# Import RAG system components
from config.rag_config import get_config
from core.rag_system.rag_system import RAGSystem
from core.rag_system.llm_integration import get_llm_provider

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Initialize RAG system
config = get_config("development")
rag_system = RAGSystem(config=config)

# Available LLM providers
LLM_PROVIDERS = {
    "openai": "OpenAI (GPT-4, etc.)",
    "anthropic": "Anthropic Claude",
    "ollama": "Ollama (local models)",
    "openrouter": "OpenRouter",
    "groq": "Groq",
    "openwebui": "Open Web UI"
}

# Available models by provider (limited selection for UI)
DEFAULT_MODELS = {
    "openai": ["gpt-4-turbo", "gpt-3.5-turbo"],
    "anthropic": ["claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"],
    "ollama": ["llama3", "mixtral", "gemma"],
    "openrouter": ["openai/gpt-4-turbo", "anthropic/claude-3-opus-20240229"],
    "groq": ["llama3-8b-8192", "llama3-70b-8192", "mixtral-8x7b-32768"],
    "openwebui": ["default"]
}


@app.route('/')
def index():
    """Render the main page"""
    return render_template(
        'index.html',
        providers=LLM_PROVIDERS,
        default_models=DEFAULT_MODELS,
        current_provider=os.environ.get("LLM_PROVIDER", "groq")
    )


@app.route('/search', methods=['POST'])
def search():
    """Perform a search only query"""
    try:
        query = request.form.get('query')
        num_results = int(request.form.get('num_results', 5))
        
        if not query:
            return jsonify({"error": "No query provided"}), 400
        
        # Perform search
        results = rag_system.search(query, k=num_results)
        
        # Format results for display
        formatted_results = []
        for i, doc in enumerate(results):
            source = "Unknown"
            if "metadata" in doc and doc["metadata"]:
                if "source" in doc["metadata"]:
                    source = doc["metadata"]["source"]
                elif "filename" in doc["metadata"]:
                    source = doc["metadata"]["filename"]
            
            formatted_results.append({
                "id": i + 1,
                "source": source,
                "content": doc["content"]
            })
        
        return jsonify({
            "query": query,
            "results": formatted_results
        })
    
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        return jsonify({"error": f"Error performing search: {str(e)}"}), 500


@app.route('/ask', methods=['POST'])
def ask():
    """Ask a question using the RAG system with a selected LLM provider"""
    try:
        query = request.form.get('query')
        provider = request.form.get('provider', os.environ.get("LLM_PROVIDER", "groq"))
        model = request.form.get('model')
        temperature = float(request.form.get('temperature', 0.0))
        system_message = request.form.get('system_message', None)
        
        if not query:
            return jsonify({"error": "No query provided"}), 400
        
        # If model was provided, set it in the environment temporarily
        original_model = None
        if model:
            if provider == "openai":
                original_model = os.environ.get("OPENAI_MODEL")
                os.environ["OPENAI_MODEL"] = model
            elif provider == "anthropic":
                original_model = os.environ.get("ANTHROPIC_MODEL")
                os.environ["ANTHROPIC_MODEL"] = model
            elif provider == "ollama":
                original_model = os.environ.get("OLLAMA_MODEL")
                os.environ["OLLAMA_MODEL"] = model
            elif provider == "openrouter":
                original_model = os.environ.get("OPENROUTER_MODEL")
                os.environ["OPENROUTER_MODEL"] = model
            elif provider == "groq":
                original_model = os.environ.get("GROQ_MODEL")
                os.environ["GROQ_MODEL"] = model
            elif provider == "openwebui":
                original_model = os.environ.get("OPENWEBUI_MODEL")
                os.environ["OPENWEBUI_MODEL"] = model
        
        # Get answer
        answer = rag_system.answer_question(
            question=query, 
            llm_provider=provider,
            system_message=system_message,
            temperature=temperature
        )
        
        # Restore original model if it was changed
        if original_model is not None:
            if provider == "openai":
                os.environ["OPENAI_MODEL"] = original_model
            elif provider == "anthropic":
                os.environ["ANTHROPIC_MODEL"] = original_model
            elif provider == "ollama":
                os.environ["OLLAMA_MODEL"] = original_model
            elif provider == "openrouter":
                os.environ["OPENROUTER_MODEL"] = original_model
            elif provider == "groq":
                os.environ["GROQ_MODEL"] = original_model
            elif provider == "openwebui":
                os.environ["OPENWEBUI_MODEL"] = original_model
        
        # Check if there was an error
        if "error" in answer:
            return jsonify({
                "query": query,
                "error": answer["error"],
                "provider": provider,
                "model": model or "default"
            })
            
        return jsonify({
            "query": query,
            "answer": answer["answer"],
            "sources": answer.get("sources", []),
            "provider": provider,
            "model": model or "default"
        })
        
    except Exception as e:
        logger.error(f"Ask error: {str(e)}")
        return jsonify({"error": f"Error generating answer: {str(e)}"}), 500


@app.route('/get_models', methods=['POST'])
def get_models():
    """Get available models for a provider"""
    provider = request.form.get('provider', 'openai')
    return jsonify({
        "models": DEFAULT_MODELS.get(provider, [])
    })


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8501)