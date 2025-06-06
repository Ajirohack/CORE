# Import necessary libraries
from ollama import OllamaClient

# Initialize Ollama client
client = OllamaClient(api_key='YOUR_API_KEY')

# Load and fine-tune the model
model = client.models.load('base_model_name')

# Prepare your dataset
dataset = [
    {"input": "Hello, my name is John Doe", "output": "John Doe"},
    # Add more samples
]

# Fine-tune the model
fine_tuned_model = client.models.fine_tune(model, dataset)

# Save the fine-tuned model
fine_tuned_model.save('fine_tuned_model.ollama')
