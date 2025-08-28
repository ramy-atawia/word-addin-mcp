"""
LangChain Agent Service for Word Add-in MCP Project.

This service integrates LangChain agents with Azure OpenAI and MCP tools,
providing intelligent conversation and tool execution capabilities.
"""

import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import structlog
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import AzureChatOpenAI
from langchain.tools import BaseTool
from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema.runnable import RunnablePassthrough
from langchain.tools.render import format_tool_to_openai_tool

from backend.app.core.config import settings
from backend.app.services.mcp_service import MCPService
from backend.app.core.mcp_tool_interface import BaseMCPTool, ToolExecutionResult

logger = structlog.get_logger()


class MCPToolWrapper(BaseTool):
    """Wrapper for MCP tools to make them compatible with LangChain."""
    
    def __init__(self, mcp_tool: BaseMCPTool, mcp_service: MCPService):
        super().__init__(
            name=mcp_tool.metadata.name,
            description=mcp_tool.metadata.description,
            return_direct=False
        )
        self.mcp_tool = mcp_tool
        self.mcp_service = mcp_service
    
    async def _arun(self, **kwargs) -> str:
        """Async execution of the MCP tool."""
        try:
            result = await self.mcp_tool.execute(kwargs)
            return str(result.content)
        except Exception as e:
            logger.error("Error executing MCP tool", 
                        tool_name=self.mcp_tool.metadata.name, 
                        error=str(e))
            return f"Error executing tool: {str(e)}"
    
    def _run(self, **kwargs) -> str:
        """Sync execution of the MCP tool (not used in async context)."""
        raise NotImplementedError("Sync execution not supported")


class LangChainService:
    """Service for managing LangChain agents and conversations."""
    
    def __init__(self):
        self.initialized = False
        self.llm: Optional[AzureChatOpenAI] = None
        self.agent_executor: Optional[AgentExecutor] = None
        self.mcp_service: Optional[MCPService] = None
        self.conversation_memory: Optional[ConversationBufferMemory] = None
        self.available_tools: List[MCPToolWrapper] = []
        
    async def initialize(self):
        """Initialize the LangChain service with Azure OpenAI and MCP tools."""
        if self.initialized:
            return
        
        try:
            # Initialize MCP service
            self.mcp_service = MCPService()
            await self.mcp_service.initialize()
            
            # Initialize Azure OpenAI
            self.llm = AzureChatOpenAI(
                azure_deployment=settings.azure_openai_deployment_name,
                openai_api_version=settings.azure_openai_api_version,
                azure_endpoint=settings.azure_openai_endpoint,
                api_key=settings.azure_openai_api_key,
                temperature=0.7,
                max_tokens=2000,
                streaming=True
            )
            
            # Initialize conversation memory
            self.conversation_memory = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True,
                output_key="output"
            )
            
            # Load and wrap MCP tools
            await self._load_mcp_tools()
            
            # Create the agent
            await self._create_agent()
            
            self.initialized = True
            logger.info("LangChain service initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize LangChain service", error=str(e))
            raise
    
    async def _load_mcp_tools(self):
        """Load MCP tools and wrap them for LangChain compatibility."""
        try:
            # Get available tools from MCP service
            mcp_tools = await self.mcp_service.list_available_tools()
            
            # Create tool wrappers
            self.available_tools = []
            for tool_info in mcp_tools:
                # For now, we'll create a basic wrapper
                # In a full implementation, you'd instantiate the actual tool classes
                wrapper = MCPToolWrapper(
                    mcp_tool=self._create_tool_instance(tool_info),
                    mcp_service=self.mcp_service
                )
                self.available_tools.append(wrapper)
            
            logger.info("Loaded MCP tools for LangChain", 
                       tool_count=len(self.available_tools))
            
        except Exception as e:
            logger.error("Failed to load MCP tools", error=str(e))
            self.available_tools = []
    
    def _create_tool_instance(self, tool_info: Dict[str, Any]) -> BaseMCPTool:
        """Create a tool instance from tool info (placeholder implementation)."""
        # This is a placeholder - in a real implementation, you'd create
        # actual tool instances based on the tool_info
        from backend.app.tools.file_reader import FileReaderTool
        
        # Return a default tool for now
        return FileReaderTool()
    
    async def _create_agent(self):
        """Create the LangChain agent with tools and memory."""
        try:
            # Convert tools to OpenAI format
            openai_tools = [format_tool_to_openai_tool(tool) for tool in self.available_tools]
            
            # Create the prompt template
            prompt = ChatPromptTemplate.from_messages([
                ("system", self._get_system_prompt()),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ])
            
            # Create the agent
            agent = create_openai_tools_agent(
                llm=self.llm,
                tools=self.available_tools,
                prompt=prompt
            )
            
            # Create the agent executor
            self.agent_executor = AgentExecutor(
                agent=agent,
                tools=self.available_tools,
                memory=self.conversation_memory,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=5
            )
            
            logger.info("LangChain agent created successfully")
            
        except Exception as e:
            logger.error("Failed to create LangChain agent", error=str(e))
            raise
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the agent."""
        return """You are an intelligent assistant integrated with Word Add-in MCP tools. 
Your role is to help users with document analysis, text processing, and content management.

Available tools:
- File Reader: Read and analyze document files
- Text Processor: Process and transform text content
- Document Analyzer: Analyze document structure and content
- Web Content Fetcher: Fetch content from web sources
- Data Formatter: Format and structure data

Guidelines:
1. Always use the appropriate tools when users request specific operations
2. Provide clear explanations of what you're doing
3. Be helpful and professional
4. If you encounter errors, explain what went wrong and suggest alternatives
5. Keep responses concise but informative

Remember: You have access to powerful MCP tools that can help with various document and text processing tasks."""
    
    async def process_message(self, message: str, session_id: str = None) -> Dict[str, Any]:
        """Process a user message and return a response."""
        if not self.initialized:
            await self.initialize()
        
        try:
            # Add user message to memory
            self.conversation_memory.chat_memory.add_user_message(message)
            
            # Process with agent
            result = await self.agent_executor.ainvoke({
                "input": message,
                "chat_history": self.conversation_memory.chat_memory.messages
            })
            
            # Add AI response to memory
            self.conversation_memory.chat_memory.add_ai_message(result["output"])
            
            # Prepare response
            response = {
                "response": result["output"],
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "tools_used": result.get("intermediate_steps", []),
                "memory_size": len(self.conversation_memory.chat_memory.messages)
            }
            
            logger.info("Message processed successfully", 
                       session_id=session_id, 
                       response_length=len(result["output"]))
            
            return response
            
        except Exception as e:
            logger.error("Failed to process message", 
                        session_id=session_id, 
                        error=str(e))
            
            error_response = {
                "response": f"I encountered an error while processing your request: {str(e)}",
                "session_id": session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "tools_used": []
            }
            
            return error_response
    
    async def get_conversation_history(self, session_id: str = None) -> List[Dict[str, Any]]:
        """Get conversation history for a session."""
        if not self.initialized:
            await self.initialize()
        
        try:
            messages = self.conversation_memory.chat_memory.messages
            history = []
            
            for msg in messages:
                if isinstance(msg, HumanMessage):
                    history.append({
                        "type": "user",
                        "content": msg.content,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                elif isinstance(msg, AIMessage):
                    history.append({
                        "type": "assistant",
                        "content": msg.content,
                        "timestamp": datetime.utcnow().isoformat()
                    })
            
            return history
            
        except Exception as e:
            logger.error("Failed to get conversation history", 
                        session_id=session_id, 
                        error=str(e))
            return []
    
    async def clear_conversation_memory(self, session_id: str = None):
        """Clear conversation memory for a session."""
        if not self.initialized:
            return
        
        try:
            self.conversation_memory.clear()
            logger.info("Conversation memory cleared", session_id=session_id)
            
        except Exception as e:
            logger.error("Failed to clear conversation memory", 
                        session_id=session_id, 
                        error=str(e))
    
    async def get_agent_status(self) -> Dict[str, Any]:
        """Get the current status of the LangChain agent."""
        if not self.initialized:
            return {"status": "not_initialized"}
        
        try:
            return {
                "status": "initialized",
                "llm_available": self.llm is not None,
                "agent_available": self.agent_executor is not None,
                "tools_available": len(self.available_tools),
                "memory_size": len(self.conversation_memory.chat_memory.messages) if self.conversation_memory else 0,
                "azure_openai_configured": all([
                    settings.azure_openai_api_key,
                    settings.azure_openai_endpoint,
                    settings.azure_openai_deployment_name
                ])
            }
            
        except Exception as e:
            logger.error("Failed to get agent status", error=str(e))
            return {"status": "error", "error": str(e)}


# Global instance
langchain_service = LangChainService()
