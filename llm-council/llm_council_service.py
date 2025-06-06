"""
LLM Council service implementation.
Manages multi-agent orchestration and specialist prompt logic.
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional
import json
from datetime import datetime
import uuid
from pathlib import Path

try:
    from ..base_service import BaseService, ServiceRequest, ServiceResponse
except ImportError:
    # For when running as a script
    import sys
    sys.path.append(str(Path(__file__).parent.parent))
    from base_service import BaseService, ServiceRequest, ServiceResponse

logger = logging.getLogger(__name__)

class LLMCouncilService(BaseService):
    """
    Service for multi-agent orchestration and specialist reasoning.
    Manages AI council agents, specialist prompts, and collaborative decision-making.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("llm-council", "1.0.0", config)
        self.agents = {}
        self.active_sessions = {}
        self.specialist_prompts = {}
        
    def get_description(self) -> str:
        return "Multi-agent orchestration and specialist prompt management for collaborative AI reasoning"
    
    def get_capabilities(self) -> List[str]:
        return [
            "multi_agent_orchestration",
            "specialist_reasoning",
            "collaborative_decision_making",
            "context_sharing",
            "prompt_management"
        ]
    
    def get_endpoints(self) -> Dict[str, str]:
        return {
            "create_session": "/council/session/create",
            "process_query": "/council/process",
            "get_session": "/council/session/{session_id}",
            "list_agents": "/council/agents",
            "agent_status": "/council/agents/{agent_id}/status"
        }
    
    async def initialize(self) -> bool:
        """Initialize the LLM Council service"""
        try:
            # Load specialist prompts
            await self._load_specialist_prompts()
            
            # Initialize core agents
            await self._initialize_agents()
            
            self.logger.info(f"LLM Council service initialized with {len(self.agents)} agents")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize LLM Council service: {e}")
            return False
    
    async def process_request(self, request: ServiceRequest) -> ServiceResponse:
        """Process incoming service request"""
        try:
            action = request.action
            payload = request.payload
            
            if action == "create_session":
                result = await self._create_session(payload)
            elif action == "process_query":
                result = await self._process_query(payload)
            elif action == "get_session":
                result = await self._get_session(payload.get("session_id"))
            elif action == "list_agents":
                result = await self._list_agents()
            elif action == "get_agent_status":
                result = await self._get_agent_status(payload.get("agent_id"))
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
        # End all active sessions
        for session_id in list(self.active_sessions.keys()):
            await self._end_session(session_id)
        
        # Shutdown agents
        for agent in self.agents.values():
            if hasattr(agent, 'shutdown'):
                await agent.shutdown()
        
        self.logger.info("LLM Council service shutdown complete")
    
    async def _load_specialist_prompts(self):
        """Load specialist prompts from configuration"""
        # This would load from ai-council-specialist-prompts.md in production
        self.specialist_prompts = {
            "analyst": {
                "role": "Data Analyst",
                "expertise": "Data analysis, pattern recognition, statistical reasoning",
                "prompt_template": "As a data analyst, analyze the following information and provide insights: {query}"
            },
            "strategist": {
                "role": "Strategic Advisor", 
                "expertise": "Strategic planning, decision-making, risk assessment",
                "prompt_template": "As a strategic advisor, evaluate the following scenario and recommend actions: {query}"
            },
            "researcher": {
                "role": "Research Specialist",
                "expertise": "Information gathering, fact-checking, knowledge synthesis",
                "prompt_template": "As a research specialist, investigate and provide comprehensive information about: {query}"
            },
            "coordinator": {
                "role": "Council Coordinator",
                "expertise": "Orchestration, consensus building, decision synthesis",
                "prompt_template": "As the council coordinator, synthesize the following specialist inputs and provide a unified recommendation: {specialist_inputs}"
            }
        }
        
        self.logger.info(f"Loaded {len(self.specialist_prompts)} specialist prompts")
    
    async def _initialize_agents(self):
        """Initialize the AI council agents"""
        for agent_name, prompt_config in self.specialist_prompts.items():
            try:
                agent = CouncilAgent(agent_name, prompt_config)
                await agent.initialize()
                self.agents[agent_name] = agent
                
                self.logger.info(f"Initialized agent: {agent_name}")
                
            except Exception as e:
                self.logger.error(f"Failed to initialize agent {agent_name}: {e}")
    
    async def _create_session(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new council session"""
        session_id = payload.get("session_id", str(uuid.uuid4()))
        query = payload.get("query", "")
        context = payload.get("context", {})
        agents_requested = payload.get("agents", list(self.agents.keys()))
        
        # Filter to available agents
        available_agents = [agent for agent in agents_requested if agent in self.agents]
        
        session = {
            "id": session_id,
            "query": query,
            "context": context,
            "agents": available_agents,
            "status": "created",
            "created_at": datetime.utcnow().isoformat(),
            "responses": {},
            "final_recommendation": None
        }
        
        self.active_sessions[session_id] = session
        
        return {
            "session_id": session_id,
            "status": "created",
            "agents_assigned": available_agents
        }
    
    async def _process_query(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process a query through the AI council"""
        session_id = payload.get("session_id")
        if not session_id:
            # Create new session if none provided
            session_result = await self._create_session(payload)
            session_id = session_result["session_id"]
        
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.active_sessions[session_id]
        session["status"] = "processing"
        
        try:
            # Gather specialist responses
            specialist_responses = await self._gather_specialist_responses(session)
            session["responses"] = specialist_responses
            
            # Coordinate final recommendation
            final_recommendation = await self._coordinate_recommendation(session, specialist_responses)
            session["final_recommendation"] = final_recommendation
            session["status"] = "completed"
            session["completed_at"] = datetime.utcnow().isoformat()
            
            return {
                "session_id": session_id,
                "status": "completed",
                "specialist_responses": specialist_responses,
                "final_recommendation": final_recommendation
            }
            
        except Exception as e:
            session["status"] = "failed"
            session["error"] = str(e)
            session["failed_at"] = datetime.utcnow().isoformat()
            raise
    
    async def _gather_specialist_responses(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Gather responses from all assigned specialist agents"""
        query = session["query"]
        context = session["context"]
        agents = session["agents"]
        
        responses = {}
        
        # Process agents concurrently
        tasks = []
        for agent_name in agents:
            if agent_name in self.agents:
                task = self._get_agent_response(agent_name, query, context)
                tasks.append((agent_name, task))
        
        # Wait for all responses
        for agent_name, task in tasks:
            try:
                response = await task
                responses[agent_name] = response
            except Exception as e:
                self.logger.error(f"Agent {agent_name} failed: {e}")
                responses[agent_name] = {
                    "status": "error",
                    "error": str(e)
                }
        
        return responses
    
    async def _get_agent_response(self, agent_name: str, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Get response from a specific agent"""
        agent = self.agents[agent_name]
        return await agent.process_query(query, context)
    
    async def _coordinate_recommendation(self, session: Dict[str, Any], specialist_responses: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate final recommendation from specialist responses"""
        if "coordinator" in self.agents:
            # Use coordinator agent to synthesize responses
            coordinator = self.agents["coordinator"]
            
            coordination_input = {
                "query": session["query"],
                "specialist_inputs": specialist_responses,
                "context": session["context"]
            }
            
            return await coordinator.coordinate(coordination_input)
        else:
            # Simple aggregation if no coordinator
            successful_responses = {
                name: resp for name, resp in specialist_responses.items()
                if resp.get("status") == "success"
            }
            
            return {
                "status": "success",
                "recommendation": "Multiple specialist perspectives gathered",
                "summary": f"Received {len(successful_responses)} successful specialist responses",
                "specialist_count": len(successful_responses)
            }
    
    async def _get_session(self, session_id: str) -> Dict[str, Any]:
        """Get session information"""
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        return self.active_sessions[session_id]
    
    async def _list_agents(self) -> Dict[str, Any]:
        """List all available agents"""
        agents_info = {}
        
        for agent_name, agent in self.agents.items():
            agents_info[agent_name] = {
                "name": agent_name,
                "role": agent.role,
                "expertise": agent.expertise,
                "status": "active" if getattr(agent, 'active', False) else "inactive",
                "queries_processed": getattr(agent, 'queries_processed', 0)
            }
        
        return {
            "agents": agents_info,
            "total_count": len(agents_info)
        }
    
    async def _get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """Get status of a specific agent"""
        if agent_id not in self.agents:
            raise ValueError(f"Agent {agent_id} not found")
        
        agent = self.agents[agent_id]
        
        return {
            "agent_id": agent_id,
            "role": agent.role,
            "status": "active" if getattr(agent, 'active', False) else "inactive",
            "queries_processed": getattr(agent, 'queries_processed', 0),
            "last_activity": getattr(agent, 'last_activity', None)
        }
    
    async def _end_session(self, session_id: str):
        """End a council session"""
        if session_id in self.active_sessions:
            session = self.active_sessions[session_id]
            session["status"] = "ended"
            session["ended_at"] = datetime.utcnow().isoformat()


class CouncilAgent:
    """Individual AI council agent implementation"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.role = config.get("role", name)
        self.expertise = config.get("expertise", "")
        self.prompt_template = config.get("prompt_template", "")
        self.active = False
        self.queries_processed = 0
        self.last_activity = None
        
    async def initialize(self):
        """Initialize the agent"""
        self.active = True
        logger.info(f"Council agent {self.name} initialized")
        
    async def process_query(self, query: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process a query and return specialist response"""
        self.queries_processed += 1
        self.last_activity = datetime.utcnow().isoformat()
        
        # Mock specialist processing - in production this would call actual LLM
        await asyncio.sleep(0.2)  # Simulate processing time
        
        # Generate mock response based on agent role
        response = {
            "status": "success",
            "agent": self.name,
            "role": self.role,
            "analysis": f"{self.role} analysis of: {query}",
            "recommendations": [
                f"Recommendation 1 from {self.role}",
                f"Recommendation 2 from {self.role}"
            ],
            "confidence": 0.85,
            "processing_time": 0.2
        }
        
        return response
        
    async def coordinate(self, coordination_input: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate multiple specialist responses (for coordinator agent)"""
        specialist_inputs = coordination_input.get("specialist_inputs", {})
        query = coordination_input.get("query", "")
        
        # Mock coordination logic
        successful_responses = [
            resp for resp in specialist_inputs.values()
            if resp.get("status") == "success"
        ]
        
        return {
            "status": "success",
            "recommendation": f"Coordinated recommendation for: {query}",
            "synthesis": "Combined insights from specialist agents",
            "specialist_count": len(successful_responses),
            "confidence": 0.9,
            "coordinator": self.name
        }
        
    async def shutdown(self):
        """Shutdown the agent"""
        self.active = False
        logger.info(f"Council agent {self.name} shutdown")
