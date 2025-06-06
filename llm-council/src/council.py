"""
AI Council - Multi-Agent System for Space Project
Uses AutoGen for agent coordination and communication
"""

import os
import logging
import uuid
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

# Import AutoGen functionality
import autogen
from autogen.agentchat.agent import Agent

# Import our components
from core.ai-council.src.mode_controller import mode_controller, SystemMode
from core.ai-council.agents.tool_agent import ToolAgent
from core.packages.permissions.base_permissions import ResourceType, PermissionLevel
from core.rag_system.rag_system import RAGSystem, QueryOptions

# Setup logging
logger = logging.getLogger(__name__)

class AICouncil:
    """
    Manages a council of AI agents that work together to accomplish complex tasks.
    Based on AutoGen's multi-agent architecture with integrated permission system.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the AI Council with configuration and agents
        
        Args:
            config: Configuration dictionary containing LLM settings, 
                   agent configurations, and council parameters
        """
        self.config = config
        self.agents = {}
        self.conversation_history = []
        self.llm_config = config.get("llm_config", {})
        self.rag_system = RAGSystem(config.get("rag_config", {}))
        self._initialize_council()
        logger.info("AI Council initialized successfully")
    
    def _initialize_council(self) -> None:
        """
        Initialize all agents in the council based on the configuration
        """
        # Create the decision maker agent (the central coordinator)
        self._create_decision_maker()
        
        # Create specialist agents
        self._create_specialist_agents()
        
        # Create the tool agent
        self._create_tool_agent()
        
        # Initialize agent connections/groupchat if needed
        self._setup_agent_connections()
    
    def _create_decision_maker(self) -> None:
        """Create the Decision Maker agent that coordinates other agents"""
        from core.ai_council.agents.decision_maker import DecisionMakerAgent
        
        decision_maker_config = self.config.get("decision_maker", {})
        self.decision_maker = DecisionMakerAgent(
            name="DecisionMaker",
            system_message=decision_maker_config.get("system_message", 
                "You are the Decision Maker that coordinates the AI Council."),
            llm_config=self.llm_config,
        )
        self.agents["decision_maker"] = self.decision_maker
        logger.info("Decision Maker agent created")
    
    def _create_specialist_agents(self) -> None:
        """Create the specialist agents based on configuration"""
        specialist_configs = self.config.get("specialists", {})
        
        # Import all specialist agent classes
        from core.ai_council.agents.specialist_agents import (
            ResearchAgent, CreativeAgent, LogicalAgent, 
            EthicalAgent, ImplementationAgent
        )
        
        # Map of agent types to their classes
        agent_classes = {
            "research": ResearchAgent,
            "creative": CreativeAgent,
            "logical": LogicalAgent,
            "ethical": EthicalAgent,
            "implementation": ImplementationAgent
        }
        
        # Create each specialist agent
        for agent_type, agent_config in specialist_configs.items():
            if agent_type in agent_classes:
                agent_class = agent_classes[agent_type]
                agent = agent_class(
                    name=agent_config.get("name", f"{agent_type.capitalize()}Agent"),
                    system_message=agent_config.get("system_message", ""),
                    llm_config=self.llm_config,
                )
                self.agents[agent_type] = agent
                logger.info(f"Created specialist agent: {agent_type}")
    
    def _create_tool_agent(self) -> None:
        """Create the Tool Agent for handling ability execution"""
        tool_config = self.config.get("tool_agent", {})
        
        self.tool_agent = ToolAgent(
            name="ToolAgent",
            system_message=tool_config.get("system_message", 
                "You are the Tool Agent that helps execute abilities and tools."),
            llm_config=self.llm_config,
            access_level="basic"  # Start with basic access
        )
        
        self.agents["tool_agent"] = self.tool_agent
        logger.info("Tool Agent created")
    
    def _setup_agent_connections(self) -> None:
        """Setup connections between agents (groupchat or direct)"""
        # Determine if we're using groupchat or direct communication
        use_groupchat = self.config.get("use_groupchat", True)
        
        if use_groupchat:
            # Create a group chat with all agents
            self.groupchat = autogen.GroupChat(
                agents=list(self.agents.values()),
                messages=[],
                max_round=self.config.get("max_rounds", 10)
            )
            self.manager = autogen.GroupChatManager(
                groupchat=self.groupchat,
                llm_config=self.llm_config
            )
            logger.info("Group chat configuration completed")
        else:
            # Set up direct connections between decision maker and specialists
            # This would be custom implementation based on AutoGen capabilities
            logger.info("Direct agent connections configured")
    
    async def process_request(
        self, 
        user_request: str, 
        mode: str = "archivist",
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a user request through the AI Council
        
        Args:
            user_request: The user's query or request
            mode: The engine mode (archivist, orchestrator, godfather, entity)
            session_id: Optional session ID (generated if not provided)
            user_id: Optional user ID for permission checks
            context: Additional context for the request
            
        Returns:
            Dict containing the response and metadata
        """
        # Generate IDs if not provided
        session_id = session_id or str(uuid.uuid4())
        user_id = user_id or session_id
        
        logger.info(f"Processing request in {mode} mode: {user_request[:50]}...")
        
        # Record the start time for performance tracking
        start_time = datetime.now()
        
        try:
            # Set up the session mode
            current_mode = mode_controller.start_session(session_id, mode)
            
            # Update tool agent's access level based on mode
            await self._update_tool_agent_access(session_id)
            
            # Verify the user has appropriate permissions for this mode
            if not await self._verify_mode_permissions(user_id, current_mode.value):
                return {
                    "status": "error",
                    "error": f"User does not have permission to use {current_mode.value} mode",
                    "processing_time": (datetime.now() - start_time).total_seconds(),
                    "mode": mode
                }
            
            # Retrieve relevant context using RAG system
            rag_context = await self._get_rag_context(user_request, session_id)
            
            # Create an appropriate request based on the mode
            enriched_request = self._enrich_request(
                user_request, 
                mode, 
                rag_context, 
                context
            )
            
            # Process through the council (either groupchat or decision maker)
            if hasattr(self, 'groupchat'):
                response = await self._process_with_groupchat(enriched_request, session_id)
            else:
                response = await self._process_with_decision_maker(enriched_request, session_id)
            
            # Structure the result
            result = {
                "status": "success",
                "response": response,
                "processing_time": (datetime.now() - start_time).total_seconds(),
                "mode": current_mode.value,
                "session_id": session_id
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "processing_time": (datetime.now() - start_time).total_seconds(),
                "mode": mode,
                "session_id": session_id
            }
    
    async def _update_tool_agent_access(self, session_id: str) -> None:
        """Update the Tool Agent's access level based on session mode"""
        mode = mode_controller.get_current_mode(session_id)
        
        # Map modes to access levels
        access_levels = {
            SystemMode.ARCHIVIST: "basic",
            SystemMode.ORCHESTRATOR: "intermediate",
            SystemMode.GODFATHER: "expert",
            SystemMode.ENTITY: "superhuman"
        }
        
        # Set the appropriate access level
        access_level = access_levels.get(mode, "basic")
        self.tool_agent.set_access_level(access_level)
        
        logger.info(f"Updated Tool Agent access level to {access_level} for mode {mode.value}")
    
    async def _verify_mode_permissions(self, user_id: str, mode_name: str) -> bool:
        """
        Verify the user has permission to use the requested mode
        
        Args:
            user_id: ID of the user
            mode_name: Name of the requested mode
            
        Returns:
            Whether the user has permission
        """
        # This would typically check against a user database or authentication system
        # For now, we'll allow all modes for simplicity
        return True
    
    async def _get_rag_context(self, query: str, session_id: str) -> str:
        """
        Get relevant context from the RAG system
        
        Args:
            query: The user's query
            session_id: Current session ID
            
        Returns:
            Relevant context as a string
        """
        # Get the current mode
        mode = mode_controller.get_current_mode(session_id)
        
        # Configure RAG options based on mode
        options = QueryOptions(
            top_k=5,
            filter_by_relevance=True,
            min_relevance_score=0.7,
            include_metadata=True
        )
        
        # Get relevant documents
        relevant_docs = await self.rag_system.query(query, options)
        
        if not relevant_docs:
            return ""
            
        # Format the context
        context_sections = []
        
        for i, doc in enumerate(relevant_docs):
            context = f"Document {i+1}: {doc['content']}"
            if 'metadata' in doc and mode.value in ("godfather", "entity"):
                # Include metadata for advanced modes
                meta = doc['metadata']
                context += f"\nMetadata: {meta}"
                
            context_sections.append(context)
        
        return "\n\n".join(context_sections)
    
    def _enrich_request(
        self, 
        user_request: str, 
        mode: str, 
        rag_context: str = "",
        additional_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Enrich the user request with context based on the mode
        
        Args:
            user_request: Original user request
            mode: System mode
            rag_context: Context from RAG system
            additional_context: Any additional context
            
        Returns:
            Enriched request
        """
        # Mode-specific enrichment logic
        mode_contexts = {
            "archivist": "Focus on information retrieval and summarization. ",
            "orchestrator": "Balance between information and problem-solving. ",
            "godfather": "Focus on strategic advice and sophisticated problem-solving. ",
            "entity": "Provide comprehensive solutions with deep domain expertise. "
        }
        
        # Add the mode context to the request
        mode_context = mode_contexts.get(mode.lower(), "")
        
        # Build the enriched request
        enriched_request = f"{mode_context}User request: {user_request}"
        
        # Add RAG context if available
        if rag_context:
            enriched_request += f"\n\nRelevant context information:\n{rag_context}"
        
        # Add additional context if provided
        if additional_context:
            # Format any additional context
            context_str = "\n".join([f"{k}: {v}" for k, v in additional_context.items()])
            enriched_request += f"\n\nAdditional context:\n{context_str}"
        
        return enriched_request
    
    async def _process_with_groupchat(self, request: str, session_id: str) -> str:
        """
        Process the request using the group chat configuration
        
        Args:
            request: The enriched request
            session_id: Current session ID
            
        Returns:
            The response from the group chat
        """
        # Initialize a new chat for this request
        self.groupchat.messages = []
        
        # Add context about the current mode
        mode = mode_controller.get_current_mode(session_id)
        mode_description = mode_controller.get_mode_description(mode)
        
        # Create a system message about current mode capabilities
        system_msg = (
            f"Processing in {mode.value} mode. "
            f"Mode description: {mode_description['description']} "
            f"Available ability level: {mode_description['ability_level']}"
        )
        
        # Add the system message to the group chat
        self.groupchat.messages.append({
            "role": "system",
            "content": system_msg
        })
        
        # Start the group chat with the user's request
        response = await self.manager.run(request)
        
        # Extract and return the final response
        return response
    
    async def _process_with_decision_maker(self, request: str, session_id: str) -> str:
        """
        Process the request through the decision maker's coordination
        
        Args:
            request: The enriched request
            session_id: Current session ID
            
        Returns:
            The response from the decision maker
        """
        # Get current mode information
        mode = mode_controller.get_current_mode(session_id)
        
        # This would implement a custom workflow where the decision maker
        # coordinates with other agents directly
        response = await self.decision_maker.process_with_specialists(
            request=request,
            agents=self.agents,
            mode=mode.value,
            session_id=session_id
        )
        return response
    
    def get_agent(self, agent_type: str) -> Optional[Agent]:
        """Get a specific agent by type"""
        return self.agents.get(agent_type)
    
    async def change_mode(
        self, 
        new_mode: str, 
        session_id: str, 
        user_id: str
    ) -> Dict[str, Any]:
        """
        Change the mode for a session
        
        Args:
            new_mode: New mode to set
            session_id: Session ID
            user_id: ID of the user making the change
            
        Returns:
            Result of the mode change
        """
        try:
            # Verify the user has permission to change to this mode
            if not await self._verify_mode_permissions(user_id, new_mode):
                return {
                    "status": "error",
                    "error": f"User does not have permission to use {new_mode} mode"
                }
            
            # Change the mode
            success = mode_controller.change_mode(new_mode, session_id)
            
            if not success:
                return {
                    "status": "error",
                    "error": f"Failed to change mode to {new_mode}"
                }
                
            # Update tool agent's access level
            await self._update_tool_agent_access(session_id)
            
            # Get description of the new mode
            mode = mode_controller.get_current_mode(session_id)
            mode_description = mode_controller.get_mode_description(mode)
            
            return {
                "status": "success",
                "mode": mode.value,
                "description": mode_description["description"],
                "ability_level": mode_description["ability_level"]
            }
            
        except Exception as e:
            logger.error(f"Error changing mode: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def list_available_modes(self, user_id: str) -> Dict[str, Any]:
        """
        Get a list of available modes for a user
        
        Args:
            user_id: ID of the user
            
        Returns:
            Dict with available modes
        """
        # Get all modes
        all_modes = mode_controller.list_available_modes()
        
        # Filter modes based on user permissions
        available_modes = []
        for mode_info in all_modes:
            mode_name = mode_info["mode"]
            if await self._verify_mode_permissions(user_id, mode_name):
                available_modes.append(mode_info)
        
        return {
            "status": "success",
            "modes": available_modes
        }
    
    async def get_ability_access(self, session_id: str) -> Dict[str, Any]:
        """
        Get information about available abilities for the current mode
        
        Args:
            session_id: Session ID
            
        Returns:
            Dict with available abilities
        """
        # Get allowed abilities for the current mode
        allowed_abilities = mode_controller.get_allowed_abilities(session_id)
        
        return {
            "status": "success",
            "mode": mode_controller.get_current_mode(session_id).value,
            "abilities": allowed_abilities
        }

# Factory function to create an AI Council instance
def create_council(config: Dict[str, Any]) -> AICouncil:
    """Create an AI Council instance with the provided configuration"""
    return AICouncil(config)