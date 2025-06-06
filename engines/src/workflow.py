"""
Implements the workflow graph for the System Engine Control using LangGraph.
"""
import logging
from langgraph.graph import StateGraph, END
from typing import Dict, Any

from .schemas import EngineState
from .router import route_by_mode, check_permissions
from .engines import Engine1, Engine2, Engine3, Engine4

# Set up logging
logger = logging.getLogger("engine_control.workflow")


class WorkflowBuilder:
    """Builder for creating the LangGraph workflow."""
    
    def __init__(self, ai_council=None, rag_system=None, tools_system=None, config=None):
        """
        Initialize the workflow builder.
        
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
        
        self.engines = {
            "engine_1": Engine1(
                ai_council=ai_council,
                rag_system=rag_system,
                tools_system=tools_system,
                config=config
            ),
            "engine_2": Engine2(
                ai_council=ai_council,
                rag_system=rag_system,
                tools_system=tools_system,
                config=config
            ),
            "engine_3": Engine3(
                ai_council=ai_council,
                rag_system=rag_system,
                tools_system=tools_system,
                config=config
            ),
            "engine_4": Engine4(
                ai_council=ai_council,
                rag_system=rag_system,
                tools_system=tools_system,
                config=config
            )
        }
    
    def build_workflow(self) -> StateGraph:
        """
        Build the workflow graph.
        
        Returns:
            The compiled StateGraph object
        """
        # Create the workflow graph
        workflow = StateGraph(EngineState)
        
        # Add nodes
        workflow.add_node("router", self._wrap_router)
        workflow.add_node("permissions", check_permissions)
        workflow.add_node("engine_1", self._wrap_engine("engine_1"))
        workflow.add_node("engine_2", self._wrap_engine("engine_2"))
        workflow.add_node("engine_3", self._wrap_engine("engine_3"))
        workflow.add_node("engine_4", self._wrap_engine("engine_4"))
        
        # Set the entry point
        workflow.set_entry_point("permissions")
        
        # Connect permissions check to router
        workflow.add_edge("permissions", "router")
        
        # Add conditional edges from router to engines
        workflow.add_conditional_edges(
            "router",
            self._route_conditional
        )
        
        # Add edges from engines to END
        workflow.add_edge("engine_1", END)
        workflow.add_edge("engine_2", END)
        workflow.add_edge("engine_3", END)
        workflow.add_edge("engine_4", END)
        
        return workflow
    
    def _wrap_router(self, state: EngineState) -> str:
        """Wrap the router function to log the decision."""
        engine_node = route_by_mode(state)
        logger.info(f"Routing to {engine_node}")
        state["current_engine"] = engine_node
        return engine_node
    
    def _wrap_engine(self, engine_key: str):
        """Wrap an engine's process method."""
        engine = self.engines[engine_key]
        
        def process_with_engine(state: EngineState) -> Dict[str, Any]:
            logger.info(f"Processing with {engine_key}")
            return engine.process(state)
        
        return process_with_engine
    
    def _route_conditional(self, state: EngineState) -> Dict[str, str]:
        """Create the conditional routing dictionary."""
        engine_node = route_by_mode(state)
        return engine_node


def create_workflow(ai_council=None, rag_system=None, tools_system=None, config=None) -> StateGraph:
    """
    Create a workflow graph for the System Engine Control.
    
    Args:
        ai_council: The AI Council component
        rag_system: The RAG System component
        tools_system: The Tools/Packages System component
        config: Configuration options
        
    Returns:
        The compiled workflow graph
    """
    builder = WorkflowBuilder(
        ai_council=ai_council,
        rag_system=rag_system,
        tools_system=tools_system,
        config=config
    )
    return builder.build_workflow()