#!/usr/bin/env python3
"""
Runner for the RAG service.
"""
import asyncio
import uvicorn
import os
import sys
from pathlib import Path

# Add core to Python path
core_path = Path(__file__).parent.parent
sys.path.insert(0, str(core_path))

from rag_service import RAGService
from fastapi import FastAPI
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="RAG Service", version="1.0.0")
service = None

@app.on_event("startup")
async def startup_event():
    global service
    config = {
        'space_api_url': os.getenv('SPACE_API_URL', 'http://localhost:8000'),
        'api_key': os.getenv('API_KEY'),
        'log_level': os.getenv('LOG_LEVEL', 'INFO')
    }
    
    service = RAGService(config)
    await service.initialize()
    await service.start()

@app.on_event("shutdown")
async def shutdown_event():
    if service:
        await service.shutdown()

@app.get("/health")
async def health_check():
    if service:
        return await service.health_check()
    return {"status": "starting"}

@app.post("/api/v1/rag/process")
async def process_request(request: dict):
    if service:
        from base_service import ServiceRequest
        service_request = ServiceRequest(
            request_id=request.get('request_id'),
            service_id=service.service_id,
            action=request.get('action'),
            payload=request.get('payload', {}),
            user_id=request.get('user_id'),
            session_id=request.get('session_id')
        )
        response = await service.process_request(service_request)
        return response
    return {"error": "Service not initialized"}

if __name__ == "__main__":
    port = int(os.getenv('SERVICE_PORT', 8004))
    uvicorn.run(app, host="0.0.0.0", port=port)
