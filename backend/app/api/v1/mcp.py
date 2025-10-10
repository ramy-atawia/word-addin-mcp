"""
MCP API endpoints for tool discovery and execution.

This module provides REST API endpoints for MCP tool interaction.
"""

import json
import logging
import time
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from ...services.mcp.orchestrator import get_initialized_mcp_orchestrator
from ...schemas.agent import AgentChatRequest, AgentChatResponse
from ...services.agent import agent_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["mcp"])


# ============================================================================
# Agent Chat Endpoint
# ============================================================================

@router.post("/mcp/agent/chat", response_model=AgentChatResponse)
async def agent_chat(request: AgentChatRequest):
    """
    Process user message through the intelligent agent.
    
    Handles intent detection, tool routing, and conversational responses.
    
    Expected context:
    - document_content: string - document text or empty
    - chat_history: string - previous conversation (JSON array)
    - available_tools: string - comma-separated tool names or JSON array
    """
    try:
        logger.info(f"Processing chat: '{request.message[:50]}...'")

        # Parse context from frontend
        chat_history = _parse_json_field(request.context.get("chat_history", ""), [])
        available_tools = _parse_json_field(request.context.get("available_tools", ""), [])
        
        # Prepare agent context
        agent_context = {
            "document_content": request.context.get("document_content", ""),
            "chat_history": chat_history,
            "available_tools": available_tools
        }
        
        # Process through agent
        start_time = time.time()
        response = await agent_service.process_user_message(
            user_message=request.message,
            document_content=agent_context.get("document_content", ""),
            available_tools=agent_context.get("available_tools", []),
            frontend_chat_history=agent_context.get("chat_history", [])
        )
        processing_time = time.time() - start_time
        
        logger.info(f"Agent completed in {processing_time:.2f}s")
        
        return AgentChatResponse(
            response=response.get("response", ""),
            intent_type=response.get("intent_type", "conversation"),
            tool_name=response.get("tool_name"),
            execution_result=response.get("execution_result"),
            processing_time=processing_time,
            success=response.get("success", True),
            error=response.get("error")
        )
        
    except Exception as e:
        logger.error(f"Agent chat failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Agent Processing Failed", "message": str(e)}
        )


# ============================================================================
# Tool Management Endpoints
# ============================================================================

class ToolListResponse(BaseModel):
    tools: List[Dict[str, Any]]
    total_count: int
    built_in_count: int
    external_count: int
    timestamp: float


@router.get("/mcp/tools", response_model=ToolListResponse)
async def list_available_tools():
    """List all available MCP tools from built-in and external servers."""
    try:
        logger.info("Listing all available MCP tools")
        
        mcp_orchestrator = _get_orchestrator_or_empty()
        if not mcp_orchestrator:
            return ToolListResponse(
                tools=[], total_count=0, 
                built_in_count=0, external_count=0, 
                timestamp=time.time()
            )
        
        tools_data = await mcp_orchestrator.list_all_tools()
        
        logger.info(f"Retrieved {tools_data['total_count']} total tools")
        
        return ToolListResponse(
            tools=tools_data["tools"],
            total_count=tools_data["total_count"],
            built_in_count=tools_data["built_in_count"],
            external_count=tools_data["external_count"],
            timestamp=tools_data["timestamp"]
        )
        
    except Exception as e:
        logger.error(f"Failed to list tools: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal Server Error", "message": str(e)}
        )


@router.get("/mcp/tools/{tool_name}")
async def get_tool_info(tool_name: str):
    """Get detailed information about a specific MCP tool."""
    try:
        logger.info(f"Getting tool info: {tool_name}")
        
        mcp_orchestrator = _get_orchestrator_or_error()
        tool_info = await mcp_orchestrator.get_tool_info(tool_name)
        
        if not tool_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tool '{tool_name}' not found"
            )
        
        return tool_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get tool info for {tool_name}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal Server Error", "message": str(e)}
        )


# ============================================================================
# Tool Execution Endpoints
# ============================================================================

class ToolExecutionRequest(BaseModel):
    parameters: Dict[str, Any]


@router.post("/mcp/tools/{tool_name}/execute")
async def execute_tool_by_name(tool_name: str, request: ToolExecutionRequest):
    """Execute a specific MCP tool with provided parameters."""
    try:
        logger.info(f"Executing tool: {tool_name}")
        
        mcp_orchestrator = _get_orchestrator_or_error()
        result = await mcp_orchestrator.execute_tool(tool_name, request.parameters)
        
        logger.info(f"Tool execution completed: {tool_name}")
        
        return {
            "tool_name": tool_name,
            "result": result,
            "success": True,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Tool execution failed for {tool_name}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Tool Execution Failed", "message": str(e)}
        )


# ============================================================================
# External Server Management
# ============================================================================

@router.get("/mcp/external/servers")
async def get_external_servers():
    """List all external MCP servers with their status."""
    try:
        logger.info("Listing external MCP servers")
        
        mcp_orchestrator = _get_orchestrator_or_empty()
        if not mcp_orchestrator:
            return {
                "servers": [],
                "total_count": 0,
                "timestamp": time.time()
            }
        
        servers = await mcp_orchestrator.get_external_servers()
        
        return {
            "servers": servers,
            "total_count": len(servers),
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Failed to list external servers: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "Internal Server Error", "message": str(e)}
        )


# ============================================================================
# Helper Functions
# ============================================================================

def _parse_json_field(value: str, default: Any) -> Any:
    """Parse JSON field from string, return default on failure."""
    if not value:
        return default
    
    try:
        return json.loads(value) if isinstance(value, str) else value
    except json.JSONDecodeError:
        logger.warning(f"Failed to parse JSON field, using default")
        # Try comma-separated fallback for arrays
        if isinstance(default, list) and isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return default


def _get_orchestrator_or_empty():
    """Get orchestrator or return None if not initialized."""
    try:
        return get_initialized_mcp_orchestrator()
    except RuntimeError as e:
        if "not yet initialized" in str(e):
            logger.warning("MCP Orchestrator not initialized")
            return None
        raise


def _get_orchestrator_or_error():
    """Get orchestrator or raise HTTP error if not initialized."""
    try:
        return get_initialized_mcp_orchestrator()
    except RuntimeError as e:
        if "not yet initialized" in str(e):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="MCP service not yet initialized"
            )
        raise