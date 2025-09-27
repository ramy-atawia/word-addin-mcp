"""
Simplified Session Management Service for Word Add-in MCP Project.

This service handles basic user session creation, validation, and cleanup
without complex background tasks or optimization features.
"""

import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger()


class SessionService:
    """Simplified service for managing user sessions."""
    
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.user_sessions: Dict[str, List[str]] = {}  # user_id -> list of session_ids
    
    def create_session(self, user_id: Optional[str] = None, 
                      metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a new user session."""
        try:
            session_id = str(uuid.uuid4())
            now = datetime.utcnow()
            
            session_data = {
                "session_id": session_id,
                "user_id": user_id,
                "created_at": now,
                "last_activity": now,
                "metadata": metadata or {},
                "is_active": True,
                "conversation_count": 0,
                "tool_usage": {},
                "memory_size": 0
            }
            
            # Store session
            self.sessions[session_id] = session_data
            
            # Track user sessions
            if user_id:
                if user_id not in self.user_sessions:
                    self.user_sessions[user_id] = []
                self.user_sessions[user_id].append(session_id)
            
            logger.info(f"Created session {session_id} for user {user_id}")
            return session_data
            
        except Exception as e:
            logger.error(f"Failed to create session: {str(e)}")
            raise
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data by ID."""
        try:
            session = self.sessions.get(session_id)
            if session and session["is_active"]:
                # Update last activity
                session["last_activity"] = datetime.utcnow()
                return session
            return None
            
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {str(e)}")
            return None
    
    def update_session_activity(self, session_id: str, activity_type: str = "general", metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Update session activity and metadata."""
        try:
            session = self.sessions.get(session_id)
            if not session:
                return False
            
            session["last_activity"] = datetime.utcnow()
            
            if activity_type == "conversation":
                session["conversation_count"] += 1
            elif activity_type == "tool":
                # Track tool usage
                pass
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update session activity: {str(e)}")
            return False
    
    def deactivate_session(self, session_id: str) -> bool:
        """Deactivate a session."""
        try:
            session = self.sessions.get(session_id)
            if session:
                session["is_active"] = False
                session["last_activity"] = datetime.utcnow()
                logger.info(f"Deactivated session {session_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to deactivate session: {str(e)}")
            return False
    
    def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all active sessions for a user."""
        try:
            if user_id not in self.user_sessions:
                return []
            
            user_session_ids = self.user_sessions[user_id]
            active_sessions = []
            
            for session_id in user_session_ids:
                session = self.sessions.get(session_id)
                if session and session["is_active"]:
                    active_sessions.append(session)
            
            return active_sessions
            
        except Exception as e:
            logger.error(f"Failed to get user sessions: {str(e)}")
            return []
    
    def cleanup_expired_sessions(self, max_age_hours: int = 24) -> int:
        """Clean up expired sessions."""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
            expired_sessions = []
            
            for session_id, session in self.sessions.items():
                if session["last_activity"] < cutoff_time:
                    expired_sessions.append(session_id)
            
            # Deactivate expired sessions
            for session_id in expired_sessions:
                self.deactivate_session(session_id)
            
            if expired_sessions:
                logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
            
            return len(expired_sessions)
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired sessions: {str(e)}")
            return 0
    
    def get_session_statistics(self, session_id: str) -> Dict[str, Any]:
        """Get statistics for a specific session."""
        try:
            session = self.get_session(session_id)
            if not session:
                return {}
            
            # Calculate session duration
            duration = datetime.utcnow() - session["created_at"]
            
            return {
                "session_id": session_id,
                "duration_seconds": int(duration.total_seconds()),
                "conversation_count": session["conversation_count"],
                "tool_usage": session["tool_usage"],
                "memory_size": session["memory_size"],
                "created_at": session["created_at"].isoformat(),
                "last_activity": session["last_activity"].isoformat(),
                "is_active": session["is_active"]
            }
            
        except Exception as e:
            logger.error(f"Failed to get session statistics: {str(e)}")
            return {}
    
    def get_global_statistics(self) -> Dict[str, Any]:
        """Get global session statistics."""
        try:
            total_sessions = len(self.sessions)
            active_sessions = sum(1 for s in self.sessions.values() if s["is_active"])
            total_users = len(self.user_sessions)
            
            # Calculate total tool usage
            total_tool_usage = {}
            for session in self.sessions.values():
                for tool, count in session["tool_usage"].items():
                    total_tool_usage[tool] = total_tool_usage.get(tool, 0) + count
            
            return {
                "total_sessions": total_sessions,
                "active_sessions": active_sessions,
                "total_users": total_users,
                "total_tool_usage": total_tool_usage,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get global statistics: {str(e)}")
            return {}
    
    def validate_session(self, session_id: str) -> bool:
        """Validate if a session is active and valid."""
        try:
            session = self.sessions.get(session_id)
            if not session:
                return False
            
            if not session["is_active"]:
                return False
            
            # Check if session is too old (more than 7 days)
            max_age = datetime.utcnow() - timedelta(days=7)
            if session["created_at"] < max_age:
                self.deactivate_session(session_id)
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to validate session: {str(e)}")
            return False
    
    def update_session(self, session_id: str, metadata: Optional[Dict[str, Any]] = None, is_active: Optional[bool] = None) -> Optional[Dict[str, Any]]:
        """Update session metadata and status."""
        try:
            session = self.sessions.get(session_id)
            if not session:
                return None
            
            # Update metadata if provided
            if metadata:
                session["metadata"].update(metadata)
            
            # Update active status if provided
            if is_active is not None:
                session["is_active"] = is_active
            
            # Update last activity
            session["last_activity"] = datetime.utcnow()
            
            logger.info(f"Updated session {session_id}")
            return session
            
        except Exception as e:
            logger.error(f"Failed to update session: {str(e)}")
            return None
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session completely."""
        try:
            if session_id in self.sessions:
                session = self.sessions[session_id]
                user_id = session.get("user_id")
                
                # Remove from user sessions
                if user_id and user_id in self.user_sessions:
                    if session_id in self.user_sessions[user_id]:
                        self.user_sessions[user_id].remove(session_id)
                    
                    # Clean up empty user sessions
                    if not self.user_sessions[user_id]:
                        del self.user_sessions[user_id]
                
                # Remove session
                del self.sessions[session_id]
                
                logger.info(f"Deleted session {session_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete session: {str(e)}")
            return False


# Global instance for easy access
session_service = SessionService()

