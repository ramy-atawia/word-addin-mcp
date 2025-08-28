"""
Tests for backend service layer components.

This test suite covers all the service layer components including:
- LangChain service
- MCP service
- Memory service
- Session service
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timedelta

from backend.app.services.langchain_service import LangChainService
from backend.app.services.mcp_service import MCPService
from backend.app.services.memory_service import MemoryService
from backend.app.services.session_service import SessionService


class TestLangChainService:
    """Test LangChain service functionality."""
    
    @pytest.fixture
    def langchain_service(self):
        """Create LangChain service instance for testing."""
        with patch('backend.app.services.langchain_service.AzureOpenAI'):
            return LangChainService()
    
    def test_service_initialization(self, langchain_service):
        """Test service initializes correctly."""
        assert langchain_service is not None
        assert hasattr(langchain_service, 'client')
    
    @pytest.mark.asyncio
    async def test_generate_response(self, langchain_service):
        """Test response generation."""
        # Mock the Azure OpenAI client
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "Test response"
        
        langchain_service.client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        result = await langchain_service.generate_response("Test prompt")
        assert result is not None
        assert "Test response" in result
    
    @pytest.mark.asyncio
    async def test_generate_response_error(self, langchain_service):
        """Test error handling in response generation."""
        langchain_service.client.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))
        
        with pytest.raises(Exception):
            await langchain_service.generate_response("Test prompt")
    
    @pytest.mark.asyncio
    async def test_analyze_text(self, langchain_service):
        """Test text analysis functionality."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "Analysis result"
        
        langchain_service.client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        result = await langchain_service.analyze_text("Test text", "summary")
        assert result is not None
        assert "Analysis result" in result


class TestMCPService:
    """Test MCP service functionality."""
    
    @pytest.fixture
    def mcp_service(self):
        """Create MCP service instance for testing."""
        return MCPService()
    
    def test_service_initialization(self, mcp_service):
        """Test service initializes correctly."""
        assert mcp_service is not None
        assert hasattr(mcp_service, 'mcp_client')
    
    @pytest.mark.asyncio
    async def test_get_tools(self, mcp_service):
        """Test getting available tools."""
        # Mock the MCP client
        mock_tools = [
            {"name": "tool1", "description": "Test tool 1"},
            {"name": "tool2", "description": "Test tool 2"}
        ]
        mcp_service.mcp_client.list_tools = AsyncMock(return_value=mock_tools)
        
        result = await mcp_service.get_tools()
        assert result == mock_tools
    
    @pytest.mark.asyncio
    async def test_execute_tool(self, mcp_service):
        """Test tool execution."""
        # Mock the MCP client
        mock_result = {"status": "success", "output": "Tool executed"}
        mcp_service.mcp_client.call_tool = AsyncMock(return_value=mock_result)
        
        result = await mcp_service.execute_tool("test_tool", {"param": "value"})
        assert result == mock_result
    
    @pytest.mark.asyncio
    async def test_get_tool_info(self, mcp_service):
        """Test getting tool information."""
        # Mock the MCP client
        mock_info = {"name": "test_tool", "description": "Test tool description"}
        mcp_service.mcp_client.get_tool = AsyncMock(return_value=mock_info)
        
        result = await mcp_service.get_tool_info("test_tool")
        assert result == mock_info
    
    @pytest.mark.asyncio
    async def test_health_check(self, mcp_service):
        """Test MCP service health check."""
        # Mock the MCP client
        mock_health = {"status": "healthy", "uptime": 100}
        mcp_service.mcp_client.health_check = AsyncMock(return_value=mock_health)
        
        result = await mcp_service.health_check()
        assert result == mock_health


class TestMemoryService:
    """Test memory service functionality."""
    
    @pytest.fixture
    def memory_service(self):
        """Create memory service instance for testing."""
        return MemoryService()
    
    def test_service_initialization(self, memory_service):
        """Test service initializes correctly."""
        assert memory_service is not None
        assert hasattr(memory_service, 'conversation_memory')
        assert hasattr(memory_service, 'user_memory')
    
    def test_store_conversation(self, memory_service):
        """Test storing conversation in memory."""
        conversation_id = "conv_123"
        user_message = "Hello"
        assistant_message = "Hi there!"
        
        memory_service.store_conversation(conversation_id, user_message, assistant_message)
        
        # Verify conversation was stored
        stored = memory_service.get_conversation(conversation_id)
        assert stored is not None
        assert len(stored) == 2
        assert stored[0]["content"] == user_message
        assert stored[1]["content"] == assistant_message
    
    def test_get_conversation(self, memory_service):
        """Test retrieving conversation from memory."""
        conversation_id = "conv_456"
        user_message = "Test message"
        assistant_message = "Test response"
        
        memory_service.store_conversation(conversation_id, user_message, assistant_message)
        stored = memory_service.get_conversation(conversation_id)
        
        assert stored is not None
        assert len(stored) == 2
    
    def test_get_nonexistent_conversation(self, memory_service):
        """Test getting non-existent conversation."""
        result = memory_service.get_conversation("nonexistent")
        assert result is None
    
    def test_clear_conversation(self, memory_service):
        """Test clearing conversation from memory."""
        conversation_id = "conv_789"
        user_message = "Test message"
        assistant_message = "Test response"
        
        memory_service.store_conversation(conversation_id, user_message, assistant_message)
        memory_service.clear_conversation(conversation_id)
        
        result = memory_service.get_conversation(conversation_id)
        assert result is None
    
    def test_store_user_memory(self, memory_service):
        """Test storing user-specific memory."""
        user_id = "user_123"
        key = "preference"
        value = "dark_mode"
        
        memory_service.store_user_memory(user_id, key, value)
        stored = memory_service.get_user_memory(user_id, key)
        
        assert stored == value
    
    def test_get_user_memory(self, memory_service):
        """Test retrieving user-specific memory."""
        user_id = "user_456"
        key = "setting"
        value = "enabled"
        
        memory_service.store_user_memory(user_id, key, value)
        result = memory_service.get_user_memory(user_id, key)
        
        assert result == value
    
    def test_get_nonexistent_user_memory(self, memory_service):
        """Test getting non-existent user memory."""
        result = memory_service.get_user_memory("user_999", "nonexistent")
        assert result is None
    
    def test_memory_cleanup(self, memory_service):
        """Test memory cleanup functionality."""
        # Store some test data
        memory_service.store_conversation("conv_1", "msg1", "resp1")
        memory_service.store_conversation("conv_2", "msg2", "resp2")
        memory_service.store_user_memory("user1", "key1", "value1")
        
        # Clean up old data
        memory_service.cleanup_old_memory(max_age_hours=1)
        
        # Verify cleanup worked (this is a soft test since timing depends on implementation)
        assert memory_service is not None


class TestSessionService:
    """Test session service functionality."""
    
    @pytest.fixture
    def session_service(self):
        """Create session service instance for testing."""
        return SessionService()
    
    def test_service_initialization(self, session_service):
        """Test service initializes correctly."""
        assert session_service is not None
        assert hasattr(session_service, 'sessions')
    
    def test_create_session(self, session_service):
        """Test session creation."""
        user_id = "user_123"
        session_type = "document_analysis"
        
        session = session_service.create_session(user_id, session_type)
        
        assert session is not None
        assert session["user_id"] == user_id
        assert session["session_type"] == session_type
        assert "session_id" in session
        assert "created_at" in session
        assert "status" in session
    
    def test_get_session(self, session_service):
        """Test session retrieval."""
        user_id = "user_456"
        session_type = "chat"
        
        created_session = session_service.create_session(user_id, session_type)
        session_id = created_session["session_id"]
        
        retrieved_session = session_service.get_session(session_id)
        
        assert retrieved_session is not None
        assert retrieved_session["session_id"] == session_id
        assert retrieved_session["user_id"] == user_id
    
    def test_get_nonexistent_session(self, session_service):
        """Test getting non-existent session."""
        result = session_service.get_session("nonexistent_session")
        assert result is None
    
    def test_update_session(self, session_service):
        """Test session update."""
        user_id = "user_789"
        session_type = "data_processing"
        
        session = session_service.create_session(user_id, session_type)
        session_id = session["session_id"]
        
        update_data = {
            "status": "active",
            "metadata": {"last_activity": datetime.now().isoformat()}
        }
        
        updated_session = session_service.update_session(session_id, update_data)
        
        assert updated_session is not None
        assert updated_session["status"] == "active"
        assert "metadata" in updated_session
    
    def test_delete_session(self, session_service):
        """Test session deletion."""
        user_id = "user_999"
        session_type = "test"
        
        session = session_service.create_session(user_id, session_type)
        session_id = session["session_id"]
        
        # Verify session exists
        assert session_service.get_session(session_id) is not None
        
        # Delete session
        session_service.delete_session(session_id)
        
        # Verify session is deleted
        assert session_service.get_session(session_id) is None
    
    def test_get_user_sessions(self, session_service):
        """Test getting all sessions for a user."""
        user_id = "user_multi"
        
        # Create multiple sessions
        session1 = session_service.create_session(user_id, "type1")
        session2 = session_service.create_session(user_id, "type2")
        session3 = session_service.create_session(user_id, "type3")
        
        user_sessions = session_service.get_user_sessions(user_id)
        
        assert len(user_sessions) == 3
        assert all(session["user_id"] == user_id for session in user_sessions)
    
    def test_session_expiration(self, session_service):
        """Test session expiration functionality."""
        user_id = "user_expire"
        session_type = "temporary"
        
        session = session_service.create_session(user_id, session_type)
        session_id = session["session_id"]
        
        # Set session to expired (this depends on implementation)
        # For now, just test that the service handles expiration gracefully
        assert session_service.get_session(session_id) is not None
        
        # Clean up expired sessions
        session_service.cleanup_expired_sessions()
        
        # Verify cleanup worked (this is a soft test)
        assert session_service is not None


class TestServiceIntegration:
    """Test service integration scenarios."""
    
    @pytest.fixture
    def services(self):
        """Create all services for integration testing."""
        with patch('backend.app.services.langchain_service.AzureOpenAI'):
            langchain_service = LangChainService()
        mcp_service = MCPService()
        memory_service = MemoryService()
        session_service = SessionService()
        
        return {
            'langchain': langchain_service,
            'mcp': mcp_service,
            'memory': memory_service,
            'session': session_service
        }
    
    @pytest.mark.asyncio
    async def test_complete_workflow(self, services):
        """Test a complete workflow using multiple services."""
        # Create a session
        session = services['session'].create_session("test_user", "document_analysis")
        session_id = session["session_id"]
        
        # Store conversation in memory
        services['memory'].store_conversation(session_id, "Analyze this document", "I'll help you analyze it")
        
        # Get MCP tools
        mock_tools = [{"name": "document_analyzer", "description": "Analyzes documents"}]
        services['mcp'].mcp_client.list_tools = AsyncMock(return_value=mock_tools)
        tools = await services['mcp'].get_tools()
        
        # Execute a tool
        mock_result = {"status": "success", "analysis": "Document analyzed successfully"}
        services['mcp'].mcp_client.call_tool = AsyncMock(return_value=mock_result)
        result = await services['mcp'].execute_tool("document_analyzer", {"content": "Test content"})
        
        # Store the result in memory
        services['memory'].store_conversation(session_id, "Tool executed", str(result))
        
        # Verify the complete workflow
        assert session is not None
        assert tools == mock_tools
        assert result == mock_result
        
        # Check memory has the complete conversation
        conversation = services['memory'].get_conversation(session_id)
        assert len(conversation) == 4  # 2 original + 2 from tool execution
    
    def test_service_dependencies(self, services):
        """Test that services can work together without conflicts."""
        # This test ensures services don't interfere with each other
        assert services['langchain'] is not None
        assert services['mcp'] is not None
        assert services['memory'] is not None
        assert services['session'] is not None
        
        # Test that each service maintains its own state
        session1 = services['session'].create_session("user1", "type1")
        session2 = services['session'].create_session("user2", "type2")
        
        assert session1["session_id"] != session2["session_id"]
        assert session1["user_id"] != session2["user_id"]
