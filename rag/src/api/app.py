"""
Main FastAPI application for the Superior RAG system.

This module defines the API routes and initializes the necessary components.
"""

import os
import logging
import asyncio
from fastapi import FastAPI, Depends, HTTPException, Header, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import time
from typing import Dict, List, Any, Optional, Union

# Import storage modules
from src.storage.vector_store import init_vector_store, get_vector_store
from src.storage.relational_store import init_relational_store, get_relational_store
from src.storage.graph_store import init_graph_store, get_graph_store
from src.storage.cache_store import init_cache_store, get_cache_store

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("superior_rag.api")

# Create FastAPI app
app = FastAPI(
    title="Superior RAG System API",
    description="A comprehensive RAG system with advanced retrieval and memory capabilities",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event to initialize services
@app.on_event("startup")
async def startup_event():
    """Initialize all required services on startup."""
    logger.info("Initializing Superior RAG system...")
    
    # Initialize storage components
    await init_vector_store()
    await init_relational_store()
    await init_graph_store()
    await init_cache_store()
    
    logger.info("Superior RAG system initialized and ready")

# Shutdown event to close connections
@app.on_event("shutdown")
async def shutdown_event():
    """Close all connections on shutdown."""
    logger.info("Shutting down Superior RAG system...")
    
    # Close connections
    vector_store = get_vector_store()
    relational_store = get_relational_store()
    graph_store = get_graph_store()
    cache_store = get_cache_store()
    
    # Close Redis connection
    await cache_store.close()
    
    # Close Neo4j connection
    await graph_store.close()
    
    # Close PostgreSQL connection
    await relational_store.disconnect()
    
    logger.info("Superior RAG system shut down complete")

# API Key authentication
async def verify_api_key(api_key: str = Header(..., description="API Key for authentication")):
    """
    Verify the API key for authentication.
    
    Args:
        api_key: API key provided in the request header
        
    Returns:
        str: The validated API key
        
    Raises:
        HTTPException: If the API key is invalid
    """
    if not api_key:
        raise HTTPException(status_code=401, detail="API Key is required")
    
    try:
        # Get the relational store
        relational_store = get_relational_store()
        
        # Check if the API key exists in the database
        results = await relational_store.execute_query(
            "SELECT id, key, name FROM api_keys WHERE key = $1",
            api_key
        )
        
        if not results:
            raise HTTPException(status_code=401, detail="Invalid API Key")
        
        # Update last used timestamp
        await relational_store.execute_query(
            "UPDATE api_keys SET last_used_at = CURRENT_TIMESTAMP WHERE key = $1",
            api_key
        )
        
        # Return the key if valid
        return api_key
        
    except Exception as e:
        logger.error(f"Error validating API key: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during authentication")

# Request/response models
class QueryRequest(BaseModel):
    """Model for query requests."""
    query: str = Field(..., description="The user's query")
    conversation_id: Optional[str] = Field(None, description="ID of the conversation for context")
    max_results: Optional[int] = Field(5, description="Maximum number of results to return")
    include_sources: Optional[bool] = Field(True, description="Whether to include source documents")

class QueryResponse(BaseModel):
    """Model for query responses."""
    answer: str = Field(..., description="The generated answer")
    sources: Optional[List[Dict[str, Any]]] = Field([], description="Source documents used")
    processing_time: float = Field(..., description="Processing time in seconds")
    context_tokens: Optional[int] = Field(None, description="Number of context tokens used")

# Health check endpoint
@app.get("/health", tags=["System"])
async def health_check():
    """
    Check the health of the system.
    
    Returns:
        dict: Health status of all components
    """
    status = {
        "status": "ok",
        "version": app.version,
        "components": {}
    }
    
    try:
        # Check vector store
        vector_store = get_vector_store()
        if vector_store.client:
            status["components"]["vector_store"] = "connected"
        else:
            status["components"]["vector_store"] = "disconnected"
            status["status"] = "degraded"
    except Exception as e:
        status["components"]["vector_store"] = f"error: {str(e)}"
        status["status"] = "degraded"
        
    try:
        # Check relational store
        relational_store = get_relational_store()
        if relational_store.pool:
            status["components"]["relational_store"] = "connected"
        else:
            status["components"]["relational_store"] = "disconnected"
            status["status"] = "degraded"
    except Exception as e:
        status["components"]["relational_store"] = f"error: {str(e)}"
        status["status"] = "degraded"
        
    try:
        # Check graph store
        graph_store = get_graph_store()
        if graph_store.driver:
            status["components"]["graph_store"] = "connected"
        else:
            status["components"]["graph_store"] = "disconnected"
            status["status"] = "degraded"
    except Exception as e:
        status["components"]["graph_store"] = f"error: {str(e)}"
        status["status"] = "degraded"
        
    try:
        # Check cache store
        cache_store = get_cache_store()
        if cache_store.client:
            status["components"]["cache_store"] = "connected"
        else:
            status["components"]["cache_store"] = "disconnected"
            status["status"] = "degraded"
    except Exception as e:
        status["components"]["cache_store"] = f"error: {str(e)}"
        status["status"] = "degraded"
        
    return status

# Root endpoint
@app.get("/", tags=["System"])
async def root():
    """
    Root endpoint returning system information.
    
    Returns:
        dict: Information about the API
    """
    return {
        "name": "Superior RAG System API",
        "version": app.version,
        "description": "A comprehensive RAG system with advanced retrieval and memory capabilities",
        "docs_url": "/docs"
    }

# Query endpoint - this would be implemented with actual RAG functionality
@app.post("/query", response_model=QueryResponse, tags=["Query"])
async def process_query(
    request: QueryRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Process a query using the Superior RAG system.
    
    Args:
        request: The query request
        api_key: Verified API key
        
    Returns:
        QueryResponse: The generated answer and sources
    """
    start_time = time.time()
    
    try:
        # In a full implementation, we would:
        # 1. Transform the query if needed
        # 2. Retrieve relevant documents
        # 3. Generate an answer with an LLM
        # 4. Track the query in the database
        
        # For now, return a placeholder response
        answer = f"This is a placeholder answer for the query: {request.query}"
        sources = [
            {
                "title": "Example Document",
                "content": "This is an example source document.",
                "score": 0.95
            }
        ]
        
        processing_time = time.time() - start_time
        
        return QueryResponse(
            answer=answer,
            sources=sources if request.include_sources else [],
            processing_time=processing_time,
            context_tokens=100  # Placeholder value
        )
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

# Error handler for unhandled exceptions
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again later."}
    )

# Main entry point for direct execution
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)