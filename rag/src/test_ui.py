"""
RAG System Test UI

A simple Flask web application to test the RAG system with various LLM providers.
"""

import os
import sys
import logging
import json
from pathlib import Path
from flask import Flask, render_template, request, jsonify

# Add parent directory to path to import modules
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

# Import RAG system components
from config.rag_config import get_config
from core.rag_system.rag_system import RAGSystem

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, template_folder=str(Path(__file__).resolve().parent / "templates"))

# Initialize RAG system
config = get_config("development")
rag_system = None  # Will be initialized on first request

# Available LLM providers
LLM_PROVIDERS = {
    "groq": "Groq (Fast inference)",
    "ollama": "Ollama (Local models)",
    "openai": "OpenAI (GPT models)",
    "anthropic": "Anthropic Claude",
    "openrouter": "OpenRouter (Multiple models)"
}

# Replace before_first_request with app setup code
def init_rag_system():
    """Initialize the RAG system"""
    global rag_system
    try:
        # Check for vector_db directory
        vector_db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vector_db")
        if os.path.exists(vector_db_path):
            logger.info(f"Using vector store from: {vector_db_path}")
            # Use dictionary-based config to avoid issues with Pydantic models
            manual_config = {
                "embeddings": config.embeddings.dict() if hasattr(config.embeddings, "dict") else dict(config.embeddings),
                "vector_store": {
                    "store_type": "faiss",
                    "collection_name": "space_documents",
                    "persist_directory": vector_db_path
                },
                "verbose": True
            }
            rag_system = RAGSystem(config=manual_config)
            logger.info("RAG system initialized successfully with custom vector store path")
        else:
            logger.warning(f"Vector store directory not found at {vector_db_path}, using default configuration")
            rag_system = RAGSystem(config=config)
            logger.info("RAG system initialized with default configuration")
    except Exception as e:
        logger.error(f"Failed to initialize RAG system: {str(e)}")

# Initialize RAG system on app startup
with app.app_context():
    init_rag_system()

@app.route('/')
def index():
    """Render the main page"""
    # Get the current LLM provider from environment or default to groq
    current_provider = os.environ.get("LLM_PROVIDER", "groq")
    
    # Render the template with available providers
    return render_template(
        "index.html", 
        providers=LLM_PROVIDERS,
        current_provider=current_provider
    )

@app.route('/search', methods=['POST'])
def search():
    """Execute a search query"""
    global rag_system
    
    # Initialize RAG system if not already done
    if rag_system is None:
        try:
            rag_system = RAGSystem(config=config)
        except Exception as e:
            return jsonify({"error": f"Failed to initialize RAG system: {str(e)}"}), 500
    
    # Get parameters from request
    query = request.form.get('query')
    provider = request.form.get('provider', os.environ.get("LLM_PROVIDER", "groq"))
    temperature = float(request.form.get('temperature', 0.0))
    
    if not query:
        return jsonify({"error": "No query provided"}), 400
    
    try:
        # Get answer from RAG system
        response = rag_system.answer_question(
            question=query,
            llm_provider=provider,
            temperature=temperature
        )
        
        # Return response
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        return jsonify({"error": f"Error processing query: {str(e)}"}), 500

if __name__ == "__main__":
    # Create templates directory if it doesn't exist
    templates_dir = Path(__file__).resolve().parent / "templates"
    templates_dir.mkdir(exist_ok=True)
    
    # Create index.html template
    index_html = templates_dir / "index.html"
    if not index_html.exists():
        with open(index_html, "w") as f:
            f.write("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RAG System Test</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        .container {
            border: 1px solid #ddd;
            padding: 20px;
            border-radius: 5px;
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }
        select, input, textarea {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        button {
            background-color: #4CAF50;
            color: white;
            padding: 10px 15px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        button:hover {
            background-color: #45a049;
        }
        #response {
            margin-top: 20px;
            border: 1px solid #ddd;
            padding: 20px;
            border-radius: 5px;
            display: none;
        }
        #loading {
            text-align: center;
            margin-top: 20px;
            display: none;
        }
        .source {
            background-color: #f8f9fa;
            padding: 10px;
            border-left: 3px solid #007bff;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <h1>RAG System Test</h1>
    <div class="container">
        <div class="form-group">
            <label for="provider">LLM Provider:</label>
            <select id="provider">
                {% for key, name in providers.items() %}
                <option value="{{ key }}" {% if key == current_provider %}selected{% endif %}>{{ name }}</option>
                {% endfor %}
            </select>
        </div>
        <div class="form-group">
            <label for="query">Query:</label>
            <textarea id="query" rows="3" placeholder="What is the membership registration process for Space WH?"></textarea>
        </div>
        <div class="form-group">
            <label for="temperature">Temperature: <span id="temp-value">0.0</span></label>
            <input type="range" id="temperature" min="0" max="1" step="0.1" value="0.0">
        </div>
        <button id="submit">Search</button>
    </div>
    
    <div id="loading">
        <img src="https://c.tenor.com/I6kN-6X7nhAAAAAj/loading-buffering.gif" alt="Loading..." height="50">
        <p>Processing your query...</p>
    </div>
    
    <div id="response">
        <h2>Response</h2>
        <div id="answer"></div>
        <div id="sources"></div>
    </div>

    <script>
        // Update temperature value display
        const tempSlider = document.getElementById('temperature');
        const tempValue = document.getElementById('temp-value');
        
        tempSlider.addEventListener('input', function() {
            tempValue.textContent = this.value;
        });
        
        // Handle form submission
        document.getElementById('submit').addEventListener('click', function() {
            const provider = document.getElementById('provider').value;
            const query = document.getElementById('query').value;
            const temperature = document.getElementById('temperature').value;
            
            if (!query) {
                alert('Please enter a query');
                return;
            }
            
            // Show loading indicator
            document.getElementById('loading').style.display = 'block';
            document.getElementById('response').style.display = 'none';
            
            // Create form data
            const formData = new FormData();
            formData.append('query', query);
            formData.append('provider', provider);
            formData.append('temperature', temperature);
            
            // Send request
            fetch('/search', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                // Hide loading indicator
                document.getElementById('loading').style.display = 'none';
                
                // Show response
                document.getElementById('response').style.display = 'block';
                
                if (data.error) {
                    document.getElementById('answer').innerHTML = `<p style="color: red;">Error: ${data.error}</p>`;
                    document.getElementById('sources').innerHTML = '';
                } else {
                    document.getElementById('answer').innerHTML = `<p><strong>Question:</strong> ${data.question}</p><p><strong>Answer:</strong> ${data.answer.replace(/\\n/g, '<br>')}</p>`;
                    
                    if (data.sources && data.sources.length > 0) {
                        let sourcesHtml = '<h3>Sources:</h3><ul>';
                        data.sources.forEach(source => {
                            sourcesHtml += `<li class="source">${source}</li>`;
                        });
                        sourcesHtml += '</ul>';
                        document.getElementById('sources').innerHTML = sourcesHtml;
                    } else {
                        document.getElementById('sources').innerHTML = '';
                    }
                }
            })
            .catch(error => {
                document.getElementById('loading').style.display = 'none';
                document.getElementById('response').style.display = 'block';
                document.getElementById('answer').innerHTML = `<p style="color: red;">Error: ${error.message}</p>`;
                document.getElementById('sources').innerHTML = '';
            });
        });
    </script>
</body>
</html>
""")
    
    # Run Flask app
    app.run(host="0.0.0.0", port=8501, debug=True)