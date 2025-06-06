"""
Engines service implementation.
Manages pluggable engine implementations for workflow processing.
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional
import importlib
import os
from pathlib import Path

try:
    from ..base_service import BaseService, ServiceRequest, ServiceResponse
except ImportError:
    # For when running as a script
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from base_service import BaseService, ServiceRequest, ServiceResponse

logger = logging.getLogger(__name__)

class EnginesService(BaseService):
    """
    Service for managing and executing pluggable engines.
    Handles workflow execution, data processing, AI reasoning, and action execution.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("engines", "1.0.0", config)
        self.engines = {}
        self.engine_configs = {}
        self.active_workflows = {}
        
    def get_description(self) -> str:
        return "Pluggable engine implementations for workflow processing and execution"
    
    def get_capabilities(self) -> List[str]:
        return [
            "workflow_execution",
            "data_processing", 
            "ai_reasoning",
            "action_execution",
            "engine_management"
        ]
    
    def get_endpoints(self) -> Dict[str, str]:
        return {
            "execute_workflow": "/engines/workflow/execute",
            "list_engines": "/engines/list",
            "engine_status": "/engines/{engine_id}/status",
            "workflow_status": "/engines/workflow/{workflow_id}/status"
        }
    
    async def initialize(self) -> bool:
        """Initialize the engines service"""
        try:
            # Load available engines
            await self._discover_engines()
            
            # Initialize core engines
            await self._initialize_core_engines()
            
            self.logger.info(f"Engines service initialized with {len(self.engines)} engines")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize engines service: {e}")
            return False
    
    async def process_request(self, request: ServiceRequest) -> ServiceResponse:
        """Process incoming service request"""
        try:
            action = request.action
            payload = request.payload
            
            if action == "execute_workflow":
                result = await self._execute_workflow(payload)
            elif action == "list_engines":
                result = await self._list_engines()
            elif action == "get_engine_status":
                result = await self._get_engine_status(payload.get("engine_id"))
            elif action == "get_workflow_status":
                result = await self._get_workflow_status(payload.get("workflow_id"))
            elif action == "stop_workflow":
                result = await self._stop_workflow(payload.get("workflow_id"))
            else:
                return ServiceResponse(
                    request_id=request.request_id,
                    service_id=self.service_id,
                    status="error",
                    error=f"Unknown action: {action}"
                )
            
            return ServiceResponse(
                request_id=request.request_id,
                service_id=self.service_id,
                status="success",
                data=result
            )
            
        except Exception as e:
            self.logger.error(f"Error processing request {request.request_id}: {e}")
            return ServiceResponse(
                request_id=request.request_id,
                service_id=self.service_id,
                status="error",
                error=str(e)
            )
    
    async def shutdown(self):
        """Cleanup on service shutdown"""
        # Stop all active workflows
        for workflow_id in list(self.active_workflows.keys()):
            await self._stop_workflow(workflow_id)
        
        # Shutdown engines
        for engine in self.engines.values():
            if hasattr(engine, 'shutdown'):
                await engine.shutdown()
        
        self.logger.info("Engines service shutdown complete")
    
    async def _discover_engines(self):
        """Discover available engines in the engines directory"""
        engines_dir = Path(__file__).parent
        
        # Look for engine directories
        for item in engines_dir.iterdir():
            if item.is_dir() and item.name.startswith('engine'):
                engine_name = item.name
                engine_path = item / 'engine.py'
                
                if engine_path.exists():
                    try:
                        # Load engine configuration
                        config_path = item / 'config.json'
                        if config_path.exists():
                            import json
                            with open(config_path) as f:
                                self.engine_configs[engine_name] = json.load(f)
                        else:
                            self.engine_configs[engine_name] = {}
                        
                        self.logger.info(f"Discovered engine: {engine_name}")
                        
                    except Exception as e:
                        self.logger.warning(f"Failed to load engine {engine_name}: {e}")
    
    async def _initialize_core_engines(self):
        """Initialize the core engines"""
        core_engines = {
            "engine1": "WorkflowExecutionEngine",
            "engine2": "DataProcessingEngine", 
            "engine3": "AIReasoningEngine",
            "engine4": "ActionIntegrationEngine"
        }
        
        for engine_name, engine_class in core_engines.items():
            try:
                # Create mock engine for now - in production these would be real implementations
                engine = MockEngine(engine_name, engine_class, self.engine_configs.get(engine_name, {}))
                await engine.initialize()
                self.engines[engine_name] = engine
                
                self.logger.info(f"Initialized engine: {engine_name}")
                
            except Exception as e:
                self.logger.error(f"Failed to initialize engine {engine_name}: {e}")
    
    async def _execute_workflow(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a workflow through the engine pipeline"""
        workflow_id = payload.get("workflow_id", f"workflow_{len(self.active_workflows) + 1}")
        workflow_type = payload.get("workflow_type", "standard")
        data = payload.get("data", {})
        
        # Create workflow context
        workflow = {
            "id": workflow_id,
            "type": workflow_type,
            "status": "running",
            "data": data,
            "current_engine": "engine1",
            "results": {},
            "started_at": asyncio.get_event_loop().time()
        }
        
        self.active_workflows[workflow_id] = workflow
        
        try:
            # Execute through engine pipeline
            result = await self._run_engine_pipeline(workflow)
            
            workflow["status"] = "completed"
            workflow["results"] = result
            workflow["completed_at"] = asyncio.get_event_loop().time()
            
            return {
                "workflow_id": workflow_id,
                "status": "completed",
                "results": result
            }
            
        except Exception as e:
            workflow["status"] = "failed"
            workflow["error"] = str(e)
            workflow["failed_at"] = asyncio.get_event_loop().time()
            
            self.logger.error(f"Workflow {workflow_id} failed: {e}")
            raise
    
    async def _run_engine_pipeline(self, workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Run data through the engine pipeline"""
        data = workflow["data"]
        results = {}
        
        # Engine 1: Workflow Execution
        if "engine1" in self.engines:
            workflow["current_engine"] = "engine1"
            data = await self.engines["engine1"].process(data)
            results["engine1"] = data
        
        # Engine 2: Data Processing
        if "engine2" in self.engines:
            workflow["current_engine"] = "engine2"
            data = await self.engines["engine2"].process(data)
            results["engine2"] = data
        
        # Engine 3: AI Reasoning
        if "engine3" in self.engines:
            workflow["current_engine"] = "engine3"
            data = await self.engines["engine3"].process(data)
            results["engine3"] = data
        
        # Engine 4: Action Execution
        if "engine4" in self.engines:
            workflow["current_engine"] = "engine4"
            data = await self.engines["engine4"].process(data)
            results["engine4"] = data
        
        return results
    
    async def _list_engines(self) -> Dict[str, Any]:
        """List all available engines"""
        engines_info = {}
        
        for engine_name, engine in self.engines.items():
            engines_info[engine_name] = {
                "name": engine_name,
                "class": engine.__class__.__name__,
                "status": "active" if hasattr(engine, 'active') and engine.active else "inactive",
                "capabilities": getattr(engine, 'capabilities', []),
                "config": self.engine_configs.get(engine_name, {})
            }
        
        return {
            "engines": engines_info,
            "total_count": len(engines_info)
        }
    
    async def _get_engine_status(self, engine_id: str) -> Dict[str, Any]:
        """Get status of a specific engine"""
        if engine_id not in self.engines:
            raise ValueError(f"Engine {engine_id} not found")
        
        engine = self.engines[engine_id]
        
        return {
            "engine_id": engine_id,
            "status": "active" if getattr(engine, 'active', False) else "inactive",
            "processed_requests": getattr(engine, 'processed_requests', 0),
            "last_activity": getattr(engine, 'last_activity', None)
        }
    
    async def _get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get status of a workflow"""
        if workflow_id not in self.active_workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        return self.active_workflows[workflow_id]
    
    async def _stop_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Stop a running workflow"""
        if workflow_id not in self.active_workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        workflow = self.active_workflows[workflow_id]
        workflow["status"] = "stopped"
        workflow["stopped_at"] = asyncio.get_event_loop().time()
        
        return {
            "workflow_id": workflow_id,
            "status": "stopped"
        }


class MockEngine:
    """Mock engine implementation for testing"""
    
    def __init__(self, name: str, engine_class: str, config: Dict[str, Any]):
        self.name = name
        self.engine_class = engine_class
        self.config = config
        self.active = False
        self.processed_requests = 0
        self.last_activity = None
        
    async def initialize(self):
        """Initialize the mock engine"""
        self.active = True
        logger.info(f"Mock engine {self.name} initialized")
        
    async def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process data through the mock engine"""
        self.processed_requests += 1
        self.last_activity = asyncio.get_event_loop().time()
        
        # Mock processing based on engine type
        if "workflow" in self.engine_class.lower():
            data["workflow_processed"] = True
            data["engine"] = self.name
        elif "data" in self.engine_class.lower():
            data["data_processed"] = True
            data["transformations"] = ["normalize", "enrich"]
        elif "ai" in self.engine_class.lower():
            data["ai_processed"] = True
            data["reasoning_result"] = "analysis_complete"
        elif "action" in self.engine_class.lower():
            data["actions_executed"] = True
            data["final_result"] = "workflow_complete"
        
        # Add processing delay to simulate real work
        await asyncio.sleep(0.1)
        
        return data
        
    async def shutdown(self):
        """Shutdown the mock engine"""
        self.active = False
        logger.info(f"Mock engine {self.name} shutdown")
