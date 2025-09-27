"""
MCP API endpoints for tool discovery and execution - CLEANED VERSION.

This module provides only the REST API endpoints actually used by the frontend.
"""

import json
import logging
import time
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, status, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel

from ...services.mcp.orchestrator import get_initialized_mcp_orchestrator
from ...schemas.agent import AgentChatRequest, AgentChatResponse
from ...services.agent import agent_service
from ...schemas.mcp import ExternalServerRequest

logger = logging.getLogger(__name__)

router = APIRouter(tags=["mcp"])


@router.post("/mcp/agent/chat", response_model=AgentChatResponse)
async def agent_chat(request: AgentChatRequest):
    """
    Process user message through the intelligent agent.
    
    This endpoint handles:
    - Intent detection using LLM
    - Routing decisions to appropriate tools
    - Tool execution when needed
    - Conversational responses
    - Conversation memory management
    
    Expected context format:
    {
        "document_content": "string - document text or empty",
        "chat_history": "string - previous conversation",
        "available_tools": "string - comma-separated tool names"
    }
    
    Args:
        request: Agent chat request with message and context
        
    Returns:
        Complete response with intent, routing, execution result, and metrics
    """
    try:
        logger.info(f"Processing chat request: '{request.message[:50]}...' ({len(request.message)} chars)")

        # Extract context information (all as strings)
        document_content = request.context.get("document_content", "")
        chat_history = request.context.get("chat_history", "")
        available_tools_string = request.context.get("available_tools", "")
        
        # Parse chat history from frontend
        parsed_chat_history = []
        if chat_history:
            try:
                parsed_chat_history = json.loads(chat_history) if isinstance(chat_history, str) else chat_history
            except json.JSONDecodeError:
                logger.warning("Failed to parse chat history, using empty list")
                parsed_chat_history = []
        
        # Parse available tools from frontend
        available_tools = []
        if available_tools_string:
            try:
                available_tools = json.loads(available_tools_string) if isinstance(available_tools_string, str) else available_tools_string
            except json.JSONDecodeError:
                # Fallback: split by comma if not JSON
                available_tools = [tool.strip() for tool in available_tools_string.split(",") if tool.strip()]
        
        # Prepare context for agent service
        agent_context = {
            "document_content": document_content,
            "chat_history": parsed_chat_history,
            "available_tools": available_tools
        }
        
        # Process through agent service
        start_time = time.time()
        response = await agent_service.process_message(
            message=request.message,
            context=agent_context
        )
        processing_time = time.time() - start_time
        
        logger.info(f"Agent processing completed in {processing_time:.2f}s")
        
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
        logger.error(f"Agent chat processing failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Agent Processing Failed",
                "message": str(e)
            }
        )


class ToolListResponse(BaseModel):
    tools: List[Dict[str, Any]]
    total_count: int
    built_in_count: int
    external_count: int
    timestamp: float


@router.get("/mcp/tools", response_model=ToolListResponse)
async def list_available_tools():
    """
    List all available MCP tools from both built-in and external servers.
    
    Returns:
        List of all available tools with source information
    """
    try:
        logger.info("Listing all available MCP tools")
        
        try:
            mcp_orchestrator = get_initialized_mcp_orchestrator()
            tools_data = await mcp_orchestrator.list_all_tools()
        except RuntimeError as e:
            if "not yet initialized" in str(e):
                logger.warning("MCP Orchestrator not initialized, returning empty tools list")
                return ToolListResponse(
                    tools=[],
                    total_count=0,
                    built_in_count=0,
                    external_count=0,
                    timestamp=time.time()
                )
            raise
        
        logger.info(f"Retrieved {tools_data['total_count']} total tools "
                   f"(built-in: {tools_data['built_in_count']}, "
                   f"external: {tools_data['external_count']})")
        
        return ToolListResponse(
            tools=tools_data["tools"],
            total_count=tools_data["total_count"],
            built_in_count=tools_data["built_in_count"],
            external_count=tools_data["external_count"],
            timestamp=tools_data["timestamp"]
        )
        
    except Exception as e:
        logger.error(f"Failed to list available tools: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal Server Error",
                "message": str(e)
            }
        )


@router.get("/mcp/tools/{tool_name}")
async def get_mcp_tool_info(tool_name: str):
    """
    Get detailed information about a specific MCP tool.
    
    Args:
        tool_name: Name of the tool to get information for
        
    Returns:
        Detailed tool information including schema and metadata
    """
    try:
        logger.info(f"Getting tool info for: {tool_name}")
        
        try:
            mcp_orchestrator = get_initialized_mcp_orchestrator()
            tool_info = await mcp_orchestrator.get_tool_info(tool_name)
        except RuntimeError as e:
            if "not yet initialized" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="MCP service not yet initialized"
                )
            raise
        
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
            detail={
                "error": "Internal Server Error",
                "message": str(e)
            }
        )


class ToolExecutionRequest(BaseModel):
    parameters: Dict[str, Any]


@router.post("/mcp/tools/{tool_name}/execute")
async def execute_mcp_tool(tool_name: str, request: ToolExecutionRequest):
    """
    Execute a specific MCP tool with the provided parameters.
    
    Args:
        tool_name: Name of the tool to execute
        request: Tool execution request with parameters
        
    Returns:
        Tool execution result
    """
    try:
        logger.info(f"Executing tool: {tool_name} with parameters: {request.parameters}")
        
        try:
            mcp_orchestrator = get_initialized_mcp_orchestrator()
            result = await mcp_orchestrator.execute_tool(tool_name, request.parameters)
        except RuntimeError as e:
            if "not yet initialized" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="MCP service not yet initialized"
                )
            raise
        
        logger.info(f"Tool execution completed for: {tool_name}")
        
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
            detail={
                "error": "Tool Execution Failed",
                "message": str(e)
            }
        )


@router.get("/mcp/external/servers")
async def get_external_servers():
    """
    List all external MCP servers.
    
    Returns:
        List of external MCP servers with their status
    """
    try:
        logger.info("Listing external MCP servers")
        
        try:
            mcp_orchestrator = get_initialized_mcp_orchestrator()
            servers = await mcp_orchestrator.list_external_servers()
        except RuntimeError as e:
            if "not yet initialized" in str(e):
                logger.warning("MCP Orchestrator not initialized, returning empty servers list")
                return {
                    "servers": [],
                    "total_count": 0,
                    "timestamp": time.time()
                }
            raise
        
        return {
            "servers": servers,
            "total_count": len(servers),
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Failed to list external servers: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Internal Server Error",
                "message": str(e)
            }
        )
