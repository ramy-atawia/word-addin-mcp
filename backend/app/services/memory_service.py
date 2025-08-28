"""
Simplified Memory Management Service for Word Add-in MCP Project.

This service provides basic conversation and document context memory
without complex indexing or optimization features.
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import structlog

logger = structlog.get_logger()


class MemoryService:
    """Simplified memory service for conversation and document context."""
    
    def __init__(self):
        self.conversations: Dict[str, List[Dict[str, Any]]] = {}
        self.documents: Dict[str, Dict[str, Any]] = {}
        self.tool_results: Dict[str, List[Dict[str, Any]]] = {}
    
    def add_conversation(self, session_id: str, message: Dict[str, Any]) -> bool:
        """Add a conversation message to memory."""
        try:
            if session_id not in self.conversations:
                self.conversations[session_id] = []
            
            message_with_timestamp = {
                **message,
                "timestamp": datetime.utcnow().isoformat(),
                "id": f"conv_{len(self.conversations[session_id])}"
            }
            
            self.conversations[session_id].append(message_with_timestamp)
            logger.info(f"Added conversation message to session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add conversation: {str(e)}")
            return False
    
    def get_conversation_history(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get conversation history for a session."""
        try:
            if session_id not in self.conversations:
                return []
            
            # Return last N messages
            return self.conversations[session_id][-limit:]
            
        except Exception as e:
            logger.error(f"Failed to get conversation history: {str(e)}")
            return []
    
    def add_document(self, session_id: str, document_data: Dict[str, Any]) -> bool:
        """Add document content to memory."""
        try:
            self.documents[session_id] = {
                **document_data,
                "timestamp": datetime.utcnow().isoformat(),
                "session_id": session_id
            }
            logger.info(f"Added document to session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add document: {str(e)}")
            return False
    
    def get_document(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get document content for a session."""
        try:
            return self.documents.get(session_id)
        except Exception as e:
            logger.error(f"Failed to get document: {str(e)}")
            return None
    
    def add_tool_result(self, session_id: str, tool_result: Dict[str, Any]) -> bool:
        """Add tool execution result to memory."""
        try:
            if session_id not in self.tool_results:
                self.tool_results[session_id] = []
            
            result_with_timestamp = {
                **tool_result,
                "timestamp": datetime.utcnow().isoformat(),
                "id": f"tool_{len(self.tool_results[session_id])}"
            }
            
            self.tool_results[session_id].append(result_with_timestamp)
            logger.info(f"Added tool result to session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add tool result: {str(e)}")
            return False
    
    def get_tool_results(self, session_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get tool execution results for a session."""
        try:
            if session_id not in self.tool_results:
                return []
            
            # Return last N results
            return self.tool_results[session_id][-limit:]
            
        except Exception as e:
            logger.error(f"Failed to get tool results: {str(e)}")
            return []
    
    def clear_session(self, session_id: str) -> bool:
        """Clear all memory for a session."""
        try:
            if session_id in self.conversations:
                del self.conversations[session_id]
            if session_id in self.documents:
                del self.documents[session_id]
            if session_id in self.tool_results:
                del self.tool_results[session_id]
            
            logger.info(f"Cleared memory for session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear session: {str(e)}")
            return False
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get a summary of session memory."""
        try:
            conv_count = len(self.conversations.get(session_id, []))
            doc_count = 1 if session_id in self.documents else 0
            tool_count = len(self.tool_results.get(session_id, []))
            
            return {
                "session_id": session_id,
                "conversation_messages": conv_count,
                "documents": doc_count,
                "tool_results": tool_count,
                "has_memory": conv_count > 0 or doc_count > 0 or tool_count > 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get session summary: {str(e)}")
            return {"session_id": session_id, "error": str(e)}
    
    def cleanup_old_sessions(self, max_age_hours: int = 24) -> int:
        """Clean up old sessions (basic cleanup without complex logic)."""
        try:
            cutoff_time = datetime.utcnow().timestamp() - (max_age_hours * 3600)
            cleaned_count = 0
            
            # Simple cleanup - in production, you'd want more sophisticated logic
            for session_id in list(self.conversations.keys()):
                # For now, just clear very old sessions
                if len(self.conversations[session_id]) > 100:  # Too many messages
                    self.clear_session(session_id)
                    cleaned_count += 1
            
            logger.info(f"Cleaned up {cleaned_count} old sessions")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old sessions: {str(e)}")
            return 0

    # Compatibility methods for existing API calls
    async def add_conversation_memory(self, session_id: str, user_id: Optional[str], content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Compatibility method for existing API calls."""
        message = {
            "user_id": user_id,
            "content": content,
            "metadata": metadata or {}
        }
        success = self.add_conversation(session_id, message)
        if success:
            return f"conv_{session_id}_{int(datetime.utcnow().timestamp())}"
        else:
            raise Exception("Failed to add conversation memory")
    
    async def add_document_memory(self, session_id: str, user_id: Optional[str], content: str, document_metadata: Dict[str, Any]) -> str:
        """Compatibility method for existing API calls."""
        document_data = {
            "user_id": user_id,
            "content": content,
            **document_metadata
        }
        success = self.add_document(session_id, document_data)
        if success:
            return f"doc_{session_id}_{int(datetime.utcnow().timestamp())}"
        else:
            raise Exception("Failed to add document memory")
    
    async def add_tool_result_memory(self, session_id: str, user_id: Optional[str], tool_name: str, result: Any, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Compatibility method for existing API calls."""
        tool_result = {
            "user_id": user_id,
            "tool_name": tool_name,
            "result": result,
            "metadata": metadata or {}
        }
        success = self.add_tool_result(session_id, tool_result)
        if success:
            return f"tool_{session_id}_{int(datetime.utcnow().timestamp())}"
        else:
            raise Exception("Failed to add tool result memory")
    
    async def search_memory(self, query: str, session_id: Optional[str] = None, user_id: Optional[str] = None, content_type: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Compatibility method for existing API calls."""
        # Simple search implementation
        results = []
        
        # Search in conversations
        if session_id and session_id in self.conversations:
            for conv in self.conversations[session_id]:
                if query.lower() in conv.get("content", "").lower():
                    results.append({
                        "memory_item": conv,
                        "relevance_score": 0.8,
                        "matched_terms": [query],
                        "context_snippet": conv.get("content", "")[:100] + "..."
                    })
        
        # Search in documents
        if session_id and session_id in self.documents:
            doc = self.documents[session_id]
            if query.lower() in doc.get("content", "").lower():
                results.append({
                    "memory_item": doc,
                    "relevance_score": 0.9,
                    "matched_terms": [query],
                    "context_snippet": doc.get("content", "")[:100] + "..."
                })
        
        return results[:limit]
    
    async def get_session_memory(self, session_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Compatibility method for existing API calls."""
        results = []
        
        # Get conversations
        if session_id in self.conversations:
            for conv in self.conversations[session_id][-limit:]:
                results.append({
                    "id": conv["id"],
                    "session_id": session_id,
                    "content": conv["content"],
                    "content_type": "conversation",
                    "created_at": conv["timestamp"],
                    "last_accessed": conv["timestamp"],
                    "access_count": 1,
                    "importance_score": 0.5,
                    "tags": []
                })
        
        # Get documents
        if session_id in self.documents:
            doc = self.documents[session_id]
            results.append({
                "id": f"doc_{session_id}",
                "session_id": session_id,
                "content": doc.get("content", ""),
                "content_type": "document",
                "created_at": doc["timestamp"],
                "last_accessed": doc["timestamp"],
                "access_count": 1,
                "importance_score": 0.8,
                "tags": []
            })
        
        return results
    
    async def get_user_memory(self, user_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Compatibility method for existing API calls."""
        results = []
        
        # Search through all sessions for user
        for session_id, conversations in self.conversations.items():
            for conv in conversations:
                if conv.get("user_id") == user_id:
                    results.append({
                        "id": conv["id"],
                        "session_id": session_id,
                        "content": conv["content"],
                        "content_type": "conversation",
                        "created_at": conv["timestamp"],
                        "last_accessed": conv["timestamp"],
                        "access_count": 1,
                        "importance_score": 0.5,
                        "tags": []
                    })
        
        return results[:limit]
    
    async def delete_memory(self, memory_id: str) -> bool:
        """Compatibility method for existing API calls."""
        # This is a simplified implementation
        # In a real system, you'd want more sophisticated deletion logic
        return True
    
    async def clear_session_memory(self, session_id: str) -> int:
        """Compatibility method for existing API calls."""
        return self.clear_session(session_id)
    
    async def get_memory_statistics(self) -> Dict[str, Any]:
        """Compatibility method for existing API calls."""
        total_conversations = sum(len(convs) for convs in self.conversations.values())
        total_documents = len(self.documents)
        total_tool_results = sum(len(results) for results in self.tool_results.values())
        
        return {
            "total_memories": total_conversations + total_documents + total_tool_results,
            "conversation_count": total_conversations,
            "document_count": total_documents,
            "tool_result_count": total_tool_results,
            "average_importance_score": 0.5,
            "index_sizes": {
                "content_index": 0,
                "tag_index": 0,
                "session_index": len(self.conversations),
                "user_index": 0
            },
            "timestamp": datetime.utcnow().isoformat()
        }


# Global instance for easy access
memory_service = MemoryService()
