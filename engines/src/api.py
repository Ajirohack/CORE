"""
API service for the System Engine Control.
Provides REST endpoints to interact with the System Engine Control.
"""
import logging
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
import uvicorn

from .control import SystemEngineControl
from .schemas import RequestInput, ResponseOutput

# Set up logging
logger = logging.getLogger("engine_control.api")

class EngineControlAPI:
    """API service for the System Engine Control."""
    
    def __init__(self, engine_control: SystemEngineControl):
        """
        Initialize the API service.
        
        Args:
            engine_control: The System Engine Control instance
        """
        self.engine_control = engine_control
        self.app = FastAPI(
            title="System Engine Control API",
            description="API for the System Engine Control component of Space WH",
            version="0.1.0"
        )
        self.setup_routes()
    
    def setup_routes(self):
        """Set up the API routes."""
        
        @self.app.get("/")
        async def root():
            """Root endpoint."""
            return {"message": "System Engine Control API"}
        
        @self.app.get("/status")
        async def get_status():
            """Get the system status."""
            return self.engine_control.get_status()
        
        @self.app.get("/active-requests")
        async def get_active_requests():
            """Get active requests."""
            return {"active_requests": self.engine_control.get_active_requests()}
        
        @self.app.post("/process", response_model=ResponseOutput)
        async def process_request(request: RequestInput):
            """Process a request."""
            try:
                return await self.engine_control.process_request(request)
            except Exception as e:
                logger.error(f"Error processing request: {str(e)}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.delete("/requests/{request_id}")
        async def cancel_request(request_id: str):
            """Cancel an active request."""
            success = await self.engine_control.cancel_request(request_id)
            if success:
                return {"message": f"Request {request_id} cancelled"}
            else:
                raise HTTPException(status_code=404, detail=f"Request {request_id} not found or not active")
    
    def run(self, host: str = "0.0.0.0", port: int = 8000):
        """
        Run the API server.
        
        Args:
            host: The host to bind to
            port: The port to listen on
        """
        uvicorn.run(self.app, host=host, port=port)


def create_api_service(
    ai_council=None,
    rag_system=None,
    tools_system=None,
    config: Optional[Dict[str, Any]] = None
) -> EngineControlAPI:
    """
    Create an API service for the System Engine Control.
    
    Args:
        ai_council: The AI Council component
        rag_system: The RAG System component
        tools_system: The Tools/Packages System component
        config: Configuration options
        
    Returns:
        The API service
    """
    engine_control = SystemEngineControl(
        ai_council=ai_council,
        rag_system=rag_system,
        tools_system=tools_system,
        config=config
    )
    return EngineControlAPI(engine_control)