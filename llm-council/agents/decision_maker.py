"""
Decision Maker Agent for the AI Council
Acts as the central coordinator for all specialist agents
"""

import logging
from typing import Dict, List, Any, Optional
import autogen
from autogen.agentchat.agent import Agent

# Setup logging
logger = logging.getLogger(__name__)

class DecisionMakerAgent(autogen.ConversableAgent):
    """
    Decision Maker Agent that coordinates the AI Council's specialist agents.
    This agent is responsible for task delegation, synthesis of specialist input,
    and final decision making.
    """
    
    def __init__(self, name: str, system_message: str, llm_config: Dict[str, Any], max_iterations: int = 3):
        """
        Initialize the Decision Maker Agent
        
        Args:
            name: Name of the agent
            system_message: The system message that defines the agent's role
            llm_config: Configuration for the language model
            max_iterations: Maximum number of iterations allowed for a single request
        """
        super().__init__(
            name=name,
            system_message=system_message,
            llm_config=llm_config
        )
        self.task_history = []
        self.max_iterations = max_iterations
        self.iteration_thresholds = {
            "confidence": 0.85,   # Minimum confidence score to accept response
            "completeness": 0.80, # Minimum completeness score to accept response
            "consensus": 0.75     # Minimum agreement level among specialists
        }
        logger.info(f"Decision Maker Agent '{name}' initialized")
        
    def process_with_specialists(self, user_request: str, specialists: Dict[str, Agent]) -> str:
        """
        Process a user request by coordinating with specialist agents
        
        Args:
            user_request: The user's request/query
            specialists: Dictionary of specialist agents available for consultation
            
        Returns:
            Final response synthesized from specialist inputs
        """
        logger.info(f"Decision Maker processing request: {user_request[:50]}...")
        
        iteration = 1
        previous_response = None
        final_response = None
        iteration_history = []
        
        while iteration <= self.max_iterations:
            logger.info(f"Starting iteration {iteration} of {self.max_iterations}")
            
            # Step 1: Analyze the request and determine which specialists to consult
            specialist_assignments = self._analyze_and_assign(user_request, specialists, 
                                                             previous_response=previous_response, 
                                                             current_iteration=iteration)
            
            # Step 2: Consult the relevant specialists in parallel or sequence
            specialist_responses = self._gather_specialist_input(user_request, specialist_assignments, 
                                                               previous_response=previous_response,
                                                               current_iteration=iteration)
            
            # Step 3: Synthesize the inputs into a coherent response
            response_data = self._synthesize_response(user_request, specialist_responses, 
                                                   previous_response=previous_response,
                                                   current_iteration=iteration)
            
            current_response = response_data["response"]
            evaluation = response_data["evaluation"]
            
            # Record this iteration
            iteration_history.append({
                "iteration": iteration,
                "specialists_consulted": list(specialist_assignments.keys()),
                "response": current_response,
                "evaluation": evaluation
            })
            
            # Check if we should continue iterating
            should_continue = self._should_continue_iteration(evaluation, iteration)
            
            if not should_continue:
                final_response = current_response
                logger.info(f"Iteration complete: Accepting response after {iteration} iterations")
                break
                
            logger.info(f"Continuing to iterate - current evaluation: {evaluation}")
            previous_response = current_response
            iteration += 1
        
        # If we've reached max iterations without breaking, use the last response
        if final_response is None:
            final_response = previous_response
            logger.info(f"Reached maximum iterations ({self.max_iterations}). Using final iteration response.")
        
        # Record this task in history
        self.task_history.append({
            "request": user_request,
            "iterations": iteration,
            "iteration_history": iteration_history,
            "specialists_consulted": list(set([specialist for it in iteration_history for specialist in it["specialists_consulted"]])),
            "response_length": len(final_response)
        })
        
        return final_response
    
    def _should_continue_iteration(self, evaluation: Dict[str, float], current_iteration: int) -> bool:
        """
        Determine if we should continue iterating based on evaluation metrics
        
        Args:
            evaluation: Dictionary containing evaluation metrics
            current_iteration: The current iteration number
            
        Returns:
            Boolean indicating whether to continue iterating
        """
        # If we've reached max iterations, don't continue
        if current_iteration >= self.max_iterations:
            return False
            
        # Check if all thresholds are met
        confidence_met = evaluation.get("confidence", 0) >= self.iteration_thresholds["confidence"]
        completeness_met = evaluation.get("completeness", 0) >= self.iteration_thresholds["completeness"]
        consensus_met = evaluation.get("consensus", 0) >= self.iteration_thresholds["consensus"]
        
        # If all thresholds are met, no need to continue
        if confidence_met and completeness_met and consensus_met:
            return False
            
        # Continue iterating
        return True
    
    def _analyze_and_assign(self, request: str, specialists: Dict[str, Agent], 
                           previous_response: Optional[str] = None, 
                           current_iteration: int = 1) -> Dict[str, Dict]:
        """
        Analyze the request and assign appropriate specialists
        
        Args:
            request: The user's request
            specialists: Available specialist agents
            previous_response: Response from previous iteration (if any)
            current_iteration: Current iteration number
            
        Returns:
            Dictionary mapping specialist types to their tasks
        """
        # This would typically involve asking the LLM to analyze and determine
        # which specialists are needed for this particular request
        
        # For now, implement a simple rule-based assignment
        assignments = {}
        
        # Research agent for factual queries
        if any(keyword in request.lower() for keyword in ["research", "find", "information", "data"]):
            if "research" in specialists:
                assignments["research"] = {
                    "priority": "high",
                    "specific_task": "Find relevant information and data for this query"
                }
        
        # Creative agent for generation tasks
        if any(keyword in request.lower() for keyword in ["create", "generate", "design", "creative"]):
            if "creative" in specialists:
                assignments["creative"] = {
                    "priority": "medium",
                    "specific_task": "Generate creative content or solutions"
                }
        
        # Logical agent for reasoning and problem-solving
        if any(keyword in request.lower() for keyword in ["analyze", "evaluate", "solve", "logic"]):
            if "logical" in specialists:
                assignments["logical"] = {
                    "priority": "high",
                    "specific_task": "Analyze the problem and provide logical reasoning"
                }
        
        # Ethical agent for ethical considerations
        if any(keyword in request.lower() for keyword in ["ethical", "moral", "right", "wrong"]):
            if "ethical" in specialists:
                assignments["ethical"] = {
                    "priority": "high",
                    "specific_task": "Evaluate ethical implications and provide guidance"
                }
        
        # Implementation agent for code/implementation tasks
        if any(keyword in request.lower() for keyword in ["implement", "code", "build", "create"]):
            if "implementation" in specialists:
                assignments["implementation"] = {
                    "priority": "medium",
                    "specific_task": "Provide implementation details or code"
                }
        
        # If no specific specialists were assigned, involve all available ones
        if not assignments and specialists:
            for specialist_type, specialist in specialists.items():
                if specialist_type != "decision_maker":
                    assignments[specialist_type] = {
                        "priority": "medium",
                        "specific_task": "Provide input from your perspective"
                    }
        
        # For iterations beyond the first, include additional context
        if current_iteration > 1 and previous_response:
            for specialist_type in assignments:
                assignments[specialist_type]["previous_response"] = previous_response
                assignments[specialist_type]["iteration"] = current_iteration
                assignments[specialist_type]["specific_task"] += f" (Iteration {current_iteration}: Refine previous response)"
        
        logger.info(f"Assigned specialists for iteration {current_iteration}: {list(assignments.keys())}")
        return assignments
    
    def _gather_specialist_input(self, request: str, assignments: Dict[str, Dict],
                               previous_response: Optional[str] = None,
                               current_iteration: int = 1) -> Dict[str, str]:
        """
        Gather input from the assigned specialists
        
        Args:
            request: The original user request
            assignments: Dictionary of specialist assignments
            previous_response: Response from previous iteration (if any)
            current_iteration: Current iteration number
            
        Returns:
            Dictionary of specialist responses
        """
        # In a real implementation, this would interact with the actual specialist agents
        # For now, we'll simulate responses
        
        # This would be replaced by actual calls to specialist agents
        responses = {}
        for specialist_type, assignment in assignments.items():
            # Prepare the prompt based on iteration
            if current_iteration == 1:
                prompt = f"Task for {specialist_type}: {assignment['specific_task']}. Request: {request}"
            else:
                prompt = (f"Task for {specialist_type}: {assignment['specific_task']}. "
                         f"Request: {request}\n\nPrevious response: {previous_response}\n\n"
                         f"Please review and improve the previous response.")
            
            # This is a placeholder for the actual agent interaction
            responses[specialist_type] = f"Input from {specialist_type} specialist (iteration {current_iteration})"
            
            logger.info(f"Gathered input from {specialist_type} specialist for iteration {current_iteration}")
            
        return responses
    
    def _synthesize_response(self, request: str, specialist_responses: Dict[str, str],
                           previous_response: Optional[str] = None,
                           current_iteration: int = 1) -> Dict[str, Any]:
        """
        Synthesize specialist responses into a coherent final response with evaluation metrics
        
        Args:
            request: The original user request
            specialist_responses: Inputs from specialist agents
            previous_response: Response from previous iteration (if any)
            current_iteration: Current iteration number
            
        Returns:
            Dictionary containing the synthesized response and evaluation metrics
        """
        # Prepare the synthesis prompt
        synthesis_input = f"Original request: {request}\n\n"
        
        # For iterations beyond the first, include the previous response
        if current_iteration > 1 and previous_response:
            synthesis_input += f"Previous response (iteration {current_iteration-1}): {previous_response}\n\n"
            synthesis_input += f"Your task is to improve upon the previous response based on new specialist inputs.\n\n"
        
        # Add all specialist inputs
        for specialist_type, response in specialist_responses.items():
            synthesis_input += f"{specialist_type.capitalize()} specialist input: {response}\n\n"
        
        synthesis_input += "Synthesize these inputs into a coherent, comprehensive response."
        
        # In a real implementation, this would use the LLM to create a synthesis
        logger.info(f"Synthesizing response for iteration {current_iteration} from specialist inputs")
        
        # This is where we would call the LLM to generate the final synthesis
        synthesized_response = f"Synthesized response for iteration {current_iteration} based on input from {len(specialist_responses)} specialists."
        
        # In a real implementation, this would use the LLM to evaluate the response
        # For now, we'll simulate evaluation metrics
        if current_iteration == 1:
            evaluation = {
                "confidence": 0.7,
                "completeness": 0.65,
                "consensus": 0.6
            }
        else:
            # Simulate improvement with each iteration
            base_improvement = min(0.1 * current_iteration, 0.3)
            evaluation = {
                "confidence": min(0.7 + base_improvement, 0.95),
                "completeness": min(0.65 + base_improvement, 0.95),
                "consensus": min(0.6 + base_improvement, 0.95)
            }
        
        return {
            "response": synthesized_response,
            "evaluation": evaluation
        }