"""
Session management API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
import structlog
from typing import Dict, Any, List, Optional
import time

from app.core.config import settings
from app.services.session_service import session_service

router = APIRouter()
logger = structlog.get_logger()


@router.post("/create")
async def create_session(user_id: Optional[str] = None, 
                        metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Create a new chat session."""
    try:
        session_data = await session_service.create_session(user_id, metadata)
        
        logger.info("Session created", 
                   session_id=session_data.session_id, 
                   user_id=user_id)
        
        return {
            "session_id": session_data.session_id,
            "user_id": session_data.user_id,
            "created_at": session_data.created_at.isoformat(),
            "last_activity": session_data.last_activity.isoformat(),
            "is_active": session_data.is_active,
            "metadata": session_data.metadata
        }
        
    except Exception as e:
        logger.error("Failed to create session", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create session: {str(e)}"
        )


@router.get("/{session_id}")
async def get_session(session_id: str) -> Dict[str, Any]:
    """Get session information."""
    try:
        session_data = await session_service.get_session(session_id)
        
        if not session_data:
            raise HTTPException(
                status_code=404,
                detail="Session not found or inactive"
            )
        
        return {
            "session_id": session_data.session_id,
            "user_id": session_data.user_id,
            "created_at": session_data.created_at.isoformat(),
            "last_activity": session_data.last_activity.isoformat(),
            "is_active": session_data.is_active,
            "conversation_count": session_data.conversation_count,
            "tool_usage": session_data.tool_usage,
            "memory_size": session_data.memory_size,
            "metadata": session_data.metadata
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get session", session_id=session_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get session: {str(e)}"
        )


@router.delete("/{session_id}")
async def delete_session(session_id: str) -> Dict[str, Any]:
    """Delete a session."""
    try:
        success = await session_service.deactivate_session(session_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Session not found"
            )
        
        logger.info("Session deleted", session_id=session_id)
        
        return {
            "session_id": session_id,
            "status": "deleted",
            "deleted_at": time.time()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete session", session_id=session_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete session: {str(e)}"
        )


@router.put("/{session_id}")
async def update_session(session_id: str, 
                        metadata: Optional[Dict[str, Any]] = None,
                        is_active: Optional[bool] = None) -> Dict[str, Any]:
    """Update session information."""
    try:
        # Validate session exists
        session_data = await session_service.get_session(session_id)
        if not session_data:
            raise HTTPException(
                status_code=404,
                detail="Session not found or inactive"
            )
        
        # Update session
        updated_session = await session_service.update_session(session_id, metadata, is_active)
        
        if not updated_session:
            raise HTTPException(
                status_code=500,
                detail="Failed to update session"
            )
        
        logger.info("Session updated", session_id=session_id)
        
        return {
            "session_id": session_id,
            "status": "updated",
            "updated_at": time.time(),
            "metadata": updated_session.metadata,
            "is_active": updated_session.is_active
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update session", session_id=session_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update session: {str(e)}"
        )


@router.get("/{session_id}/messages")
async def get_session_messages(session_id: str, limit: int = 50) -> Dict[str, Any]:
    """Get messages for a session."""
    try:
        # Validate session exists
        session_data = await session_service.get_session(session_id)
        if not session_data:
            raise HTTPException(
                status_code=404,
                detail="Session not found or inactive"
            )
        
        # TODO: Implement message retrieval from conversation memory
        # For now, return placeholder messages
        messages = [
            {
                "id": "1",
                "session_id": session_id,
                "content": "Hello, how can I help you?",
                "role": "assistant",
                "timestamp": time.time() - 300
            },
            {
                "id": "2",
                "session_id": session_id,
                "content": "I need help with my document",
                "role": "user",
                "timestamp": time.time() - 240
            }
        ]
        
        return {
            "session_id": session_id,
            "messages": messages[:limit],
            "total_count": len(messages),
            "limit": limit
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get session messages", 
                    session_id=session_id, 
                    error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get session messages: {str(e)}"
        )


@router.post("/{session_id}/activity")
async def update_session_activity(session_id: str, 
                                activity_type: str = "conversation",
                                metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Update session activity timestamp."""
    try:
        await session_service.update_session_activity(session_id, activity_type, metadata)
        
        logger.info("Session activity updated", 
                   session_id=session_id, 
                   activity_type=activity_type)
        
        return {
            "session_id": session_id,
            "activity_type": activity_type,
            "status": "updated",
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error("Failed to update session activity", 
                    session_id=session_id, 
                    error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update session activity: {str(e)}"
        )


@router.get("/user/{user_id}/sessions")
async def get_user_sessions(user_id: str, limit: int = 20) -> Dict[str, Any]:
    """Get all sessions for a user."""
    try:
        sessions = await session_service.get_user_sessions(user_id)
        
        # Convert to response format
        session_list = []
        for session in sessions[:limit]:
            session_list.append({
                "session_id": session.session_id,
                "user_id": session.user_id,
                "created_at": session.created_at.isoformat(),
                "last_activity": session.last_activity.isoformat(),
                "is_active": session.is_active,
                "conversation_count": session.conversation_count,
                "tool_usage": session.tool_usage,
                "memory_size": session.memory_size
            })
        
        return {
            "user_id": user_id,
            "sessions": session_list,
            "total_count": len(sessions),
            "limit": limit
        }
        
    except Exception as e:
        logger.error("Failed to get user sessions", user_id=user_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get user sessions: {str(e)}"
        )


@router.get("/{session_id}/statistics")
async def get_session_statistics(session_id: str) -> Dict[str, Any]:
    """Get statistics for a specific session."""
    try:
        stats = await session_service.get_session_statistics(session_id)
        
        if not stats:
            raise HTTPException(
                status_code=404,
                detail="Session not found"
            )
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get session statistics", 
                    session_id=session_id, 
                    error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get session statistics: {str(e)}"
        )


@router.get("/statistics/global")
async def get_global_statistics() -> Dict[str, Any]:
    """Get global session statistics."""
    try:
        stats = await session_service.get_global_statistics()
        return stats
        
    except Exception as e:
        logger.error("Failed to get global statistics", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get global statistics: {str(e)}"
        )


@router.post("/{session_id}/validate")
async def validate_session(session_id: str) -> Dict[str, Any]:
    """Validate if a session is still valid."""
    try:
        is_valid = await session_service.validate_session(session_id)
        
        return {
            "session_id": session_id,
            "is_valid": is_valid,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error("Failed to validate session", 
                    session_id=session_id, 
                    error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to validate session: {str(e)}"
        )
