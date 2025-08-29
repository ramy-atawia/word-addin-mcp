"""
MCP tools API endpoints for Word Add-in MCP Project.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import structlog
from typing import Dict, Any, List, Optional
import time
from datetime import datetime

from app.core.config import settings
from app.schemas.mcp import (
    MCPToolExecutionRequest,
    MCPToolExecutionResponse,
    MCPToolListResponse,
    MCPToolDefinition,
    MCPError,
    MCPToolResult
)
from app.services.langchain_service import langchain_service
from app.services.memory_service import memory_service
from app.services.web_search_service import web_search_service
from app.services.file_system_service import file_system_service
from app.services.validation_service import validation_service
from app.services.tool_execution_service import tool_execution_service
from app.core.config import is_azure_openai_configured
from app.services.llm_client import llm_client

router = APIRouter()
logger = structlog.get_logger()


@router.post("/initialize")
async def initialize_mcp_connection(
    client_info: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Initialize MCP connection (MCP-compliant).
    
    Args:
        client_info: Client information for MCP protocol initialization
        
    Returns:
        MCP initialization response with server capabilities
    """
    try:
        logger.info("MCP connection initialization", client_info=client_info)
        
        # TODO: Implement actual MCP server initialization
        # This is a placeholder implementation
        
        response = {
            "jsonrpc": "2.0",
            "id": client_info.get("id", "init_001"),
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {
                        "listChanged": True
                    }
                },
                "serverInfo": {
                    "name": "word-addin-mcp-server",
                    "version": "1.0.0"
                }
            }
        }
        
        logger.info("MCP connection initialized successfully")
        return response
        
    except Exception as e:
        logger.error("MCP connection initialization failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to initialize MCP connection"
        )


@router.get("/tools", response_model=MCPToolListResponse)
async def list_available_tools() -> MCPToolListResponse:
    """
    List all available MCP tools (MCP-compliant).
    
    Returns:
        MCPToolListResponse containing available tools following MCP protocol
    """
    try:
        # TODO: Implement actual tool discovery from MCP server
        tools = [
            MCPToolDefinition(
                name="file_reader",
                description="Read file contents from the local filesystem",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "File path to read",
                            "minLength": 1,
                            "maxLength": 500
                        },
                        "encoding": {
                            "type": "string",
                            "description": "File encoding",
                            "enum": ["utf-8", "ascii", "latin-1", "utf-16"],
                            "default": "utf-8"
                        },
                        "max_size": {
                            "type": "integer",
                            "description": "Maximum file size to read in bytes",
                            "minimum": 1,
                            "maximum": 10485760,
                            "default": 1048576
                        }
                    },
                    "required": ["path"]
                }
            ),
            MCPToolDefinition(
                name="text_processor",
                description="Process and manipulate text content",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Text to process",
                            "minLength": 1
                        },
                        "operation": {
                            "type": "string",
                            "description": "Processing operation",
                            "enum": ["summarize", "translate", "enhance", "extract_keywords", "sentiment_analysis"]
                        }
                    },
                    "required": ["text", "operation"]
                }
            ),
            MCPToolDefinition(
                name="document_analyzer",
                description="Analyze document content for insights",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "content": {
                            "type": "string",
                            "description": "Document content to analyze",
                            "minLength": 1
                        },
                        "analysis_type": {
                            "type": "string",
                            "description": "Type of analysis",
                            "enum": ["readability", "structure", "tone", "summary", "keyword_extraction"]
                        }
                    },
                    "required": ["content", "analysis_type"]
                }
            ),
            MCPToolDefinition(
                name="web_content_fetcher",
                description="Fetch and process web content",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "URL to fetch content from",
                            "format": "uri"
                        },
                        "extract_text": {
                            "type": "boolean",
                            "description": "Whether to extract text content",
                            "default": True
                        },
                        "max_size": {
                            "type": "integer",
                            "description": "Maximum content size to fetch",
                            "minimum": 1,
                            "maximum": 10485760,
                            "default": 1048576
                        }
                    },
                    "required": ["url"]
                }
            ),
            MCPToolDefinition(
                name="data_formatter",
                description="Format and structure data for document presentation",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "data": {
                            "type": "string",
                            "description": "Data to format",
                            "minLength": 1
                        },
                        "format": {
                            "type": "string",
                            "description": "Output format",
                            "enum": ["table", "list", "summary", "json", "csv", "markdown"]
                        }
                    },
                    "required": ["data", "format"]
                }
            )
        ]
        
        logger.info("MCP tools listed successfully", tool_count=len(tools))
        
        response = MCPToolListResponse(
            tools=tools,
            total_count=len(tools),
            protocol_version="2024-11-05",
            server_capabilities={
                "tools": {
                    "listChanged": True
                }
            },
            timestamp=datetime.now()
        )
        
        logger.info("Created response object", response_type=type(response))
        return response
        
    except Exception as e:
        logger.error("Failed to list MCP tools", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve MCP tools"
        )


@router.post("/tools/list")
async def list_mcp_tools(
    mcp_request: Dict[str, Any]
) -> Dict[str, Any]:
    """
    List available MCP tools using JSON-RPC 2.0 format (MCP-compliant).
    
    Args:
        mcp_request: JSON-RPC 2.0 formatted MCP tools list request
        
    Returns:
        JSON-RPC 2.0 formatted MCP tools list response
    """
    try:
        # Extract MCP request parameters
        method = mcp_request.get("method", "")
        request_id = mcp_request.get("id", "")
        
        if method != "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": "Method not found",
                    "data": {"method": method}
                }
            }
        
        logger.info("MCP tools list request received", request_id=request_id)
        
        # Get tools list
        tools = [
            {
                "name": "file_reader",
                "description": "Read file contents from the local filesystem",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File path to read", "minLength": 1, "maxLength": 500},
                        "encoding": {"type": "string", "description": "File encoding", "enum": ["utf-8", "ascii", "latin-1", "utf-16"], "default": "utf-8"},
                        "max_size": {"type": "integer", "description": "Maximum file size to read in bytes", "minimum": 1, "maximum": 10485760, "default": 1048576}
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "text_processor",
                "description": "Process and manipulate text content",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Text to process", "minLength": 1},
                        "operation": {"type": "string", "description": "Processing operation", "enum": ["summarize", "translate", "enhance", "extract_keywords", "sentiment_analysis"]}
                    },
                    "required": ["text", "operation"]
                }
            },
            {
                "name": "document_analyzer",
                "description": "Analyze document content for insights",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string", "description": "Document content to analyze", "minLength": 1},
                        "analysis_type": {"type": "string", "description": "Type of analysis", "enum": ["readability", "structure", "tone", "summary", "keyword_extraction"]}
                    },
                    "required": ["content", "analysis_type"]
                }
            },
            {
                "name": "web_content_fetcher",
                "description": "Fetch and process web content",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "URL to fetch content from", "format": "uri"},
                        "extract_text": {"type": "boolean", "description": "Whether to extract text content", "default": True},
                        "max_size": {"type": "integer", "description": "Maximum content size to fetch", "minimum": 1, "maximum": 10485760, "default": 1048576}
                    },
                    "required": ["url"]
                }
            },
            {
                "name": "data_formatter",
                "description": "Format and structure data for document presentation",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "data": {"type": "string", "description": "Data to format", "minLength": 1},
                        "format": {"type": "string", "description": "Output format", "enum": ["table", "list", "summary", "json", "csv", "markdown"]}
                    },
                    "required": ["data", "format"]
                }
            }
        ]
        
        # Return MCP-compliant response
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "tools": tools
            }
        }
        
        logger.info("MCP tools list completed successfully", tool_count=len(tools))
        return response
        
    except Exception as e:
        logger.error("MCP tools list failed", error=str(e))
        return {
            "jsonrpc": "2.0",
            "id": mcp_request.get("id", ""),
            "error": {
                "code": -32603,
                "message": "Internal error",
                "data": {"details": str(e)}
            }
        }





@router.get("/tools/{tool_name}")
async def get_tool_info(tool_name: str) -> MCPToolDefinition:
    """
    Get information about a specific MCP tool.
    
    Args:
        tool_name: Name of the tool to get info for
        
    Returns:
        MCPToolDefinition containing tool information
    """
    try:
        # TODO: Implement actual tool info retrieval from MCP server
        # This is a placeholder implementation
        tools = {
            "file_reader": MCPToolDefinition(
                name="file_reader",
                description="Read file contents from the local filesystem",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "File path to read", "minLength": 1, "maxLength": 500},
                        "encoding": {"type": "string", "description": "File encoding", "enum": ["utf-8", "ascii", "latin-1", "utf-16"], "default": "utf-8"},
                        "max_size": {"type": "integer", "description": "Maximum file size to read in bytes", "minimum": 1, "maximum": 10485760, "default": 1048576}
                    },
                    "required": ["path"]
                }
            ),
            "text_processor": MCPToolDefinition(
                name="text_processor",
                description="Process and manipulate text content",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Text to process", "minLength": 1},
                        "operation": {"type": "string", "description": "Processing operation", "enum": ["summarize", "translate", "enhance", "extract_keywords", "sentiment_analysis"]}
                    },
                    "required": ["text", "operation"]
                }
            ),
            "document_analyzer": MCPToolDefinition(
                name="document_analyzer",
                description="Analyze document content for insights",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "content": {"type": "string", "description": "Document content to analyze", "minLength": 1},
                        "analysis_type": {"type": "string", "description": "Type of analysis", "enum": ["readability", "structure", "tone", "summary", "keyword_extraction"]}
                    },
                    "required": ["content", "analysis_type"]
                }
            ),
            "web_content_fetcher": MCPToolDefinition(
                name="web_content_fetcher",
                description="Fetch and process web content",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "URL to fetch content from", "format": "uri"},
                        "extract_text": {"type": "boolean", "description": "Whether to extract text content", "default": True},
                        "max_size": {"type": "integer", "description": "Maximum content size to fetch", "minimum": 1, "maximum": 10485760, "default": 1048576}
                    },
                    "required": ["url"]
                }
            ),
            "data_formatter": MCPToolDefinition(
                name="data_formatter",
                description="Format and structure data for document presentation",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "data": {"type": "string", "description": "Data to format", "minLength": 1},
                        "format": {"type": "string", "description": "Output format", "enum": ["table", "list", "summary", "json", "csv", "markdown"]}
                    },
                    "required": ["data", "format"]
                }
            )
        }
        
        if tool_name not in tools:
            raise HTTPException(
                status_code=404,
                detail=f"Tool '{tool_name}' not found"
            )
        
        return tools[tool_name]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to retrieve tool info", tool_name=tool_name, error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve tool information"
        )


@router.post("/tools/call")
async def call_mcp_tool(
    mcp_request: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Execute an MCP tool using JSON-RPC 2.0 format (MCP-compliant).
    
    Args:
        mcp_request: JSON-RPC 2.0 formatted MCP tool call request
        
    Returns:
        JSON-RPC 2.0 formatted MCP tool call response
    """
    try:
        # Extract MCP request parameters
        method = mcp_request.get("method", "")
        params = mcp_request.get("params", {})
        request_id = mcp_request.get("id", "")
        
        if method != "tools/call":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": "Method not found",
                    "data": {"method": method}
                }
            }
        
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})
        
        logger.info(
            "MCP tool call received",
            tool_name=tool_name,
            request_id=request_id
        )
        
        # Execute the tool
        if tool_name == "file_reader":
            result = await _execute_file_reader(arguments)
        elif tool_name == "text_processor":
            result = await _execute_text_processor(arguments)
        elif tool_name == "document_analyzer":
            result = await _execute_document_analyzer(arguments)
        elif tool_name == "web_content_fetcher":
            result = await _execute_web_content_fetcher(arguments)
        elif tool_name == "data_formatter":
            result = await _execute_data_formatter(arguments)
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32602,
                    "message": "Invalid params",
                    "data": {"details": f"Unknown tool: {tool_name}"}
                }
            }
        
        # Return MCP-compliant response
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": str(result)
                    }
                ]
            }
        }
        
        logger.info("MCP tool call completed successfully", tool_name=tool_name)
        return response
        
    except Exception as e:
        logger.error("MCP tool call failed", error=str(e))
        return {
            "jsonrpc": "2.0",
            "id": mcp_request.get("id", ""),
            "error": {
                "code": -32603,
                "message": "Internal error",
                "data": {"details": str(e)}
            }
        }


@router.post("/tools/execute", response_model=MCPToolExecutionResponse)
async def execute_mcp_tool(
    request: MCPToolExecutionRequest,
    background_tasks: BackgroundTasks
) -> MCPToolExecutionResponse:
    """
    Execute an MCP tool with the given parameters.
    
    Args:
        request: MCPToolExecutionRequest containing tool execution details
        background_tasks: FastAPI background tasks for async operations
    
    Returns:
        MCPToolExecutionResponse containing tool execution results
    """
    try:
        start_time = time.time()
        
        logger.info(
            "Executing MCP tool",
            tool_name=request.tool_name,
            session_id=request.session_id
        )
        
        # Execute tool using the tool execution service
        if request.tool_name == "file_reader":
            result = await tool_execution_service.execute_file_reader(request.parameters)
        elif request.tool_name == "text_processor":
            result = await tool_execution_service.execute_text_processor(request.parameters)
        elif request.tool_name == "document_analyzer":
            result = await tool_execution_service.execute_document_analyzer(request.parameters)
        elif request.tool_name == "web_content_fetcher":
            result = await tool_execution_service.execute_web_content_fetcher(request.parameters)
        elif request.tool_name == "data_formatter":
            result = await tool_execution_service.execute_data_formatter(request.parameters)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown tool: {request.tool_name}"
            )
        
        execution_time = time.time() - start_time
        
        # Log successful execution
        logger.info(
            "MCP tool executed successfully",
            tool_name=request.tool_name,
            execution_time=execution_time,
            session_id=request.session_id
        )
        
        return MCPToolExecutionResponse(
            tool_name=request.tool_name,
            session_id=request.session_id,
            result=MCPToolResult(
                content=result,
                content_type="text",
                metadata={"execution_time": execution_time}
            ),
            execution_time=execution_time,
            status="success",
            mcp_protocol_version="2024-11-05"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "MCP tool execution failed",
            tool_name=request.tool_name,
            error=str(e),
            session_id=request.session_id
        )
        
        return MCPToolExecutionResponse(
            tool_name=request.tool_name,
            session_id=request.session_id,
            error=MCPError(
                code="TOOL_EXECUTION_FAILED",
                message=str(e),
                details="Tool execution encountered an unexpected error"
            ),
            execution_time=execution_time,
            status="error",
            mcp_protocol_version="2024-11-05"
        )


@router.post("/conversation")
async def handle_conversation(
    request: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Handle conversational queries using Azure OpenAI LLM.
    
    Args:
        request: Contains user message and context
        
    Returns:
        AI-generated conversational response
    """
    try:
        user_message = request.get("message", "")
        context = request.get("context", "general")
        
        if not user_message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        # Import LLM client for conversational AI
        from app.services.llm_client import llm_client
        from app.core.config import is_azure_openai_configured
        
        # Check if Azure OpenAI is available
        if not is_azure_openai_configured():
            return {
                "status": "error",
                "error_message": "Azure OpenAI not configured",
                "error_type": "configuration_error"
            }
        
        # Create conversational prompt based on context
        if context == "greeting":
            system_prompt = "You are a helpful AI assistant for document analysis and text processing. Respond warmly and naturally to greetings, then briefly explain how you can help with document work."
        elif context == "help":
            system_prompt = "You are an AI assistant specializing in document analysis, text processing, and web content fetching. Explain your capabilities in a friendly, helpful way with specific examples."
        elif context == "conversation":
            system_prompt = "You are a friendly AI assistant for document analysis and text processing. Respond naturally and conversationally to general questions and social interactions. Be warm, helpful, and guide the conversation toward how you can assist with document work. For questions about weather, time, or general knowledge that you can't answer (like current weather), politely explain that you're focused on document analysis and suggest how you can help with that instead."
        else:
            system_prompt = "You are a helpful AI assistant for document analysis and text processing. Be conversational, friendly, and helpful."
        
        # Generate conversational response using LLM
        result = llm_client.generate_text(
            prompt=user_message,
            max_tokens=200,
            temperature=0.7,
            system_message=system_prompt
        )
        
        if result.get("success"):
            return {
                "status": "success",
                "response": result["text"],
                "ai_model": llm_client.get_model_info()["model"],
                "usage": result.get("usage", {}),
                "confidence": 0.95
            }
        else:
            return {
                "status": "error",
                "error_message": f"LLM generation failed: {result.get('error', 'Unknown error')}",
                "error_type": "llm_error"
            }
        
    except Exception as e:
        logger.error(f"Conversation handling failed: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Conversation failed: {str(e)}",
            "error_type": "execution_error"
        }

@router.get("/status")
async def get_mcp_status() -> Dict[str, Any]:
    """
    Get MCP server connection status.
    
    Returns:
        Dict containing MCP server status information
    """
    try:
        # TODO: Implement actual MCP server status check
        status = {
            "status": "connected",
            "server_url": settings.MCP_SERVER_URL,
            "protocol_version": "2024-11-05",
            "last_heartbeat": time.time(),
            "connection_health": "healthy",
            "available_tools": 5,
            "tool_count": 5,
            "server_capabilities": {
                "tools": {
                    "listChanged": True
                }
            },
            "server_info": {
                "name": "word-addin-mcp-server",
                "version": "1.0.0"
            }
        }
        
        return status
        
    except Exception as e:
        logger.error("Failed to get MCP status", error=str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve MCP status"
        )


# Tool execution methods moved to tool_execution_service


# Text processor execution moved to tool_execution_service


# Document analyzer execution moved to tool_execution_service


# Web content fetcher and data formatter execution moved to tool_execution_service

# LangChain Chat Endpoints

@router.post("/chat")
async def chat_with_agent(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Chat with the LangChain agent using MCP tools.
    
    Args:
        request: Dict containing message and optional session_id
        
    Returns:
        Dict containing agent response and metadata
    """
    try:
        message = request.get("message")
        session_id = request.get("session_id")
        
        if not message:
            raise HTTPException(
                status_code=400,
                detail="Message is required"
            )
        
        # Process message with LangChain agent
        response = await langchain_service.process_message(message, session_id)
        
        logger.info("Chat message processed successfully", 
                   session_id=session_id, 
                   message_length=len(message))
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to process chat message", 
                    error=str(e), 
                    session_id=request.get("session_id"))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process chat message: {str(e)}"
        )


@router.post("/agent/intent")
async def detect_user_intent(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Detect user intent and determine routing using intelligent agent.
    
    Args:
        request: Dict containing message, conversation_history, document_content, available_tools
        
    Returns:
        Dict containing intent detection results and routing decision
    """
    try:
        from app.services.agent import AgentService
        
        message = request.get("message")
        conversation_history = request.get("conversation_history", [])
        document_content = request.get("document_content", "")
        available_tools = request.get("available_tools", [])
        
        if not message:
            raise HTTPException(
                status_code=400,
                detail="Message is required"
            )
        
        # Initialize agent service and detect intent
        agent_service = AgentService()
        intent_result = await agent_service.detect_intent_and_route(
            user_input=message,
            conversation_history=conversation_history,
            document_content=document_content,
            available_tools=available_tools
        )
        
        intent_type, routing_decision, parameters, reasoning = intent_result
        
        logger.info("User intent detected successfully", 
                   message_length=len(message),
                   intent_type=intent_type.value,
                   routing_decision=routing_decision.value)
        
        return {
            "status": "success",
            "intent_type": intent_type.value,
            "routing_decision": routing_decision.value,
            "parameters": parameters,
            "reasoning": reasoning,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to detect user intent", 
                    error=str(e), 
                    message=request.get("message"))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to detect user intent: {str(e)}"
        )


@router.get("/chat/history")
async def get_chat_history(session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Get conversation history for a session.
    
    Args:
        session_id: Optional session ID to filter history
        
    Returns:
        Dict containing conversation history
    """
    try:
        history = await langchain_service.get_conversation_history(session_id)
        
        return {
            "session_id": session_id,
            "history": history,
            "total_messages": len(history),
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error("Failed to get chat history", 
                    error=str(e), 
                    session_id=session_id)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get chat history: {str(e)}"
        )


@router.delete("/chat/history")
async def clear_chat_history(session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Clear conversation history for a session.
    
    Args:
        session_id: Optional session ID to clear history for
        
    Returns:
        Dict confirming history cleared
    """
    try:
        await langchain_service.clear_conversation_memory(session_id)
        
        return {
            "message": "Chat history cleared successfully",
            "session_id": session_id,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error("Failed to clear chat history", 
                    error=str(e), 
                    session_id=session_id)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear chat history: {str(e)}"
        )


@router.get("/agent/status")
async def get_agent_status() -> Dict[str, Any]:
    """
    Get the current status of the LangChain agent.
    
    Returns:
        Dict containing agent status information
    """
    try:
        status = await langchain_service.get_agent_status()
        
        return {
            **status,
            "timestamp": time.time(),
            "mcp_integration": True
        }
        
    except Exception as e:
        logger.error("Failed to get agent status", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get agent status: {str(e)}"
        )


@router.post("/agent/initialize")
async def initialize_agent() -> Dict[str, Any]:
    """
    Initialize or reinitialize the LangChain agent.
    
    Returns:
        Dict confirming agent initialization
    """
    try:
        await langchain_service.initialize()
        
        return {
            "message": "LangChain agent initialized successfully",
            "status": "initialized",
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error("Failed to initialize agent", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize agent: {str(e)}"
        )


# Memory Management Endpoints

@router.post("/memory/conversation")
async def add_conversation_memory(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add conversation memory for a session.
    
    Args:
        request: Dict containing session_id, user_id, content, and optional metadata
        
    Returns:
        Dict containing memory ID and status
    """
    try:
        session_id = request.get("session_id")
        user_id = request.get("user_id")
        content = request.get("content")
        metadata = request.get("metadata")
        
        if not session_id or not content:
            raise HTTPException(
                status_code=400,
                detail="session_id and content are required"
            )
        
        memory_id = await memory_service.add_conversation_memory(
            session_id, user_id, content, metadata
        )
        
        return {
            "memory_id": memory_id,
            "session_id": session_id,
            "status": "added",
            "timestamp": time.time()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to add conversation memory", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add conversation memory: {str(e)}"
        )


@router.post("/memory/document")
async def add_document_memory(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add document context memory.
    
    Args:
        request: Dict containing session_id, user_id, content, and document_metadata
        
    Returns:
        Dict containing memory ID and status
    """
    try:
        session_id = request.get("session_id")
        user_id = request.get("user_id")
        content = request.get("content")
        document_metadata = request.get("document_metadata", {})
        
        if not session_id or not content:
            raise HTTPException(
                status_code=400,
                detail="session_id and content are required"
            )
        
        memory_id = await memory_service.add_document_memory(
            session_id, user_id, content, document_metadata
        )
        
        return {
            "memory_id": memory_id,
            "session_id": session_id,
            "status": "added",
            "timestamp": time.time()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to add document memory", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add document memory: {str(e)}"
        )


@router.post("/memory/tool-result")
async def add_tool_result_memory(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add tool result memory.
    
    Args:
        request: Dict containing session_id, user_id, tool_name, result, and optional metadata
        
    Returns:
        Dict containing memory ID and status
    """
    try:
        session_id = request.get("session_id")
        user_id = request.get("user_id")
        tool_name = request.get("tool_name")
        result = request.get("result")
        metadata = request.get("metadata")
        
        if not session_id or not tool_name or result is None:
            raise HTTPException(
                status_code=400,
                detail="session_id, tool_name, and result are required"
            )
        
        memory_id = await memory_service.add_tool_result_memory(
            session_id, user_id, tool_name, result, metadata
        )
        
        return {
            "memory_id": memory_id,
            "session_id": session_id,
            "tool_name": tool_name,
            "status": "added",
            "timestamp": time.time()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to add tool result memory", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add tool result memory: {str(e)}"
        )


@router.get("/memory/search")
async def search_memory(query: str, session_id: Optional[str] = None, 
                       user_id: Optional[str] = None, content_type: Optional[str] = None,
                       limit: int = 10) -> Dict[str, Any]:
    """
    Search memory using various criteria.
    
    Args:
        query: Search query string
        session_id: Optional session ID to filter results
        user_id: Optional user ID to filter results
        content_type: Optional content type to filter results
        limit: Maximum number of results to return
        
    Returns:
        Dict containing search results and metadata
    """
    try:
        if not query:
            raise HTTPException(
                status_code=400,
                detail="query is required"
            )
        
        search_results = await memory_service.search_memory(
            query, session_id, user_id, content_type, limit
        )
        
        # Convert search results to serializable format
        results = []
        for result in search_results:
            results.append({
                "memory_id": result.memory_item.id,
                "session_id": result.memory_item.session_id,
                "content": result.memory_item.content,
                "content_type": result.memory_item.content_type,
                "relevance_score": result.relevance_score,
                "matched_terms": result.matched_terms,
                "context_snippet": result.context_snippet,
                "created_at": result.memory_item.created_at.isoformat(),
                "importance_score": result.memory_item.importance_score,
                "tags": result.memory_item.tags
            })
        
        return {
            "query": query,
            "results": results,
            "total_count": len(results),
            "filters": {
                "session_id": session_id,
                "user_id": user_id,
                "content_type": content_type
            },
            "timestamp": time.time()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to search memory", query=query, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search memory: {str(e)}"
        )


@router.get("/memory/session/{session_id}")
async def get_session_memory(session_id: str, limit: int = 50) -> Dict[str, Any]:
    """
    Get all memory items for a session.
    
    Args:
        session_id: Session ID to get memory for
        limit: Maximum number of memories to return
        
    Returns:
        Dict containing session memories and metadata
    """
    try:
        memories = await memory_service.get_session_memory(session_id, limit)
        
        # Convert to serializable format
        memory_list = []
        for memory in memories:
            memory_list.append({
                "id": memory.id,
                "session_id": memory.session_id,
                "user_id": memory.user_id,
                "content": memory.content,
                "content_type": memory.content_type,
                "metadata": memory.metadata,
                "created_at": memory.created_at.isoformat(),
                "last_accessed": memory.last_accessed.isoformat(),
                "access_count": memory.access_count,
                "importance_score": memory.importance_score,
                "tags": memory.tags
            })
        
        return {
            "session_id": session_id,
            "memories": memory_list,
            "total_count": len(memory_list),
            "limit": limit,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error("Failed to get session memory", 
                    session_id=session_id, 
                    error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get session memory: {str(e)}"
        )


@router.get("/memory/user/{user_id}")
async def get_user_memory(user_id: str, limit: int = 100) -> Dict[str, Any]:
    """
    Get all memory items for a user.
    
    Args:
        user_id: User ID to get memory for
        limit: Maximum number of memories to return
        
    Returns:
        Dict containing user memories and metadata
    """
    try:
        memories = await memory_service.get_user_memory(user_id, limit)
        
        # Convert to serializable format
        memory_list = []
        for memory in memories:
            memory_list.append({
                "id": memory.id,
                "session_id": memory.session_id,
                "user_id": memory.user_id,
                "content": memory.content,
                "content_type": memory.content_type,
                "metadata": memory.metadata,
                "created_at": memory.created_at.isoformat(),
                "last_accessed": memory.last_accessed.isoformat(),
                "access_count": memory.access_count,
                "importance_score": memory.importance_score,
                "tags": memory.tags
            })
        
        return {
            "user_id": user_id,
            "memories": memory_list,
            "total_count": len(memory_list),
            "limit": limit,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error("Failed to get user memory", 
                    user_id=user_id, 
                    error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get user memory: {str(e)}"
        )


@router.delete("/memory/{memory_id}")
async def delete_memory(memory_id: str) -> Dict[str, Any]:
    """
    Delete a memory item.
    
    Args:
        memory_id: ID of the memory to delete
        
    Returns:
        Dict confirming memory deletion
    """
    try:
        success = await memory_service.delete_memory(memory_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Memory not found"
            )
        
        return {
            "memory_id": memory_id,
            "status": "deleted",
            "timestamp": time.time()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete memory", 
                    memory_id=memory_id, 
                    error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete memory: {str(e)}"
        )


@router.delete("/memory/session/{session_id}")
async def clear_session_memory(session_id: str) -> Dict[str, Any]:
    """
    Clear all memory for a session.
    
    Args:
        session_id: Session ID to clear memory for
        
    Returns:
        Dict confirming memory clearing
    """
    try:
        deleted_count = await memory_service.clear_session_memory(session_id)
        
        return {
            "session_id": session_id,
            "deleted_count": deleted_count,
            "status": "cleared",
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error("Failed to clear session memory", 
                    session_id=session_id, 
                    error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear session memory: {str(e)}"
        )


@router.get("/memory/statistics")
async def get_memory_statistics() -> Dict[str, Any]:
    """
    Get memory system statistics.
    
    Returns:
        Dict containing memory system statistics
    """
    try:
        stats = await memory_service.get_memory_statistics()
        return stats
        
    except Exception as e:
        logger.error("Failed to get memory statistics", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get memory statistics: {str(e)}"
        )


# Data Formatter Helper Methods

def _detect_data_type(data: str) -> str:
    """Auto-detect the type of input data."""
    data = data.strip()
    
    # Check if it's JSON
    if data.startswith('{') and data.endswith('}') or data.startswith('[') and data.endswith(']'):
        try:
            import json
            json.loads(data)
            return "json"
        except:
            pass
    
    # Check if it's CSV-like
    if ',' in data and '\n' in data:
        lines = data.split('\n')
        if len(lines) > 1 and all(',' in line for line in lines[:2]):
            return "csv"
    
    # Check if it's a list (comma-separated or newline-separated)
    if ',' in data or '\n' in data:
        import re
        items = re.split(r'[,;\n]', data)
        if len(items) > 1 and all(item.strip() for item in items):
            return "list"
    
    # Default to text
    return "text"

def _parse_data(data: str, data_type: str):
    """Parse data based on detected type."""
    try:
        if data_type == "json":
            import json
            return json.loads(data)
        elif data_type == "csv":
            return self._parse_csv(data)
        elif data_type == "list":
            import re
            return self._parse_list(data)
        else:
            return data
    except Exception as e:
        logger.warning(f"Failed to parse data as {data_type}: {str(e)}")
        return data

def _parse_csv(data: str):
    """Parse CSV data into list of dictionaries."""
    try:
        import csv
        from io import StringIO
        csv_file = StringIO(data)
        reader = csv.DictReader(csv_file)
        return [dict(row) for row in reader]
    except Exception as e:
        logger.warning(f"CSV parsing failed: {str(e)}")
        # Fallback: split by lines and commas
        lines = data.strip().split('\n')
        if lines:
            headers = [h.strip() for h in lines[0].split(',')]
            result = []
            for line in lines[1:]:
                values = [v.strip() for v in line.split(',')]
                if len(values) == len(headers):
                    result.append(dict(zip(headers, values)))
            return result
        return []

def _parse_list(data: str):
    """Parse list data into list of strings."""
    import re
    items = re.split(r'[,;\n]', data)
    return [item.strip() for item in items if item.strip()]

def _format_as_json(data, indent: int = 2, include_metadata: bool = True) -> str:
    """Format data as JSON with proper indentation."""
    try:
        import json
        if include_metadata:
            formatted_data = {
                "data": data,
                "format": "json",
                "metadata": {
                    "indentation": indent,
                    "formatted_at": "now"
                }
            }
        else:
            formatted_data = data
        
        return json.dumps(formatted_data, indent=indent, ensure_ascii=False)
    except Exception as e:
        logger.error(f"JSON formatting failed: {str(e)}")
        return f'{{"error": "JSON formatting failed", "original_data": "{str(data)[:100]}..."}}'

def _format_as_csv(data, include_metadata: bool = True) -> str:
    """Format data as CSV."""
    try:
        import csv
        from io import StringIO
        if isinstance(data, list) and data and isinstance(data[0], dict):
            # List of dictionaries
            if not data:
                return ""
            
            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
            csv_content = output.getvalue()
            output.close()
            
            if include_metadata:
                return f"# CSV Export\n# Generated at: now\n# Records: {len(data)}\n\n{csv_content}"
            return csv_content
        else:
            # Single value or simple list
            if isinstance(data, list):
                csv_content = '\n'.join(f'"{item}"' for item in data)
            else:
                csv_content = f'"{data}"'
            
            if include_metadata:
                return f"# CSV Export\n# Generated at: now\n# Type: {type(data).__name__}\n\n{csv_content}"
            return csv_content
    except Exception as e:
        logger.error(f"CSV formatting failed: {str(e)}")
        return f"Error: CSV formatting failed - {str(e)}"

def _format_as_xml(data, include_metadata: bool = True) -> str:
    """Format data as XML."""
    try:
        if isinstance(data, dict):
            xml_content = self._dict_to_xml(data, "data")
        elif isinstance(data, list):
            xml_content = f"<data>\n" + '\n'.join(f"  <item>{item}</item>" for item in data) + "\n</data>"
        else:
            xml_content = f"<data>{data}</data>"
        
        if include_metadata:
            return f"""<?xml version="1.0" encoding="UTF-8"?>
<!-- XML Export -->
<!-- Generated at: now -->
<!-- Type: {type(data).__name__} -->
{xml_content}"""
        return f"""<?xml version="1.0" encoding="UTF-8"?>
{xml_content}"""
    except Exception as e:
        logger.error(f"XML formatting failed: {str(e)}")
        return f"<error>XML formatting failed - {str(e)}</error>"

def _dict_to_xml(data: dict, root_name: str) -> str:
    """Convert dictionary to XML string."""
    xml_parts = [f"<{root_name}>"]
    for key, value in data.items():
        if isinstance(value, dict):
            xml_parts.append(self._dict_to_xml(value, key))
        elif isinstance(value, list):
            xml_parts.append(f"<{key}>")
            for item in value:
                if isinstance(item, dict):
                    xml_parts.append(self._dict_to_xml(item, "item"))
                else:
                    xml_parts.append(f"<item>{item}</item>")
            xml_parts.append(f"</{key}>")
        else:
            xml_parts.append(f"<{key}>{value}</{key}>")
    xml_parts.append(f"</{root_name}>")
    return '\n'.join(xml_parts)

def _format_as_yaml(data, include_metadata: bool = True) -> str:
    """Format data as YAML."""
    try:
        if include_metadata:
            yaml_content = f"""# YAML Export
# Generated at: now
# Type: {type(data).__name__}

data: {data}"""
        else:
            yaml_content = str(data)
        
        return yaml_content
    except Exception as e:
        logger.error(f"YAML formatting failed: {str(e)}")
        return f"# Error: YAML formatting failed - {str(e)}"

def _format_as_table(data, include_metadata: bool = True) -> str:
    """Format data as a formatted table."""
    try:
        if isinstance(data, list) and data and isinstance(data[0], dict):
            # List of dictionaries - create table
            if not data:
                return "No data to display"
            
            headers = list(data[0].keys())
            table_lines = []
            
            if include_metadata:
                table_lines.append(f"# Table Export - Generated at: now")
                table_lines.append(f"# Records: {len(data)}")
                table_lines.append("")
            
            # Header
            header_line = "| " + " | ".join(headers) + " |"
            separator_line = "| " + " | ".join("-" * len(h) for h in headers) + " |"
            table_lines.extend([header_line, separator_line])
            
            # Data rows
            for row in data:
                row_line = "| " + " | ".join(str(row.get(h, "")) for h in headers) + " |"
                table_lines.append(row_line)
            
            return '\n'.join(table_lines)
        else:
            # Single value or simple list
            if isinstance(data, list):
                table_content = '\n'.join(f"- {item}" for item in data)
            else:
                table_content = str(data)
            
            if include_metadata:
                return f"# Table Export\n# Generated at: now\n# Type: {type(data).__name__}\n\n{table_content}"
            return table_content
    except Exception as e:
        logger.error(f"Table formatting failed: {str(e)}")
        return f"Error: Table formatting failed - {str(e)}"

# Web Content Fetcher Helper Functions - REMOVED (now handled by the tool directly)

# Simple data formatter fallback moved to tool_execution_service
