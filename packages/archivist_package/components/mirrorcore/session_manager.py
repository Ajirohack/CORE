"""
MirrorCore Session Manager

This module provides session management functionality for the MirrorCore
human simulation system.
"""
from typing import Dict, List, Any, Optional
import os
import json
import sqlite3
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class SessionManager:
    """
    Session Manager for MirrorCore.
    
    Handles session persistence, retrieval, and management.
    """
    
    def __init__(self, db_path: str = None):
        """
        Initialize the Session Manager.
        
        Args:
            db_path: Path to the SQLite database for session storage
        """
        self.db_path = db_path or os.path.join(os.getcwd(), "data", "mirrorcore", "sessions.db")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        logger.info(f"SessionManager initialized with database at {self.db_path}")
    
    def _init_database(self):
        """Initialize the SQLite database and create tables if they don't exist"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create sessions table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                persona_id TEXT NOT NULL,
                scenario_type TEXT NOT NULL,
                current_stage TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT,
                status TEXT NOT NULL,
                metrics TEXT NOT NULL,
                history TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error initializing session database: {str(e)}")
            raise
    
    def save_session(self, session: Dict[str, Any]) -> bool:
        """
        Save a new session to the database.
        
        Args:
            session: Session data dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Convert complex objects to JSON strings
            metrics_json = json.dumps(session.get("metrics", {}))
            history_json = json.dumps(session.get("history", []))
            
            cursor.execute('''
            INSERT INTO sessions (
                session_id, persona_id, scenario_type, current_stage,
                start_time, status, metrics, history, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session["session_id"],
                session["persona_id"],
                session["scenario_type"],
                session["current_stage"],
                session["start_time"],
                session["status"],
                metrics_json,
                history_json,
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving session {session.get('session_id')}: {str(e)}")
            return False
    
    def update_session(self, session: Dict[str, Any]) -> bool:
        """
        Update an existing session in the database.
        
        Args:
            session: Session data dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if the session exists
            cursor.execute('''
            SELECT COUNT(*) FROM sessions WHERE session_id = ?
            ''', (session["session_id"],))
            
            if cursor.fetchone()[0] == 0:
                # Session doesn't exist, create it
                conn.close()
                return self.save_session(session)
            
            # Convert complex objects to JSON strings
            metrics_json = json.dumps(session.get("metrics", {}))
            history_json = json.dumps(session.get("history", []))
            
            # End time is optional
            end_time = session.get("end_time")
            
            cursor.execute('''
            UPDATE sessions SET
                persona_id = ?,
                scenario_type = ?,
                current_stage = ?,
                end_time = ?,
                status = ?,
                metrics = ?,
                history = ?,
                updated_at = ?
            WHERE session_id = ?
            ''', (
                session["persona_id"],
                session["scenario_type"],
                session["current_stage"],
                end_time,
                session["status"],
                metrics_json,
                history_json,
                datetime.now().isoformat(),
                session["session_id"]
            ))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating session {session.get('session_id')}: {str(e)}")
            return False
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a session by ID.
        
        Args:
            session_id: The session ID to retrieve
            
        Returns:
            Session dictionary or None if not found
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT * FROM sessions WHERE session_id = ?
            ''', (session_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                return None
            
            # Convert row to dict and parse JSON fields
            session = dict(row)
            session["metrics"] = json.loads(session["metrics"])
            session["history"] = json.loads(session["history"])
            
            return session
            
        except Exception as e:
            logger.error(f"Error retrieving session {session_id}: {str(e)}")
            return None
    
    def get_sessions_by_persona(self, persona_id: str) -> List[Dict[str, Any]]:
        """
        Get all sessions for a specific persona.
        
        Args:
            persona_id: The persona ID to filter by
            
        Returns:
            List of session dictionaries
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT * FROM sessions WHERE persona_id = ? ORDER BY start_time DESC
            ''', (persona_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            sessions = []
            for row in rows:
                session = dict(row)
                session["metrics"] = json.loads(session["metrics"])
                session["history"] = json.loads(session["history"])
                sessions.append(session)
            
            return sessions
            
        except Exception as e:
            logger.error(f"Error retrieving sessions for persona {persona_id}: {str(e)}")
            return []
    
    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """
        Get all active sessions.
        
        Returns:
            List of active session dictionaries
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT * FROM sessions WHERE status = 'active' ORDER BY start_time DESC
            ''')
            
            rows = cursor.fetchall()
            conn.close()
            
            sessions = []
            for row in rows:
                session = dict(row)
                session["metrics"] = json.loads(session["metrics"])
                session["history"] = json.loads(session["history"])
                sessions.append(session)
            
            return sessions
            
        except Exception as e:
            logger.error(f"Error retrieving active sessions: {str(e)}")
            return []
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session from the database.
        
        Args:
            session_id: The session ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            DELETE FROM sessions WHERE session_id = ?
            ''', (session_id,))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {str(e)}")
            return False
