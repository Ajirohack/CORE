"""
MirrorCore Orchestrator for Human Simulation

This module provides the main orchestration functionality for the MirrorCore
human simulation system. It manages simulation sessions, stages, and coordinates
with external platforms.
"""
from typing import Dict, List, Any, Optional
import os
import json
import logging
from datetime import datetime
import uuid

from .stage_controller import StageController
from .session_manager import SessionManager

logger = logging.getLogger(__name__)

class Orchestrator:
    """
    MirrorCore Orchestrator class.
    
    Controls the overall simulation process, managing sessions, stages,
    and coordinating interactions across platforms.
    """
    
    def __init__(self, stages_config_path: str = None, scoring_schema_path: str = None, models: Dict[str, str] = None):
        """
        Initialize the MirrorCore Orchestrator.
        
        Args:
            stages_config_path: Path to the stage definitions JSON file
            scoring_schema_path: Path to the scoring schema JSON file
            models: Dictionary mapping model types to model names
        """
        self.stages_config_path = stages_config_path
        self.scoring_schema_path = scoring_schema_path
        self.models = models or {
            "conversation": "gpt-4-turbo",
            "evaluation": "gpt-4",
            "planning": "gpt-4",
        }
        
        # Load stage definitions and scoring schema
        self.stage_definitions = self._load_json_file(stages_config_path)
        self.scoring_schema = self._load_json_file(scoring_schema_path)
        
        # Initialize controllers
        self.stage_controller = StageController(
            stage_definitions=self.stage_definitions,
            scoring_schema=self.scoring_schema,
            evaluation_model=self.models.get("evaluation")
        )
        
        self.session_manager = SessionManager()
        
        # Active sessions dictionary: session_id -> session_data
        self.active_sessions = {}
        
        logger.info("MirrorCore Orchestrator initialized")
    
    def _load_json_file(self, file_path: str) -> Dict:
        """Load a JSON file from disk"""
        try:
            if file_path and os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    return json.load(f)
            else:
                logger.warning(f"File not found: {file_path}, using default empty dict")
                return {}
        except Exception as e:
            logger.error(f"Error loading JSON file {file_path}: {str(e)}")
            return {}
    
    def create_session(self, persona_id: str, scenario_type: str, target_platforms: List[str] = None) -> Dict[str, Any]:
        """
        Create a new simulation session.
        
        Args:
            persona_id: ID of the persona to use
            scenario_type: Type of scenario (dating, investment, etc.)
            target_platforms: List of platforms to engage with
            
        Returns:
            Dict containing session details including session_id
        """
        session_id = str(uuid.uuid4())
        
        session_data = {
            "session_id": session_id,
            "persona_id": persona_id,
            "scenario_type": scenario_type,
            "target_platforms": target_platforms or [],
            "current_stage": "initial",
            "start_time": datetime.now().isoformat(),
            "metrics": {
                "messages_sent": 0,
                "messages_received": 0,
                "platforms_engaged": [],
                "stage_completion": {},
            },
            "status": "active",
            "history": []
        }
        
        # Store in active sessions
        self.active_sessions[session_id] = session_data
        
        # Persist in session manager
        self.session_manager.save_session(session_data)
        
        logger.info(f"Created new session: {session_id} for persona {persona_id}")
        return session_data
    
    def process_message(self, session_id: str, message: str, platform: str = None) -> Dict[str, Any]:
        """
        Process an incoming message and generate a response based on the current stage.
        
        Args:
            session_id: ID of the session
            message: The incoming message text
            platform: The platform this message came from
            
        Returns:
            Dict containing the response and updated session information
        """
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.active_sessions[session_id]
        current_stage = session["current_stage"]
        persona_id = session["persona_id"]
        
        # Evaluate the message against the current stage
        evaluation_result = self.stage_controller.evaluate_message(
            message=message,
            current_stage=current_stage,
            persona_id=persona_id,
            session_history=session["history"]
        )
        
        # Update session with the evaluation
        session["metrics"]["messages_received"] += 1
        if platform and platform not in session["metrics"]["platforms_engaged"]:
            session["metrics"]["platforms_engaged"].append(platform)
        
        # Store the message in history
        session["history"].append({
            "role": "user",
            "content": message,
            "timestamp": datetime.now().isoformat(),
            "platform": platform,
            "evaluation": evaluation_result
        })
        
        # Check if we should transition to the next stage
        if evaluation_result["should_transition"]:
            next_stage = evaluation_result["next_stage"]
            
            # Update stage completion metrics
            session["metrics"]["stage_completion"][current_stage] = {
                "completed": True,
                "score": evaluation_result["score"],
                "completion_time": datetime.now().isoformat()
            }
            
            # Update current stage
            session["current_stage"] = next_stage
            logger.info(f"Session {session_id} advanced to stage: {next_stage}")
        
        # Generate response based on evaluation and current/next stage
        response = self.stage_controller.generate_response(
            evaluation=evaluation_result,
            current_stage=session["current_stage"],
            persona_id=persona_id,
            session_history=session["history"],
            model=self.models.get("conversation")
        )
        
        # Update session with the response
        session["metrics"]["messages_sent"] += 1
        
        # Store the response in history
        session["history"].append({
            "role": "assistant",
            "content": response,
            "timestamp": datetime.now().isoformat(),
            "platform": platform
        })
        
        # Update session in storage
        self.session_manager.update_session(session)
        
        return {
            "response": response,
            "current_stage": session["current_stage"],
            "evaluation": evaluation_result,
            "session_updated": True
        }
    
    def get_session(self, session_id: str) -> Dict[str, Any]:
        """Get session details by ID"""
        if session_id in self.active_sessions:
            return self.active_sessions[session_id]
        else:
            # Try to load from session manager
            session = self.session_manager.get_session(session_id)
            if session:
                # Cache in active sessions
                self.active_sessions[session_id] = session
                return session
            else:
                raise ValueError(f"Session {session_id} not found")
    
    def close_session(self, session_id: str) -> bool:
        """Close a session and mark it as completed"""
        if session_id not in self.active_sessions:
            raise ValueError(f"Session {session_id} not found")
        
        session = self.active_sessions[session_id]
        session["status"] = "completed"
        session["end_time"] = datetime.now().isoformat()
        
        # Calculate final metrics
        final_metrics = self._calculate_final_metrics(session)
        session["final_metrics"] = final_metrics
        
        # Update session in storage
        self.session_manager.update_session(session)
        
        # Remove from active sessions
        del self.active_sessions[session_id]
        
        logger.info(f"Session {session_id} closed with status 'completed'")
        return True
    
    def _calculate_final_metrics(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate final metrics for a completed session"""
        total_score = 0
        completed_stages = 0
        
        for stage, completion_data in session["metrics"]["stage_completion"].items():
            if completion_data.get("completed", False):
                total_score += completion_data.get("score", 0)
                completed_stages += 1
        
        average_score = total_score / completed_stages if completed_stages > 0 else 0
        
        # Calculate session duration
        start_time = datetime.fromisoformat(session["start_time"])
        end_time = datetime.fromisoformat(session["end_time"]) if "end_time" in session else datetime.now()
        duration_seconds = (end_time - start_time).total_seconds()
        
        return {
            "average_stage_score": average_score,
            "completed_stages": completed_stages,
            "total_stages": len(self.stage_definitions),
            "completion_percentage": (completed_stages / len(self.stage_definitions)) * 100 if self.stage_definitions else 0,
            "messages_exchanged": session["metrics"]["messages_sent"] + session["metrics"]["messages_received"],
            "duration_seconds": duration_seconds,
            "platforms_engaged": len(session["metrics"]["platforms_engaged"]),
        }
    
    def get_active_session_count(self) -> int:
        """Get the count of active sessions"""
        return len(self.active_sessions)
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """Get memory usage statistics"""
        import psutil
        import sys
        
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        
        return {
            "rss_mb": memory_info.rss / (1024 * 1024),
            "vms_mb": memory_info.vms / (1024 * 1024),
            "active_sessions": len(self.active_sessions),
            "history_entries": sum(len(session["history"]) for session in self.active_sessions.values()),
        }
    
    def shutdown(self):
        """Shut down the orchestrator and clean up resources"""
        # Save all active sessions
        for session_id, session in self.active_sessions.items():
            if session["status"] == "active":
                session["status"] = "interrupted"
                session["end_time"] = datetime.now().isoformat()
                self.session_manager.update_session(session)
        
        logger.info(f"Orchestrator shutdown: {len(self.active_sessions)} active sessions saved")
        self.active_sessions = {}
