"""
Intelligent Agent Service for Word Add-in MCP Project.

This service uses Azure OpenAI LLM for:
- Intent detection from user input
- Conversation context understanding
- Routing decisions to appropriate tools
- Dynamic response generation
- Tool execution orchestration
- Conversation memory management
"""

import structlog
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from enum import Enum
import json
import re

logger = structlog.get_logger()


class IntentType(Enum):
    """Types of user intents."""
    GREETING = "greeting"
    HELP = "help"
    CONVERSATION = "conversation"
    DOCUMENT_ANALYSIS = "document_analysis"
    TEXT_PROCESSING = "text_processing"
    WEB_CONTENT = "web_content"
    FILE_OPERATIONS = "file_operations"
    SEARCH_REQUEST = "search_request"
    SEARCH_INFORMATION = "search_information"
    WEB_SEARCH = "web_search"
    TEXT_ANALYSIS = "text_analysis"
    DOCUMENT_PROCESSING = "document_processing"
    FILE_READING = "file_reading"
    UNKNOWN = "unknown"





class ConversationMemory:
    """Simple conversation memory management."""
    
    def __init__(self):
        self.messages = []
        self.max_messages = 50  # Keep last 50 messages
    
    def add_message(self, role: str, content: str):
        """Add a message to conversation history."""
        message = {
            "role": role,
            "content": content,
            "timestamp": time.time()
        }
        self.messages.append(message)
        
        # Keep only recent messages
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
    
    def get_recent_messages(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversation messages."""
        return self.messages[-count:] if self.messages else []
    
    def get_conversation_history_string(self) -> str:
        """Get conversation history as formatted string."""
        if not self.messages:
            return "No conversation history"
        
        history_lines = []
        for msg in self.messages[-10:]:  # Last 10 messages
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')[:100]  # Truncate long messages
            history_lines.append(f"{role}: {content}")
        
        return "\n".join(history_lines)
    
    def clear(self):
        """Clear conversation memory."""
        self.messages.clear()
    
    def get_memory_size(self) -> int:
        """Get current memory size."""
        return len(self.messages)


class AgentService:
    """Intelligent agent service for intent detection, routing, and tool execution."""
    
    def __init__(self):
        """Initialize the agent service."""
        self.llm_client = None
        self.conversation_memory = ConversationMemory()
        self.mcp_orchestrator = None  # Add MCP orchestrator
        # LLM client will be initialized lazily when needed
        # MCP orchestrator will be initialized lazily when needed
    
    def _initialize_llm_client(self):
        """Initialize the LLM client."""
        try:
            # Use relative imports for consistency
            try:
                from .llm_client import get_llm_client
                from ..core.config import is_azure_openai_configured
                logger.info("Using relative import path")
            except ImportError:
                logger.error("Failed to import LLM client")
                self.llm_client = None
                return
            
            if is_azure_openai_configured():
                self.llm_client = get_llm_client()
                logger.info("Agent service initialized with Azure OpenAI LLM")
            else:
                logger.warning("Azure OpenAI not configured - agent will use fallback logic")
                self.llm_client = None
        except Exception as e:
            logger.error(f"Failed to initialize LLM client: {str(e)}")
            self.llm_client = None
    
    def _get_llm_client(self):
        """Get LLM client with lazy initialization."""
        if self.llm_client is None:
            try:
                from .llm_client import get_llm_client
                from ..core.config import is_azure_openai_configured
                logger.info("Initializing LLM client...")
            except ImportError:
                logger.error("Failed to import LLM client")
                self.llm_client = None
                return None
            
            if is_azure_openai_configured():
                self.llm_client = get_llm_client()
                logger.info("Agent service initialized with Azure OpenAI LLM")
            else:
                logger.warning("Azure OpenAI not configured - agent will use fallback logic")
                self.llm_client = None
        return self.llm_client
    
    def _get_mcp_orchestrator(self):
        """Get MCP orchestrator with lazy initialization."""
        if self.mcp_orchestrator is None:
            try:
                from .mcp.orchestrator import get_initialized_mcp_orchestrator
                self.mcp_orchestrator = get_initialized_mcp_orchestrator()
                logger.info("Agent service initialized with MCP orchestrator")
            except RuntimeError as e:
                logger.error(f"MCP Orchestrator not initialized: {str(e)}")
                raise RuntimeError("AgentService requires initialized MCP Orchestrator")
            except Exception as e:
                logger.error(f"Failed to initialize MCP orchestrator: {str(e)}")
                raise RuntimeError(f"Failed to initialize MCP orchestrator: {str(e)}")
        return self.mcp_orchestrator
    
    async def process_user_message(
        self,
        user_message: str,
        document_content: Optional[str] = None,
        available_tools: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Main method to process user message end-to-end.
        
        Args:
            user_message: Current user message
            document_content: Current Word document content (if any)
            available_tools: List of available MCP tools
            
        Returns:
            Complete response with intent, routing, execution result, and metrics
        """
        start_time = time.time()
        
        try:
            # Add user message to memory
            self.conversation_memory.add_message("user", user_message)
            
            # Get conversation history
            conversation_history = self.conversation_memory.get_recent_messages()
            
            # Step 1: Detect intent and get tool name and parameters from LLM
            action_result = await self.detect_intent_and_route(
                user_input=user_message,
                conversation_history=conversation_history,
                document_content=document_content,
                available_tools=available_tools
            )

            intent_type, tool_name, parameters, reasoning = action_result

            final_response = ""
            execution_result = {}
            tools_used = ["llm_chat"] # Default to LLM chat

            if action_result[0] == IntentType.CONVERSATION: # IntentType.CONVERSATION
                final_response = reasoning  # In this case, reasoning is the conversational response
                logger.info(f"Agent decided on conversational response: {final_response[:100]}...")

            elif action_result[0] in [IntentType.WEB_SEARCH, IntentType.TEXT_ANALYSIS, IntentType.DOCUMENT_ANALYSIS, IntentType.FILE_READING, IntentType.UNKNOWN]:
                # This is a tool call, execute the tool
                try:
                    orchestrator = self._get_mcp_orchestrator()
                    if not orchestrator:
                        raise RuntimeError("MCP Orchestrator not initialized.")

                    logger.info(f"Agent decided to call tool: {tool_name} with parameters: {parameters}")
                    execution_result = await orchestrator.execute_tool(tool_name, parameters)
                    final_response = await self._format_tool_response(execution_result, user_message)
                    tools_used.append(tool_name)
                    logger.info(f"Tool {tool_name} executed successfully. Response: {final_response[:100]}...")

                except Exception as e:
                    logger.error(f"Tool execution failed for {tool_name}: {str(e)}")
                    final_response = f"I tried to use the {tool_name} tool, but it encountered an error: {str(e)}. Please try again."
                    tools_used.append(f"{tool_name}_failed")
                    intent_type = IntentType.UNKNOWN # Mark as unknown if tool failed
            else:
                final_response = "I'm having trouble processing your request. Please try again or ask me to help with a specific task."
                intent_type = IntentType.UNKNOWN
                logger.warning(f"Unknown action result from LLM: {action_result}. Defaulting to conversational fallback.")

            # Add AI response to memory
            self.conversation_memory.add_message("assistant", final_response)
            
            execution_time = time.time() - start_time
            
            # Prepare comprehensive response
            response = {
                "response": final_response,
                "intent_type": intent_type.value,
                "tool_name": tool_name,
                "tools_used": tools_used,
                "execution_time": execution_time,
                "success": True,
                "reasoning": reasoning,
                "conversation_memory_size": self.conversation_memory.get_memory_size()
            }
            
            logger.info(f"Message processed successfully - intent: {intent_type.value}, tool_name: {tool_name}, execution_time: {execution_time}")
            
            return response
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Failed to process user message: {str(e)}")
            
            # Add error response to memory
            error_response = f"I encountered an error while processing your request: {str(e)}"
            self.conversation_memory.add_message("assistant", error_response)
            
            return {
                "response": error_response,
                "intent_type": "unknown",
                "tool_name": None,
                "tools_used": [],
                "execution_time": execution_time,
                "success": False,
                "error": str(e),
                "conversation_memory_size": self.conversation_memory.get_memory_size()
            }
    
    async def detect_intent_and_route(
        self,
        user_input: str,
        conversation_history: List[Dict[str, Any]],
        document_content: Optional[str] = None,
        available_tools: List[Dict[str, Any]] = None
    ) -> Tuple[IntentType, str, Dict[str, Any], str]:
        """
        Detect user intent and determine routing using LLM.
        
        Args:
            user_input: Current user message
            conversation_history: Previous conversation messages
            document_content: Current Word document content (if any)
            available_tools: List of available MCP tools
            
        Returns:
            Tuple of (intent_type, tool_name, parameters, reasoning)
        """
        try:
            llm_client = self._get_llm_client()
            logger.info(f"Agent service: LLM client available: {llm_client is not None}")
            if not llm_client:
                logger.warning("Using fallback intent detection - no LLM client")
                return await self._fallback_intent_detection(user_input)
            
            # Prepare context for LLM
            context = self._prepare_context(user_input, conversation_history, document_content, available_tools)
            logger.info(f"Prepared context: {context[:200]}...")
            
            # Use LLM for intent detection and routing
            result = await self._llm_intent_detection(context, llm_client)
            
            return result
            
        except Exception as e:
            logger.error(f"Intent detection failed: {str(e)}")
            return await self._fallback_intent_detection(user_input)
    
    def _map_tool_to_intent_type(self, tool_name: str) -> IntentType:
        """Helper to map tool names to a general IntentType for classification/logging."""
        if "search" in tool_name:
            return IntentType.WEB_SEARCH
        elif "text_analysis" in tool_name:
            return IntentType.TEXT_ANALYSIS
        elif "document_analysis" in tool_name:
            return IntentType.DOCUMENT_ANALYSIS
        elif "file_reader" in tool_name:
            return IntentType.FILE_READING
        else:
            return IntentType.UNKNOWN

    def _prepare_context(self,
        user_input: str,
        conversation_history: List[Dict[str, Any]],
        document_content: Optional[str] = None,
        available_tools: List[Dict[str, Any]] = None
    ) -> str:
        """Prepare context information for LLM analysis, including full tool schemas."""
        context_parts = []

        context_parts.append(f"User Input: {user_input}")

        if conversation_history:
            recent_history = conversation_history[-5:]  # Last 5 messages
            history_text = "\n".join([
                f"{msg.get('role', 'user')}: {msg.get('content', '')}"
                for msg in recent_history
            ])
            context_parts.append(f"Recent Conversation:\n{history_text}")

        if document_content:
            doc_preview = document_content[:1000] + "..." if len(document_content) > 1000 else document_content
            context_parts.append(f"Current Document Content:\n\'\'\'\n{{doc_preview}}\n\'\'\'")

        # Crucially, include full tool schemas for the LLM
        if available_tools:
            tool_descriptions = []
            for tool in available_tools:
                # Only include essential fields for LLM to understand
                tool_schema = {
                    "name": tool.get("name"),
                    "description": tool.get("description"),
                    "parameters": tool.get("input_schema")
                }
                tool_descriptions.append(json.dumps(tool_schema, indent=2))
            context_parts.append(f"Tools Available:\n\'\'\'\n{{'\n'.join(tool_descriptions)}}\n\'\'\'")
        else:
            context_parts.append("No tools are currently available.")

        return "\n\n".join(context_parts)

    async def _llm_intent_detection(self, context: str, llm_client) -> Tuple[IntentType, str, Dict[str, Any], str]:
        """Use LLM to detect intent and return actual MCP tool names - pure MCP approach."""

        logger.info("Starting LLM intent detection with pure MCP approach")

        # Dynamically create the system prompt based on available tools
        # The prompt will guide the LLM to output JSON with tool_name and parameters or a conversational_response
        system_prompt = f'''
        You are a highly intelligent agent that can analyze user input, conversation history, and document context to determine the most appropriate action.
        Your primary goal is to decide between calling an available tool or providing a direct conversational response.

        Available tools are described below. Each tool has a `name`, `description`, and `parameters`.
        `parameters` is a JSON schema for the tool's inputs.

        {context}

        Based on the user's intent, respond with a JSON object in one of two formats:

        **Format 1: Tool Call**
        If you determine a tool is necessary, provide the `tool_name` and a `parameters` object matching the tool's JSON schema.
        Example:
        ```json
        {{
            "action": "tool_call",
            "tool_name": "web_search_tool",
            "parameters": {{
                "query": "latest AI developments"
            }}
        }}
        ```

        **Format 2: Conversational Response**
        If no tool is suitable or if a direct answer is possible, provide a `conversational_response`.
        Example:
        ```json
        {{
            "action": "conversational_response",
            "response": "Hello! How can I help you today?"
        }}
        ```

        Ensure your JSON output is valid and directly parsable. Only output the JSON object.
        Do not include any other text or explanation outside the JSON.
        '''

        user_prompt = "Determine the user's intent and provide the appropriate JSON response based on the context."

        try:
            logger.info("Calling LLM client for intent detection")
            raw_llm_response = llm_client.generate_text(
                prompt=user_prompt,
                max_tokens=800,
                temperature=0.0,
                system_message=system_prompt
            )

            logger.info(f"LLM Raw Response: {raw_llm_response}")

            # Extract the actual text content from the LLM's response structure
            if isinstance(raw_llm_response, dict) and "text" in raw_llm_response:
                llm_response_text = raw_llm_response["text"]
            else:
                llm_response_text = str(raw_llm_response)

            # Attempt to extract JSON from markdown code block if present
            json_match = re.search(r'```json\s*\n(?P<json_content>.*?)\n\s*```', llm_response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group("json_content")
            else:
                # If not in markdown, assume the entire text content is JSON
                json_str = llm_response_text

            # Attempt to parse the extracted string as JSON
            try:
                parsed_response = json.loads(json_str)
            except json.JSONDecodeError:
                logger.error(f"Extracted text is not valid JSON: {json_str}")
                return IntentType.UNKNOWN, None, {}, f"LLM returned invalid JSON: {json_str}"

            action = parsed_response.get("action")

            if action == "tool_call":
                tool_name = parsed_response.get("tool_name")
                parameters = parsed_response.get("parameters", {})
                if not tool_name or not isinstance(parameters, dict):
                    logger.warning(f"Invalid tool_call format from LLM: {parsed_response}")
                    return IntentType.UNKNOWN, None, {}, "LLM returned malformed tool call"
                # We don't use IntentType directly for routing anymore, but keeping it for a general classification
                # For now, we'll map tool names to a general intent type if possible, or UNKNOWN
                intent_type = self._map_tool_to_intent_type(tool_name)
                reasoning = f"LLM decided to call tool: {tool_name}"
                return intent_type, tool_name, parameters, reasoning

            elif action == "conversational_response":
                response_text = parsed_response.get("response")
                if not response_text:
                    logger.warning(f"Invalid conversational_response format from LLM: {parsed_response}")
                    return IntentType.UNKNOWN, None, {}, "LLM returned empty conversational response"
                return IntentType.CONVERSATION, None, {}, response_text

            else:
                logger.warning(f"Unknown action type from LLM: {action} - {parsed_response}")
                return IntentType.UNKNOWN, None, {}, f"LLM returned unknown action: {action}"

        except Exception as e:
            logger.error(f"Error in LLM intent detection: {str(e)}")
            return IntentType.UNKNOWN, None, {}, f"LLM processing failed: {str(e)}"
    
    def _parse_llm_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Parse the LLM response to extract intent and routing information."""
        try:
            # Try to extract JSON from the response
            import json
            import re
            
            # Find JSON pattern in the response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                return json.loads(json_str)
            
            # If no JSON found, try to extract key information
            return self._extract_info_from_text(response_text)
            
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {str(e)}")
            return None
    
    def _extract_info_from_text(self, text: str) -> Dict[str, Any]:
        """Extract intent and tool information from text when JSON parsing fails."""
        # Default to conversation when we can't parse the LLM response
        return {
            "intent_type": "conversation",
            "tool_name": None,
            "parameters": {},
            "reasoning": "JSON parsing failed, defaulting to conversational AI",
            "confidence": 0.3
        }
    
    async def _fallback_intent_detection(self, user_input: str) -> Tuple[IntentType, str, Dict[str, Any], str]:
        """Fallback intent detection when LLM is not available."""
        # No pattern matching - default to conversation
        return IntentType.CONVERSATION, None, {}, "Fallback: LLM unavailable, defaulting to conversational AI"
    
    async def _execute_web_search(self, parameters: Dict[str, Any], user_message: str) -> str:
        """Execute web search operation."""
        try:
            # Import web search service
            from app.services.web_search_service import WebSearchService
            
            async with WebSearchService() as web_search:
                # Extract search query from user message or parameters
                search_query = parameters.get('query') or user_message
                
                # Perform search
                results = await web_search.search_google(search_query, max_results=5)
                
                if results:
                    # Format results
                    formatted_results = []
                    for i, result in enumerate(results[:3], 1):
                        title = result.get('title', 'No title')
                        snippet = result.get('snippet', 'No description')
                        formatted_results.append(f"{i}. **{title}**\n   {snippet}")
                    
                    return f"Here's what I found for '{search_query}':\n\n" + "\n\n".join(formatted_results)
                else:
                    return f"I couldn't find any results for '{search_query}'. Please try a different search term."
                    
        except Exception as e:
            logger.error(f"Web search execution failed: {str(e)}")
            return f"I encountered an error while searching: {str(e)}"
    
    async def _execute_text_processing(
        self, 
        parameters: Dict[str, Any], 
        user_message: str, 
        document_content: Optional[str] = None
    ) -> str:
        """Execute text processing operation."""
        try:
            # Import LLM client for text processing
            if not self.llm_client:
                return "Text processing is not available at the moment."
            
            # Determine operation type
            operation = parameters.get('operation', 'analyze')
            text_to_process = document_content or user_message
            
            if operation == 'summarize':
                system_prompt = "You are a text summarization expert. Provide a concise summary of the given text."
            elif operation == 'analyze':
                system_prompt = "You are a text analysis expert. Analyze the given text and provide insights about its content, structure, and key points."
            else:
                system_prompt = "You are a text processing expert. Process the given text according to the user's request."
            
            result = self.llm_client.generate_text(
                prompt=text_to_process,
                max_tokens=300,
                temperature=0.3,
                system_message=system_prompt
            )
            
            if result.get("success"):
                return result["text"]
            else:
                return "I encountered an error while processing the text. Please try again."
                
        except Exception as e:
            logger.error(f"Text processing execution failed: {str(e)}")
            return f"I encountered an error while processing the text: {str(e)}"
    
    async def _execute_document_analysis(self, parameters: Dict[str, Any], document_content: Optional[str] = None) -> str:
        """Execute document analysis operation."""
        if not document_content:
            return "No document content available for analysis. Please open a Word document first."
        
        try:
            # Use LLM for document analysis
            if not self.llm_client:
                return "Document analysis is not available at the moment."
            
            system_prompt = """You are a document analysis expert. Analyze the given document content and provide insights about:
1. Document structure and organization
2. Key topics and themes
3. Writing style and tone
4. Potential improvements or suggestions
5. Summary of main points

Be concise but comprehensive in your analysis."""
            
            result = self.llm_client.generate_text(
                prompt=document_content,
                max_tokens=400,
                temperature=0.3,
                system_message=system_prompt
            )
            
            if result.get("success"):
                return result["text"]
            else:
                return "I encountered an error while analyzing the document. Please try again."
                
        except Exception as e:
            logger.error(f"Document analysis execution failed: {str(e)}")
            return f"I encountered an error while analyzing the document: {str(e)}"
    
    async def _format_tool_response(self, tool_result: Dict[str, Any], user_message: str) -> str:
        """Format tool execution result into a user-friendly response, handling different tool outputs."""
        if not tool_result or tool_result.get("status") == "error":
            return f"The requested operation for '{user_message}' failed or returned no results."

        formatted_output_parts = []
        formatted_output_parts.append(f"Here's what I found for your request '{user_message}':")

        # Handle web_search_tool results specifically
        if tool_result.get("tool_name") == "web_search_tool" and tool_result.get("result"):
            search_data = tool_result["result"]
            if search_data.get("status") == "success" and search_data.get("results"):
                results = search_data["results"]
                if results:
                    for i, item in enumerate(results[:5], 1): # Limit to top 5 results for brevity
                        title = item.get("title", "No Title")
                        url = item.get("url", "No URL")
                        snippet = item.get("snippet", "No Snippet")
                        formatted_output_parts.append(f"{i}. **{title}**\n   URL: {url}\n   Snippet: {snippet}")
                else:
                    formatted_output_parts.append("No specific web search results found.")
            else:
                formatted_output_parts.append("Web search tool returned an empty or unsuccessful result.")

        # Handle generic tool results (e.g., text analysis, document analysis, file reader)
        elif tool_result.get("result"):
            # If the result is a string, use it directly. Otherwise, try to pretty-print JSON.
            result_content = tool_result["result"]
            if isinstance(result_content, str):
                formatted_output_parts.append(result_content)
            elif isinstance(result_content, dict) or isinstance(result_content, list):
                try:
                    formatted_output_parts.append("```json\n" + json.dumps(result_content, indent=2) + "\n```")
                except TypeError:
                    formatted_output_parts.append(f"Raw result: {str(result_content)}")
            else:
                formatted_output_parts.append(f"Raw result: {str(result_content)}")
        else:
            formatted_output_parts.append("The tool executed successfully but provided no detailed output.")

        return "\n\n".join(formatted_output_parts)
    
    async def generate_conversational_response(
        self,
        user_input: str,
        intent_type: IntentType,
        conversation_history: List[Dict[str, Any]],
        document_context: Optional[str] = None
    ) -> str:
        """Generate conversational response using LLM."""
        try:
            if not self.llm_client:
                return self._get_fallback_response(intent_type)
            
            # Create context-aware system prompt
            system_prompt = self._get_system_prompt_for_intent(intent_type, document_context)
            
            # Generate response
            result = self.llm_client.generate_text(
                prompt=user_input,
                max_tokens=200,
                temperature=0.7,
                system_message=system_prompt
            )
            
            if result.get("success"):
                return result["text"]
            else:
                return self._get_fallback_response(intent_type)
                
        except Exception as e:
            logger.error(f"Failed to generate conversational response: {str(e)}")
            return self._get_fallback_response(intent_type)
    
    def _get_system_prompt_for_intent(self, intent_type: IntentType, document_context: Optional[str] = None) -> str:
        """Get appropriate system prompt based on intent type."""
        base_prompt = "You are a helpful AI assistant for document analysis and text processing."
        
        if intent_type == IntentType.GREETING:
            return f"{base_prompt} Respond warmly and naturally to greetings, then briefly explain how you can help with document work."
        elif intent_type == IntentType.HELP:
            return f"{base_prompt} Explain your capabilities in a friendly, helpful way with specific examples of document analysis and text processing."
        elif intent_type == IntentType.CONVERSATION:
            return f"{base_prompt} Respond naturally and conversationally to general questions and social interactions. Be warm, helpful, and guide the conversation toward how you can assist with document work."
        else:
            return f"{base_prompt} Be conversational, friendly, and helpful."
    
    def _get_fallback_response(self, intent_type: IntentType) -> str:
        """Get minimal fallback response when LLM is not available."""
        return "I'm having trouble processing your request. Please try again or ask me to help with a specific task."
    
    # Conversation memory management methods
    def add_message(self, role: str, content: str):
        """Add a message to conversation memory."""
        self.conversation_memory.add_message(role, content)
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get conversation history."""
        return self.conversation_memory.get_recent_messages()
    
    def get_conversation_history_string(self) -> str:
        """Get conversation history as formatted string."""
        return self.conversation_memory.get_conversation_history_string()
    
    def clear_conversation_memory(self):
        """Clear conversation memory."""
        self.conversation_memory.clear()
    
    def get_memory_size(self) -> int:
        """Get current memory size."""
        return self.conversation_memory.get_memory_size()


# Lazy-loaded global instance
_agent_service_instance = None

def get_agent_service():
    """Get the agent service instance, creating it if necessary."""
    global _agent_service_instance
    if _agent_service_instance is None:
        _agent_service_instance = AgentService()
    return _agent_service_instance

# For backward compatibility
agent_service = get_agent_service()
