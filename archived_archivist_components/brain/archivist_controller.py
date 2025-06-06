"""
Archivist Brain Controller - Central orchestration system for the Archivist cognitive architecture.
Implements autonomous cognitive cycles and manages the flow of information between memory, reasoning, and knowledge systems.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta
import json

from .controller import BrainController, CognitiveContext
from .memory import MemorySystem
from .reasoning import ReasoningEngine
from .knowledge import KnowledgeManager
from ..enhanced_event_bus import EventBus, EventPriority, EventStatus, EventTaxonomy
from core.perception import PerceptionModule
from core.nlu import NLUModule
from core.nlg import NLGModule
from core.tool_integration import ToolIntegrationModule

logger = logging.getLogger(__name__)

@dataclass
class CognitiveState:
    """Represents the current cognitive state of the Archivist system"""
    active_goals: List[str]
    attention_focus: str
    working_memory: Dict[str, Any]
    current_context: CognitiveContext
    last_updated: datetime
    processing_state: str  # "idle", "processing", "learning", "reasoning", etc.


class ArchivistController(BrainController):
    """
    Advanced brain controller implementing the Archivist cognitive architecture.
    Extends the basic BrainController with autonomous processing capabilities.
    """
    
    def __init__(self):
        super().__init__()
        self.cognitive_state = None
        self.cycle_interval = 5.0  # seconds between autonomous cognitive cycles
        self.background_tasks = set()
        # New modules
        self.perception = PerceptionModule()
        self.nlu = NLUModule()
        self.nlg = NLGModule()
        self.tool_integration = ToolIntegrationModule()
        self.logger = logging.getLogger(__name__)

    async def initialize(self):
        """Initialize the Archivist controller and all cognitive subsystems"""
        await super().initialize()
        
        # Additional event subscriptions for autonomous operation
        self.event_bus.subscribe("user.interaction", self._handle_user_interaction)
        self.event_bus.subscribe("system.perception", self._handle_perception)
        self.event_bus.subscribe("knowledge.updated", self._handle_knowledge_update)
        self.event_bus.subscribe("memory.consolidated", self._handle_memory_consolidation)
        
        # Initialize cognitive state
        self.cognitive_state = CognitiveState(
            active_goals=["maintain_system"],
            attention_focus="initialization",
            working_memory={},
            current_context=CognitiveContext(
                user_id="system",
                session_id="initialization",
                request_id="initialization",
                metadata={}
            ),
            last_updated=datetime.now(),
            processing_state="idle"
        )
        
        # Start autonomous cognitive cycle
        task = asyncio.create_task(self._run_cognitive_cycle())
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)
        
        logger.info("Archivist controller initialized and autonomous cycle started")
    
    async def process_input(self, user_input: Dict[str, Any], context: CognitiveContext) -> Dict[str, Any]:
        """Process user input through the cognitive architecture"""
        self.cognitive_state.processing_state = "processing"
        self.cognitive_state.current_context = context
        self.cognitive_state.attention_focus = "user_input"
        self.cognitive_state.last_updated = datetime.now()

        # Perception: normalize input
        normalized = self.perception.normalize_event(user_input)
        self.logger.info(f"Perceived input: {normalized}")

        # NLU: parse intent/entities
        nlu_result = self.nlu.parse(normalized["content"])
        self.logger.info(f"NLU result: {nlu_result}")

        # Store input in memory
        memory_id = await self.memory.store({
            "content": normalized["content"],
            "memory_type": "short_term",
            "metadata": {
                "type": "user_input",
                "timestamp": datetime.now().isoformat(),
                "session_id": context.session_id,
                "intent": nlu_result["intent"],
                "entities": nlu_result["entities"]
            }
        }, context)

        # Retrieve relevant knowledge and memories
        relevant_memories = await self.memory.retrieve({
            "content": normalized["content"],
            "limit": 10
        }, context)

        # Generate reasoning about the input
        reasoning_task = {
            "operation": "infer",
            "data": {
                "query": normalized["content"],
                "relevant_memories": [mem.id for mem in relevant_memories],
                "intent": nlu_result["intent"],
                "entities": nlu_result["entities"]
            }
        }
        inference_result = await self.reasoning.process(reasoning_task, context)

        # Tool integration: optionally invoke tools based on intent
        tool_result = None
        if nlu_result["intent"] in self.tool_integration.tools:
            tool_result = self.tool_integration.invoke(nlu_result["intent"], nlu_result["entities"])
            self.logger.info(f"Tool invoked for intent {nlu_result['intent']}: {tool_result}")

        # NLG: generate response
        nlg_context = {
            "input": normalized["content"],
            "reasoning": inference_result,
            "tool_result": tool_result,
            "memories": [mem.id for mem in relevant_memories]
        }
        response = self.nlg.generate(nlg_context)
        self.logger.info(f"NLG response: {response}")

        # Store the entire interaction
        await self.memory.store({
            "content": {
                "input": normalized,
                "reasoning": inference_result,
                "tool_result": tool_result,
                "nlg_response": response,
                "memories_used": [mem.id for mem in relevant_memories]
            },
            "memory_type": "short_term",
            "metadata": {
                "type": "interaction",
                "timestamp": datetime.now().isoformat(),
                "session_id": context.session_id
            }
        }, context)

        self.cognitive_state.processing_state = "idle"
        self.cognitive_state.last_updated = datetime.now()

        await self.event_bus.publish("interaction.processed", {
            "user_input": user_input,
            "response": response,
            "context": context
        })

        return {"response": response, "tool_result": tool_result, "reasoning": inference_result}
    
    async def _run_cognitive_cycle(self):
        """Execute the autonomous cognitive cycle at regular intervals"""
        logger.info("Starting autonomous cognitive cycle")
        while True:
            try:
                if self.cognitive_state.processing_state == "idle":
                    await self._execute_cognitive_cycle()
                await asyncio.sleep(self.cycle_interval)
            except Exception as e:
                logger.error(f"Error in cognitive cycle: {str(e)}", exc_info=True)
                await asyncio.sleep(self.cycle_interval * 2)  # Longer sleep on error
    
    async def _execute_cognitive_cycle(self):
        """Run a single iteration of the autonomous cognitive cycle"""
        try:
            # Update processing state
            self.cognitive_state.processing_state = "thinking"
            context = self._create_system_context()
            cycle_start_time = datetime.now()
            
            # Publish cycle start event
            cycle_id = await self.event_bus.publish(
                "cognitive.cycle.started", 
                {
                    "timestamp": cycle_start_time.isoformat(),
                    "context": context.__dict__
                },
                priority=EventPriority.HIGH
            )
            
            # 1. Perception phase - gather current state
            self.cognitive_state.attention_focus = "perception"
            system_state = await self._gather_system_state(context)
            
            # Store system state perception in memory
            await self.memory.store({
                "content": {
                    "type": "system_state",
                    "data": system_state
                },
                "memory_type": "short_term",
                "metadata": {
                    "type": "system_perception",
                    "timestamp": datetime.now().isoformat(),
                    "cognitive_cycle": cycle_id
                }
            }, context)
            
            # 2. Memory consolidation - process short-term memories
            self.cognitive_state.attention_focus = "memory_consolidation"
            # Retrieve memories ready for consolidation (created > 24h ago with high importance)
            memory_task = {
                "operation": "retrieve",
                "query": {
                    "memory_type": "short_term",
                    "filter": {
                        "created_before": (datetime.now() - timedelta(hours=24)).isoformat(),
                        "importance_above": 0.7
                    },
                    "limit": 20
                }
            }
            
            # Let the memory system handle the consolidation
            memories_to_consolidate = await self.memory.process(memory_task, context)
            
            if memories_to_consolidate and len(memories_to_consolidate) > 0:
                for memory in memories_to_consolidate:
                    # Request reasoning to evaluate memory importance
                    reasoning_task = {
                        "operation": "infer",
                        "data": {
                            "query": "Evaluate memory importance for long-term storage",
                            "memory_id": memory.id,
                            "context": "memory_consolidation"
                        }
                    }
                    evaluation = await self.reasoning.process(reasoning_task, context)
                    
                    # If reasoning determines memory is important, consolidate to long-term
                    if evaluation.get("importance_score", 0) > 0.5:
                        await self._consolidate_memory(memory.id, evaluation.get("summary"), context)
            
            # 3. Goal evaluation - check current goals and priorities
            self.cognitive_state.attention_focus = "goal_evaluation"
            
            # Request reasoning to evaluate goals based on system state
            goal_task = {
                "operation": "plan",
                "goal": "Maintain optimal system operation and knowledge coherence",
                "system_state": system_state,
                "current_goals": self.cognitive_state.active_goals
            }
            goal_evaluation = await self.reasoning.process(goal_task, context)
            
            # Update goals based on reasoning
            if "updated_goals" in goal_evaluation:
                self.cognitive_state.active_goals = goal_evaluation["updated_goals"]
                
                # Log goal changes
                await self.event_bus.publish("cognitive.goals.updated", {
                    "previous_goals": goal_evaluation.get("previous_goals", []),
                    "current_goals": self.cognitive_state.active_goals,
                    "rationale": goal_evaluation.get("rationale", "")
                })
            
            # 4. Knowledge integration - process new information
            self.cognitive_state.attention_focus = "knowledge_integration"
            
            # Find unprocessed information for knowledge integration
            knowledge_task = {
                "operation": "retrieve",
                "query": {
                    "status": "unprocessed",
                    "limit": 10
                }
            }
            knowledge_to_process = await self.knowledge.process(knowledge_task, context)
            
            # Process each knowledge item
            for item in knowledge_to_process:
                integration_task = {
                    "operation": "synthesize",
                    "params": {
                        "knowledge_id": item.get("id"),
                        "integrate_with_existing": True,
                        "update_connections": True
                    }
                }
                await self.knowledge.process(integration_task, context)
            
            # 5. Planning - determine next actions based on goals
            self.cognitive_state.attention_focus = "planning"
            
            # Generate actions for each active goal
            all_actions = []
            for goal in self.cognitive_state.active_goals:
                planning_task = {
                    "operation": "plan",
                    "goal": goal,
                    "constraints": {
                        "max_actions": 5,
                        "resources_available": True,
                        "priority_threshold": 0.3
                    }
                }
                actions = await self.reasoning.process(planning_task, context)
                if actions and isinstance(actions, list):
                    all_actions.extend(actions)
            
            # Sort actions by confidence/priority
            all_actions.sort(key=lambda x: x.confidence, reverse=True)
            
            # 6. Execute high-priority autonomous actions
            self.cognitive_state.attention_focus = "action_execution"
            await self._execute_actions(all_actions, context)
            
            # Update cognitive state
            self.cognitive_state.last_updated = datetime.now()
            self.cognitive_state.processing_state = "idle"
            
            # Calculate cycle metrics
            cycle_duration = (datetime.now() - cycle_start_time).total_seconds()
            
            # Publish cycle completion event
            await self.event_bus.publish("cognitive.cycle.completed", {
                "cycle_id": cycle_id,
                "timestamp": datetime.now().isoformat(),
                "duration_seconds": cycle_duration,
                "actions_taken": len(all_actions),
                "attention_sequence": [
                    "perception",
                    "memory_consolidation",
                    "goal_evaluation",
                    "knowledge_integration",
                    "planning",
                    "action_execution"
                ],
                "goals_updated": self.cognitive_state.active_goals != goal_evaluation.get("previous_goals", [])
            })
            
        except Exception as e:
            logger.error(f"Error in cognitive cycle execution: {str(e)}", exc_info=True)
            self.cognitive_state.processing_state = "error"
            
            # Publish error event
            await self.event_bus.publish("cognitive.cycle.error", {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "state": self.cognitive_state.__dict__
            }, priority=EventPriority.HIGH)
    
    async def _gather_system_state(self, context: CognitiveContext) -> Dict[str, Any]:
        """Collect current system state information"""
        # This would collect metrics, active sessions, recent events, etc.
        return {
            "timestamp": datetime.now().isoformat(),
            "active_sessions": 0,  # placeholder
            "recent_events": [],  # placeholder
            "system_load": 0.5,  # placeholder
        }
    
    async def _consolidate_memories(self, context: CognitiveContext):
        """Process short-term memories and consolidate important ones to long-term"""
        memory_task = {
            "operation": "consolidate",
            "query": {
                "memory_type": "short_term",
                "status": "active",
                "created_before": (datetime.now() - timedelta(hours=24)).isoformat()
            }
        }
        candidates = await self.memory.process(memory_task, context)
        for memory in candidates:
            # Use reasoning to evaluate importance
            reasoning_task = {
                "operation": "infer",
                "data": {
                    "query": "Evaluate memory importance for long-term storage",
                    "memory_id": memory.id,
                    "context": "memory_consolidation"
                }
            }
            evaluation = await self.reasoning.process(reasoning_task, context)
            if evaluation.get("importance_score", 0) > 0.5:
                await self._consolidate_memory(memory.id, evaluation.get("summary"), context)

    async def _evaluate_goals(self, system_state: Dict[str, Any], context: CognitiveContext):
        """Evaluate and update system goals based on current state"""
        goal_task = {
            "operation": "plan",
            "goal": "Maintain optimal system operation and knowledge coherence",
            "system_state": system_state,
            "current_goals": self.cognitive_state.active_goals
        }
        goal_evaluation = await self.reasoning.process(goal_task, context)
        if "updated_goals" in goal_evaluation:
            self.cognitive_state.active_goals = goal_evaluation["updated_goals"]
            await self.event_bus.publish("cognitive.goals.updated", {
                "previous_goals": goal_evaluation.get("previous_goals", []),
                "current_goals": self.cognitive_state.active_goals,
                "rationale": goal_evaluation.get("rationale", "")
            })

    async def _integrate_knowledge(self, context: CognitiveContext):
        """Process and integrate new knowledge into knowledge base"""
        knowledge_task = {
            "operation": "retrieve",
            "query": {
                "status": "unprocessed",
                "limit": 10
            }
        }
        knowledge_to_process = await self.knowledge.process(knowledge_task, context)
        for item in knowledge_to_process:
            integration_task = {
                "operation": "synthesize",
                "params": {
                    "knowledge_id": item.get("id"),
                    "integrate_with_existing": True,
                    "update_connections": True
                }
            }
            await self.knowledge.process(integration_task, context)

    async def _determine_actions(self, context: CognitiveContext) -> List[Dict[str, Any]]:
        """Determine what actions to take based on current goals and state"""
        all_actions = []
        for goal in self.cognitive_state.active_goals:
            planning_task = {
                "operation": "plan",
                "goal": goal,
                "constraints": {
                    "max_actions": 5,
                    "resources_available": True,
                    "priority_threshold": 0.3
                }
            }
            actions = await self.reasoning.process(planning_task, context)
            if actions and isinstance(actions, list):
                all_actions.extend(actions)
        all_actions.sort(key=lambda x: getattr(x, 'confidence', 0), reverse=True)
        return all_actions

    async def _cleanup_old_memories(self):
        """Cleanup old memories that are no longer relevant"""
        # Use the memory system's cleanup logic
        await self.memory._cleanup_old_memories()

    async def _update_knowledge_base(self, params: Dict[str, Any]):
        """Update the knowledge base with new connections or information"""
        update_task = {
            "operation": "update",
            "params": params
        }
        await self.knowledge.process(update_task, self.cognitive_state.current_context)

    async def _handle_user_interaction(self, event_data):
        """Handle user interaction events"""
        # Update cognitive state to reflect user interaction
        self.cognitive_state.attention_focus = "user_interaction"
        self.cognitive_state.last_updated = datetime.now()
    
    async def _handle_perception(self, event_data):
        """Handle system perception events"""
        # Store perception event in memory
        context = self._create_system_context()
        await self.memory.store({
            "content": event_data,
            "memory_type": "short_term",
            "metadata": {"type": "perception", "timestamp": datetime.now().isoformat()}
        }, context)

    async def _handle_knowledge_update(self, event_data):
        """Handle knowledge update events"""
        # Store knowledge update in memory and trigger integration
        context = self._create_system_context()
        await self.memory.store({
            "content": event_data,
            "memory_type": "short_term",
            "metadata": {"type": "knowledge_update", "timestamp": datetime.now().isoformat()}
        }, context)
        await self._integrate_knowledge(context)

    async def _handle_memory_consolidation(self, event_data):
        """Handle memory consolidation events"""
        # Log and update state
        logger.info(f"Memory consolidation event: {event_data}")
        self.cognitive_state.last_updated = datetime.now()
    
    async def _consolidate_memory(self, memory_id: str, summary: Optional[str], context: CognitiveContext):
        """
        Consolidate a single memory from short-term to long-term storage
        
        Args:
            memory_id: The ID of the memory to consolidate
            summary: Optional summary or abstraction of the memory
            context: The cognitive context
        """
        try:
            # Retrieve the original memory
            retrieve_task = {
                "operation": "retrieve",
                "query": {
                    "id": memory_id
                }
            }
            original_memories = await self.memory.process(retrieve_task, context)
            
            if not original_memories or len(original_memories) == 0:
                logger.warning(f"Cannot consolidate memory {memory_id}: not found")
                return
                
            original_memory = original_memories[0]
            
            # Create consolidated version
            consolidated = {
                "content": original_memory.content,
                "memory_type": "long_term",
                "metadata": {
                    **original_memory.metadata,
                    "consolidated_at": datetime.now().isoformat(),
                    "original_id": memory_id,
                    "summary": summary
                }
            }
            
            # Store in long-term memory
            new_id = await self.memory.store(consolidated, context)
            
            # Create relationship between original and consolidated memory
            graph_query = f"""
            MATCH (original:Memory {{id: '{memory_id}'}}),
                  (consolidated:Memory {{id: '{new_id}'}})
            CREATE (original)-[:CONSOLIDATED_TO]->(consolidated)
            """
            
            # This assumes the memory system can run graph queries or has a way to create relationships
            # For now, just log the operation
            logger.info(f"Memory {memory_id} consolidated to long-term memory as {new_id}")
            
            # Publish event about memory consolidation
            await self.event_bus.publish(EventTaxonomy.MEMORY_CONSOLIDATED, {
                "original_id": memory_id,
                "consolidated_id": new_id,
                "has_summary": summary is not None,
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error consolidating memory {memory_id}: {str(e)}", exc_info=True)
            
            # Publish error event
            await self.event_bus.publish(EventTaxonomy.SYSTEM_ERROR, {
                "operation": "memory_consolidation",
                "memory_id": memory_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
