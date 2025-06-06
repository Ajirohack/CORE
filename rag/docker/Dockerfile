FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    pkg-config \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Create necessary directories
RUN mkdir -p /app/data/models
RUN mkdir -p /app/data/uploads
RUN mkdir -p /app/data/temp
RUN mkdir -p /app/logs

# Make scripts executable
RUN chmod +x /app/scripts/setup.sh
RUN chmod +x /app/scripts/start.sh

# Expose API port
EXPOSE 8000

# Command to run when the container starts
CMD ["./scripts/start.sh", "--host=0.0.0.0"]