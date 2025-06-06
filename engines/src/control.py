"""
Main System Engine Control class that orchestrates the workflow and provides interfaces.
"""
import logging
import time
from typing import Dict, Any, Optional, List, Union
import asyncio

from .schemas import EngineState, RequestInput, ResponseOutput
from .workflow import create_workflow
from .router import get_engine_for_mode

# Set up logging
logger = logging.getLogger("engine_control")


class SystemEngineControl:
    """
    The main control system that orchestrates workflows and integrates components.
    """
    
    def __init__(self, 
                ai_council=None, 
                rag_system=None, 
                tools_system=None, 
                config: Dict[str, Any] = None):
        """
        Initialize the System Engine Control.
        
        Args:
            ai_council: The AI Council component
            rag_system: The RAG System component
            tools_system: The Tools/Packages System component
            config: Configuration options
        """
        self.ai_council = ai_council
        self.rag_system = rag_system
        self.tools_system = tools_system
        self.config = config or {}
        
        # Set up the workflow
        self.workflow = create_workflow(
            ai_council=ai_council,
            rag_system=rag_system,
            tools_system=tools_system,
            config=config
        )
        
        # Compile the workflow
        self.graph = self.workflow.compile()
        
        logger.info("System Engine Control initialized")
        
        # Track active requests
        self.active_requests = {}
    
    async def process_request(self, request: Union[RequestInput, Dict[str, Any]]) -> ResponseOutput:
        """
        Process a request using the appropriate engine based on mode.
        
        Args:
            request: The request to process (either a RequestInput object or a dict)
            
        Returns:
            ResponseOutput: The processing result
        """
        start_time = time.time()
        
        if isinstance(request, dict):
            request = RequestInput(**request)
        
        logger.info(f"Processing request for user {request.user_id} with mode {request.mode}")
        
        # Create initial state for the workflow
        initial_state: EngineState = {
            "user_id": request.user_id,
            "mode": request.mode,
            "query": request.message,
            "context": request.context or {},
            "tools_used": [],
            "tool_results": [],
            "current_engine": None,
            "response": None,
            "error": None,
            "metadata": request.metadata or {}
        }
        
        try:
            # Add the request to active requests
            request_id = f"{request.user_id}_{int(time.time())}"
            self.active_requests[request_id] = {
                "status": "processing",
                "start_time": start_time,
                "request": request.dict()
            }
            
            # Execute the workflow
            logger.info(f"Executing workflow for request {request_id}")
            final_state = await self.graph.ainvoke(initial_state)
            
            # Update request status
            self.active_requests[request_id]["status"] = "completed"
            
            # Build response
            processing_time_ms = round((time.time() - start_time) * 1000, 2)
            response = ResponseOutput(
                response=final_state.get("response", ""),
                user_id=request.user_id,
                tools_used=final_state.get("tools_used", []),
                processing_time_ms=processing_time_ms,
                metadata=final_state.get("metadata", {}),
                error=final_state.get("error")
            )
            
            logger.info(f"Request {request_id} processed in {processing_time_ms} ms")
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            
            # Update request status
            if request_id in self.active_requests:
                self.active_requests[request_id]["status"] = "failed"
                self.active_requests[request_id]["error"] = str(e)
            
            # Return error response
            processing_time_ms = round((time.time() - start_time) * 1000, 2)
            return ResponseOutput(
                response="An error occurred while processing your request.",
                user_id=request.user_id,
                processing_time_ms=processing_time_ms,
                error=str(e)
            )
    
    def get_active_requests(self) -> List[Dict[str, Any]]:
        """
        Get a list of current active requests.
        
        Returns:
            List of active request information
        """
        return [
            {
                "id": req_id,
                "status": info["status"],
                "user_id": info["request"]["user_id"],
                "mode": info["request"]["mode"],
                "duration": round((time.time() - info["start_time"]) * 1000, 2),
                "started_at": info["start_time"]
            }
            for req_id, info in self.active_requests.items()
            if info["status"] == "processing"
        ]
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the system status.
        
        Returns:
            Status information
        """
        return {
            "status": "operational",
            "active_requests": len([r for r, info in self.active_requests.items() if info["status"] == "processing"]),
            "components": {
                "engine1": "operational",
                "engine2": "operational",
                "engine3": "operational",
                "engine4": "in_development",
                "ai_council": "operational" if self.ai_council else "not_connected",
                "rag_system": "operational" if self.rag_system else "not_connected",
                "tool_system": "operational" if self.tools_system else "not_connected"
            },
            "timestamp": time.time()
        }
        
    async def cancel_request(self, request_id: str) -> bool:
        """
        Cancel an active request.
        
        Args:
            request_id: The ID of the request to cancel
            
        Returns:
            True if cancelled successfully, False otherwise
        """
        if request_id in self.active_requests and self.active_requests[request_id]["status"] == "processing":
            self.active_requests[request_id]["status"] = "cancelled"
            logger.info(f"Request {request_id} cancelled")
            return True
        return False