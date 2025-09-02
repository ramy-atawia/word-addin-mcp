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
    """Generic intent types - no hardcoded tool mapping."""
    CONVERSATION = "conversation"
    TOOL_EXECUTION = "tool_execution"
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
        
        # Intent detection caching
        self._intent_cache = {}
        self._cache_ttl = 60  # 1 minute cache TTL
        
        # Clear cache method for debugging
        self._clear_intent_cache = lambda: self._intent_cache.clear()
        
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
    
    def _get_intent_cache_key(self, user_input: str, conversation_history: List[Dict[str, Any]], 
                             document_content: Optional[str] = None, available_tools: List[Dict[str, Any]] = None) -> str:
        """Generate a cache key for intent detection."""
        import hashlib
        
        # Create a hash of the key components
        key_components = [
            user_input.lower().strip(),
            str(len(conversation_history)),
            document_content[:100] if document_content else "",  # First 100 chars of doc
            str(len(available_tools)) if available_tools else "0"
        ]
        
        key_string = "|".join(key_components)
        return hashlib.md5(key_string.encode()).hexdigest()
    
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

            elif action_result[0] == IntentType.TOOL_EXECUTION:
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
                    intent_type = IntentType.TOOL_EXECUTION # Keep as tool execution even if failed
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
            # Check cache first
            cache_key = self._get_intent_cache_key(user_input, conversation_history, document_content, available_tools)
            current_time = time.time()
            
            if cache_key in self._intent_cache:
                cached_result = self._intent_cache[cache_key]
                if current_time - cached_result['timestamp'] < self._cache_ttl:
                    logger.info(f"Returning cached intent detection result (cache hit)")
                    return cached_result['result']
            
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
            
            # Cache the result
            self._intent_cache[cache_key] = {
                'result': result,
                'timestamp': current_time
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Intent detection failed: {str(e)}")
            return await self._fallback_intent_detection(user_input)
    
    def _get_generic_intent_type(self, tool_name: str) -> IntentType:
        """Get generic intent type for any tool - no hardcoded mapping."""
        # All tool executions are treated the same way
        return IntentType.TOOL_EXECUTION

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
            context_parts.append(f"Current Document Content:\n\'\'\'\n{doc_preview}\n\'\'\'")

        # Crucially, include full tool schemas for the LLM with enhanced descriptions
        if available_tools:
            tool_descriptions = []
            for tool in available_tools:
                # Create enhanced tool description for LLM decision making
                tool_info = {
                    "name": tool.get("name"),
                    "description": tool.get("description"),
                    "when_to_use": self._generate_tool_usage_guidance(tool),
                    "parameters": tool.get("input_schema")
                }
                tool_descriptions.append(json.dumps(tool_info, indent=2))
            context_parts.append(f"Available Tools (use these when appropriate):\n\'\'\'\n{'\n'.join(tool_descriptions)}\n\'\'\'")
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

        **CRITICAL TOOL USAGE RULES:**
        - ALWAYS use the appropriate tool when the user's request matches a tool's purpose
        - Look at each tool's description to understand when to use it
        - If the user explicitly asks for a tool by name, you MUST use that tool
        - ONLY provide conversational responses for simple greetings like "hello" or "hi"
        - When in doubt, prefer using a tool over conversational response

        Based on the user's intent, respond with a JSON object in one of two formats:

        **Format 1: Tool Call**
        If you determine a tool is necessary, provide the `tool_name` and a `parameters` object matching the tool's JSON schema.
        
        Example for tool call:
        ```json
        {{
            "action": "tool_call",
            "tool_name": "actual_tool_name_from_available_tools",
            "parameters": {{
                "parameter1": "value1",
                "parameter2": "value2"
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

        user_prompt = f"""Determine the user's intent and provide the appropriate JSON response based on the context.

IMPORTANT: The user said: "{context.split('User Input: ')[1].split('\n\n')[0]}"

Analyze the available tools and their descriptions to determine the best tool to use, or provide a conversational response if no tool is appropriate."""

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
                # Use generic intent type for any tool
                intent_type = self._get_generic_intent_type(tool_name)
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
    
    async def _format_tool_response(self, tool_result: Any, user_message: str) -> str:
        """Format tool execution result into a user-friendly response, handling different tool outputs."""
        # Handle empty dict case first
        if isinstance(tool_result, dict) and len(tool_result) == 0:
            return f"The tool executed successfully but provided no detailed output."
        
        # Don't treat error responses as failures - let the generic formatter handle them
        if not tool_result:
            return f"The requested operation for '{user_message}' returned no results."

        formatted_output_parts = []
        formatted_output_parts.append(f"Here's what I found for your request '{user_message}':")

        # Generic tool response formatting - no hardcoded tool handling
        # All tool responses are handled generically below

        # Handle tool results - check both direct result and nested result field
        result_content = None
        
        # Always use the tool_result directly for generic formatting
        # The generic formatter will handle all types intelligently
        result_content = tool_result

        if result_content is not None:
            # Generic intelligent formatting for any tool response
            formatted_content = self._format_any_tool_response(result_content)
            if formatted_content:
                formatted_output_parts.append(formatted_content)
            else:
                formatted_output_parts.append("The tool executed successfully but provided no detailed output.")
        else:
            formatted_output_parts.append("The tool executed successfully but provided no detailed output.")

        return "\n\n".join(formatted_output_parts)
    
    def _format_any_tool_response(self, result_content: Any) -> str:
        """
        Generic intelligent formatting for any tool response.
        Automatically detects and formats different response types without hardcoding specific tools.
        """
        try:
            # Handle string responses
            if isinstance(result_content, str):
                # Check if it's JSON that can be parsed and formatted
                if result_content.strip().startswith('{') or result_content.strip().startswith('['):
                    try:
                        import json
                        parsed = json.loads(result_content)
                        return self._format_structured_data(parsed)
                    except:
                        # Not valid JSON, return as-is
                        return result_content
                else:
                    return result_content
            
            # Handle list responses (common in MCP)
            elif isinstance(result_content, list):
                return self._format_list_response(result_content)
            
            # Handle dict responses
            elif isinstance(result_content, dict):
                return self._format_structured_data(result_content)
            
            # Handle other types
            else:
                return str(result_content)
                
        except Exception as e:
            # Fallback to string representation
            return str(result_content)
    
    def _format_list_response(self, data: list) -> str:
        """Format list responses intelligently."""
        if not data:
            return "No results found."
        
        formatted_parts = []
        
        for i, item in enumerate(data, 1):
            if isinstance(item, dict):
                # Check for common MCP response patterns
                if item.get("type") == "text" and "text" in item:
                    text_content = item["text"]
                    # Try to parse JSON content for better formatting
                    if isinstance(text_content, str) and (text_content.strip().startswith('{') or text_content.strip().startswith('[')):
                        try:
                            import json
                            parsed = json.loads(text_content)
                            formatted_parts.append(f"**Result {i}:**\n{self._format_structured_data(parsed)}")
                        except:
                            formatted_parts.append(f"**Result {i}:** {text_content}")
                    else:
                        formatted_parts.append(f"**Result {i}:** {text_content}")
                else:
                    formatted_parts.append(f"**Result {i}:**\n{self._format_structured_data(item)}")
            else:
                formatted_parts.append(f"**Result {i}:** {str(item)}")
        
        return "\n\n".join(formatted_parts)
    
    def _format_structured_data(self, data: dict) -> str:
        """Format structured data (dict) intelligently with emojis and user-friendly presentation."""
        if not data:
            return "No data available."
        
        formatted_parts = []
        
        # Special handling for MCP response format with nested JSON content
        content_parsed = False
        if "content" in data and isinstance(data["content"], list):
            for item in data["content"]:
                if isinstance(item, dict) and item.get("type") == "text" and "text" in item:
                    text_content = item["text"]
                    # Try to parse JSON content for better formatting
                    if isinstance(text_content, str) and (text_content.strip().startswith('{') or text_content.strip().startswith('[')):
                        try:
                            import json
                            parsed = json.loads(text_content)
                            formatted_parts.append(self._format_structured_data(parsed))
                            content_parsed = True
                            break  # Only parse the first valid JSON content
                        except:
                            pass  # Fall back to generic formatting
                    else:
                        # Simple text content - display directly
                        formatted_parts.append(text_content)
                        content_parsed = True
                        break
        
        # Look for common patterns and format them nicely
        for key, value in data.items():
            # Skip content field if we already parsed it
            if key.lower() == "content" and content_parsed:
                continue
                
            if key.lower() in ["status", "state"]:
                if value == "success" or value == "completed":
                    formatted_parts.append(f"✅ **Status**: {value}")
                elif value == "error" or value == "failed":
                    formatted_parts.append(f"❌ **Status**: {value}")
                else:
                    formatted_parts.append(f"📊 **Status**: {value}")
            
            elif key.lower() in ["progress", "thoughtnumber", "current"]:
                if isinstance(value, (int, float)):
                    formatted_parts.append(f"📊 **Progress**: {value}")
                else:
                    formatted_parts.append(f"📊 **{key.title()}**: {value}")
            
            elif key.lower() in ["total", "totalthoughts", "max"]:
                if isinstance(value, (int, float)):
                    formatted_parts.append(f"🎯 **Total**: {value}")
                else:
                    formatted_parts.append(f"🎯 **{key.title()}**: {value}")
            
            elif key.lower() in ["next", "nextthoughtneeded", "continue"]:
                if isinstance(value, bool):
                    if value:
                        formatted_parts.append(f"⏭️ **Next Step**: More processing needed")
                    else:
                        formatted_parts.append(f"✅ **Status**: Process complete")
                else:
                    formatted_parts.append(f"⏭️ **{key.title()}**: {value}")
            
            elif key.lower() in ["thought", "content", "message", "result"]:
                formatted_parts.append(f"💭 **{key.title()}**: {value}")
            
            elif key.lower() in ["history", "thoughthistorylength", "count"]:
                formatted_parts.append(f"📚 **{key.title()}**: {value}")
            
            elif key.lower() in ["branches", "alternatives", "options"]:
                if isinstance(value, list):
                    formatted_parts.append(f"🌿 **{key.title()}**: {len(value)} alternatives")
                else:
                    formatted_parts.append(f"🌿 **{key.title()}**: {value}")
            
            elif key.lower() in ["confidence", "accuracy", "score"]:
                if isinstance(value, (int, float)):
                    formatted_parts.append(f"📊 **{key.title()}**: {value}")
                else:
                    formatted_parts.append(f"📊 **{key.title()}**: {value}")
            
            elif key.lower() in ["error", "error_message", "details"]:
                formatted_parts.append(f"⚠️ **{key.title()}**: {value}")
            
            elif key.lower() in ["url", "link", "href"]:
                formatted_parts.append(f"🔗 **{key.title()}**: {value}")
            
            elif key.lower() in ["title", "name", "label"]:
                formatted_parts.append(f"📝 **{key.title()}**: {value}")
            
            elif key.lower() in ["snippet", "description", "summary"]:
                formatted_parts.append(f"📄 **{key.title()}**: {value}")
            
            else:
                # Generic formatting for unknown keys
                formatted_parts.append(f"📋 **{key.title()}**: {value}")
        
        return "\n\n".join(formatted_parts)
    
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
        """Get generic system prompt for any intent type."""
        base_prompt = "You are a helpful AI assistant for document analysis and text processing."
        
        if intent_type == IntentType.CONVERSATION:
            return f"{base_prompt} Respond naturally and conversationally to general questions and social interactions. Be warm, helpful, and guide the conversation toward how you can assist with document work."
        elif intent_type == IntentType.TOOL_EXECUTION:
            return f"{base_prompt} Execute tools and provide helpful responses based on the results."
        else:
            return f"{base_prompt} Be conversational, friendly, and helpful."
    
    def _get_fallback_response(self, intent_type: IntentType) -> str:
        """Get generic fallback response when LLM is not available."""
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
    
    def clear_intent_cache(self):
        """Clear the intent detection cache for debugging."""
        self._intent_cache.clear()
        logger.info("Intent detection cache cleared")
    
    def _generate_tool_usage_guidance(self, tool: Dict[str, Any]) -> str:
        """Generate usage guidance for a tool based on its name and description."""
        tool_name = tool.get("name", "").lower()
        description = tool.get("description", "").lower()
        
        # Generate dynamic usage guidance based on tool characteristics
        guidance_parts = []
        
        # Check for common patterns in tool names and descriptions
        if "search" in tool_name or "search" in description:
            guidance_parts.append("Use when user asks for web search, information lookup, or finding content online")
        
        if "sequential" in tool_name or "thinking" in tool_name or "sequential" in description or "thinking" in description:
            guidance_parts.append("Use when user asks for sequential thinking, step-by-step analysis, problem breakdown, or detailed planning")
        
        if "analysis" in tool_name or "analyze" in tool_name or "analysis" in description:
            guidance_parts.append("Use when user asks for text analysis, document analysis, or content analysis")
        
        if "document" in tool_name or "document" in description:
            guidance_parts.append("Use when user asks for document processing, document analysis, or document-related tasks")
        
        if "file" in tool_name or "read" in tool_name or "file" in description:
            guidance_parts.append("Use when user asks for file reading, file processing, or file-related operations")
        
        if "text" in tool_name or "text" in description:
            guidance_parts.append("Use when user asks for text processing, text analysis, or text-related operations")
        
        # If no specific patterns found, use the description
        if not guidance_parts:
            guidance_parts.append(f"Use when user's request matches: {description[:100]}...")
        
        return "; ".join(guidance_parts)


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
