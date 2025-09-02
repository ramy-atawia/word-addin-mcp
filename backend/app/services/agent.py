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
from typing import Dict, Any, List, Optional, Tuple, Union
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
        self.max_messages = 50
    
    def add_message(self, role: str, content: str):
        """Add a message to conversation history."""
        message = {
            "role": role,
            "content": content,
            "timestamp": time.time()
        }
        self.messages.append(message)
        
        if len(self.messages) > self.max_messages:
            self.messages = self.messages[-self.max_messages:]
    
    def get_recent_messages(self, count: int = 10) -> List[Dict[str, Any]]:
        """Get recent conversation messages."""
        return self.messages[-count:] if self.messages else []
    
    def get_conversation_history_string(self) -> str:
        """Get conversation history as formatted string."""
        if not self.messages:
            return ""
        
        history_lines = []
        for msg in self.messages[-10:]:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')[:100]
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
        self.mcp_orchestrator = None
        self._intent_cache = {}
        self._cache_ttl = 60
    
    def _get_llm_client(self):
        """Get LLM client with lazy initialization."""
        if self.llm_client is None:
            try:
                from .llm_client import get_llm_client
                from ..core.config import is_azure_openai_configured
            except ImportError:
                self.llm_client = None
                return None
            
            if is_azure_openai_configured():
                self.llm_client = get_llm_client()
            else:
                self.llm_client = None
        return self.llm_client
    
    def _get_mcp_orchestrator(self):
        """Get MCP orchestrator with lazy initialization."""
        if self.mcp_orchestrator is None:
            try:
                from .mcp.orchestrator import get_initialized_mcp_orchestrator
                self.mcp_orchestrator = get_initialized_mcp_orchestrator()
            except RuntimeError as e:
                raise RuntimeError("AgentService requires initialized MCP Orchestrator")
            except Exception as e:
                raise RuntimeError(f"Failed to initialize MCP orchestrator: {str(e)}")
        return self.mcp_orchestrator
    
    def _get_intent_cache_key(self, user_input: str, conversation_history: List[Dict[str, Any]], 
                             document_content: Optional[str] = None, available_tools: List[Dict[str, Any]] = None) -> str:
        """Generate a cache key for intent detection."""
        import hashlib
        
        key_components = [
            user_input.lower().strip(),
            str(len(conversation_history)),
            document_content[:100] if document_content else "",
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
        """
        start_time = time.time()
        
        try:
            self.conversation_memory.add_message("user", user_message)
            conversation_history = self.conversation_memory.get_recent_messages()
            
            action_result = await self.detect_intent_and_route(
                user_input=user_message,
                conversation_history=conversation_history,
                document_content=document_content,
                available_tools=available_tools
            )

            intent_type, tool_name, parameters, reasoning = action_result
            final_response = ""
            execution_result = {}
            tools_used = ["llm_chat"]

            if intent_type == IntentType.CONVERSATION:
                final_response = reasoning
            elif intent_type == IntentType.TOOL_EXECUTION:
                try:
                    orchestrator = self._get_mcp_orchestrator()
                    if not orchestrator:
                        raise RuntimeError("MCP Orchestrator not initialized.")

                    execution_result = await orchestrator.execute_tool(tool_name, parameters)
                    final_response = await self._format_tool_response(execution_result, user_message, tool_name)
                    tools_used = ["llm_chat", tool_name]

                except Exception as e:
                    final_response = f"Tool execution failed: {str(e)}"
                    tools_used = ["llm_chat", f"{tool_name}_failed"]
                    intent_type = IntentType.TOOL_EXECUTION
            else:
                final_response = "Unable to process request."
                intent_type = IntentType.UNKNOWN

            self.conversation_memory.add_message("assistant", final_response)
            execution_time = time.time() - start_time
            
            return {
                "response": final_response,
                "intent_type": intent_type.value,
                "tool_name": tool_name,
                "tools_used": tools_used,
                "execution_time": execution_time,
                "success": True,
                "reasoning": reasoning,
                "conversation_memory_size": self.conversation_memory.get_memory_size()
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_response = f"Error processing request: {str(e)}"
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
        """
        try:
            cache_key = self._get_intent_cache_key(user_input, conversation_history, document_content, available_tools)
            current_time = time.time()
            
            if cache_key in self._intent_cache:
                cached_result = self._intent_cache[cache_key]
                if current_time - cached_result['timestamp'] < self._cache_ttl:
                    return cached_result['result']
            
            llm_client = self._get_llm_client()
            if not llm_client:
                return await self._fallback_intent_detection(user_input, available_tools)
            
            context = self._prepare_context(user_input, conversation_history, document_content, available_tools)
            result = await self._llm_intent_detection(context, llm_client)
            
            self._intent_cache[cache_key] = {
                'result': result,
                'timestamp': current_time
            }
            
            return result
            
        except Exception as e:
            return await self._fallback_intent_detection(user_input, available_tools)
    
    def _get_generic_intent_type(self, tool_name: str) -> IntentType:
        """Get generic intent type for any tool - no hardcoded mapping."""
        return IntentType.TOOL_EXECUTION

    def _prepare_context(self,
        user_input: str,
        conversation_history: List[Dict[str, Any]],
        document_content: Optional[str] = None,
        available_tools: List[Dict[str, Any]] = None
    ) -> str:
        """Prepare context information for LLM analysis."""
        context_parts = []
        context_parts.append(f"User Input: {user_input}")

        if conversation_history:
            recent_history = conversation_history[-5:]
            history_text = "\n".join([
                f"{msg.get('role', 'user')}: {msg.get('content', '')}"
                for msg in recent_history
            ])
            context_parts.append(f"Recent Conversation:\n{history_text}")

        if document_content:
            doc_preview = document_content[:1000] + "..." if len(document_content) > 1000 else document_content
            context_parts.append(f"Current Document Content:\n\'\'\'\n{doc_preview}\n\'\'\'")

        if available_tools:
            tool_descriptions = []
            for tool in available_tools:
                tool_info = {
                    "name": tool.get("name"),
                    "description": tool.get("description"),
                    "usage": self._generate_tool_usage_guidance(tool),
                    "parameters": tool.get("input_schema")
                }
                tool_descriptions.append(json.dumps(tool_info, indent=2))
            context_parts.append(f"Available Tools:\n\'\'\'\n{'\n'.join(tool_descriptions)}\n\'\'\'")

        return "\n\n".join(context_parts)

    async def _llm_intent_detection(self, context: str, llm_client) -> Tuple[IntentType, str, Dict[str, Any], str]:
        """Use LLM to detect intent and return actual MCP tool names."""

        system_prompt = f'''
        Analyze user input and determine whether to call a tool or provide a conversational response.

        {context}

        Respond with JSON in one of two formats:

        Tool Call:
        {{
            "action": "tool_call",
            "tool_name": "exact_tool_name_from_available_tools",
            "parameters": {{
                "param1": "value1"
            }}
        }}

        Conversational Response:
        {{
            "action": "conversational_response",
            "response": "Your response text"
        }}

        Only output valid JSON.
        '''

        user_prompt = f"""Analyze the request and provide appropriate JSON response.

User said: "{context.split('User Input: ')[1].split('\n\n')[0]}"

Choose the most appropriate tool or provide a conversational response."""

        try:
            raw_llm_response = llm_client.generate_text(
                prompt=user_prompt,
                max_tokens=800,
                temperature=0.0,
                system_message=system_prompt
            )

            if isinstance(raw_llm_response, dict) and "text" in raw_llm_response:
                llm_response_text = raw_llm_response["text"]
            else:
                llm_response_text = str(raw_llm_response)

            json_match = re.search(r'```json\s*\n(?P<json_content>.*?)\n\s*```', llm_response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group("json_content")
            else:
                json_str = llm_response_text

            try:
                parsed_response = json.loads(json_str)
            except json.JSONDecodeError:
                return IntentType.UNKNOWN, None, {}, f"Invalid JSON: {json_str}"

            action = parsed_response.get("action")

            if action == "tool_call":
                tool_name = parsed_response.get("tool_name")
                parameters = parsed_response.get("parameters", {})
                if not tool_name or not isinstance(parameters, dict):
                    return IntentType.UNKNOWN, None, {}, "Malformed tool call"
                
                intent_type = self._get_generic_intent_type(tool_name)
                reasoning = f"Tool call: {tool_name}"
                return intent_type, tool_name, parameters, reasoning

            elif action == "conversational_response":
                response_text = parsed_response.get("response")
                if not response_text:
                    return IntentType.UNKNOWN, None, {}, "Empty conversational response"
                return IntentType.CONVERSATION, None, {}, response_text

            else:
                return IntentType.UNKNOWN, None, {}, f"Unknown action: {action}"

        except Exception as e:
            return IntentType.UNKNOWN, None, {}, f"LLM processing failed: {str(e)}"
    
    async def _fallback_intent_detection(self, user_input: str, available_tools: List[Dict[str, Any]] = None) -> Tuple[IntentType, str, Dict[str, Any], str]:
        """Fallback intent detection without hardcoded patterns."""
        
        user_input_lower = user_input.lower().strip()
        
        # Simple conversational patterns
        simple_greetings = ['hi', 'hello', 'hey', 'thanks', 'thank you', 'bye', 'goodbye']
        if user_input_lower in simple_greetings:
            return IntentType.CONVERSATION, None, {}, "Simple interaction detected"
        
        # Try to match available tools
        if available_tools:
            best_match = self._find_best_tool_match(user_input, available_tools)
            if best_match:
                tool_name, confidence, suggested_params = best_match
                if confidence > 0.6:
                    return IntentType.TOOL_EXECUTION, tool_name, suggested_params, f"Tool matched: {tool_name}"
        
        # Default to conversation
        return IntentType.CONVERSATION, None, {}, "Defaulting to conversation"
    
    def _find_best_tool_match(self, user_input: str, available_tools: List[Dict[str, Any]]) -> Optional[Tuple[str, float, Dict[str, Any]]]:
        """Find best matching tool based on word overlap."""
        
        user_words = set(user_input.lower().split())
        best_match = None
        best_score = 0.0
        
        for tool in available_tools:
            tool_name = tool.get("name", "").lower()
            description = tool.get("description", "").lower()
            tool_words = set((tool_name + " " + description).split())
            common_words = user_words.intersection(tool_words)
            
            if common_words:
                score = len(common_words) / len(user_words.union(tool_words))
                
                if score > best_score:
                    best_score = score
                    suggested_params = self._extract_basic_parameters(user_input, tool)
                    best_match = (tool.get("name"), score, suggested_params)
        
        return best_match
    
    def _extract_basic_parameters(self, user_input: str, tool: Dict[str, Any]) -> Dict[str, Any]:
        """Extract basic parameters from user input based on tool schema."""
        
        params = {}
        input_schema = tool.get("input_schema", {})
        properties = input_schema.get("properties", {})
        
        for param_name, param_info in properties.items():
            param_type = param_info.get("type", "string")
            
            if param_type == "string":
                if param_name.lower() in ["query", "text", "input", "content"]:
                    params[param_name] = user_input
                elif param_name.lower() in ["url", "path", "file"]:
                    url_match = re.search(r'https?://\S+', user_input)
                    if url_match:
                        params[param_name] = url_match.group()
        
        return params
    
    async def _format_tool_response(self, tool_result: Any, user_message: str, tool_name: str = None) -> str:
        """Format tool execution result into user-friendly response using LLM."""
        
        if tool_result is None:
            return f"The {tool_name or 'tool'} executed but returned no results."
        
        if isinstance(tool_result, dict) and len(tool_result) == 0:
            return f"The {tool_name or 'tool'} executed successfully."
        
        # Use LLM to format the tool output
        formatted_response = await self.format_tool_output_with_llm(tool_result, user_message, tool_name)
        return formatted_response
    
    def _format_mcp_content_response(self, content_list: List[Dict[str, Any]], user_message: str, tool_name: str = None) -> str:
        """Format MCP content response."""
        
        if not content_list:
            return f"The {tool_name or 'tool'} returned no content."
        
        formatted_parts = []
        
        for i, content_item in enumerate(content_list):
            if not isinstance(content_item, dict):
                formatted_parts.append(str(content_item))
                continue
            
            content_type = content_item.get("type", "unknown")
            
            if content_type == "text":
                text_content = content_item.get("text", "")
                if text_content:
                    if text_content.strip().startswith('{') or text_content.strip().startswith('['):
                        try:
                            parsed_json = json.loads(text_content)
                            formatted_content = self._format_json_content(parsed_json)
                            formatted_parts.append(formatted_content)
                        except json.JSONDecodeError:
                            formatted_parts.append(text_content)
                    else:
                        formatted_parts.append(text_content)
            
            elif content_type == "resource":
                uri = content_item.get("uri", "Unknown resource")
                name = content_item.get("name", "")
                formatted_parts.append(f"Resource: {name or uri}")
                
                resource_text = content_item.get("text", "")
                if resource_text:
                    display_text = resource_text[:500] + "..." if len(resource_text) > 500 else resource_text
                    formatted_parts.append(display_text)
            
            else:
                formatted_parts.append(json.dumps(content_item, indent=2))
        
        return "\n\n".join(formatted_parts)
    
    def _format_json_content(self, json_data: Union[Dict[str, Any], List[Any]]) -> str:
        """Format JSON content."""
        
        if isinstance(json_data, dict):
            return self._format_structured_response(json_data, "", "")
        elif isinstance(json_data, list):
            if not json_data:
                return "Empty list"
            
            formatted_items = []
            for i, item in enumerate(json_data):
                if isinstance(item, dict):
                    formatted_items.append(f"Item {i+1}: {self._format_structured_response(item, '', '')}")
                else:
                    formatted_items.append(f"Item {i+1}: {str(item)}")
            
            return "\n".join(formatted_items)
        else:
            return str(json_data)
    
    def _format_text_response(self, text_content: str, user_message: str, tool_name: str = None) -> str:
        """Format plain text response."""
        
        if not text_content or not text_content.strip():
            return f"The {tool_name or 'tool'} returned empty response."
        
        return text_content
    
    def _format_structured_response(self, data: Dict[str, Any], user_message: str, tool_name: str = None) -> str:
        """Format structured data response dynamically."""
        
        if not data:
            return f"The {tool_name or 'tool'} returned no data."
        
        formatted_parts = []
        sorted_items = self._sort_response_fields(list(data.items()))
        
        for key, value in sorted_items:
            formatted_field = self._format_field_dynamically(key, value)
            if formatted_field:
                formatted_parts.append(formatted_field)
        
        return "\n".join(formatted_parts) if formatted_parts else "No data to display"
    
    def _sort_response_fields(self, items: List[Tuple[str, Any]]) -> List[Tuple[str, Any]]:
        """Sort response fields by likely importance."""
        
        def field_importance(item):
            key, value = item
            key_lower = key.lower()
            
            if any(word in key_lower for word in ['result', 'output', 'response', 'answer']):
                return 0
            elif any(word in key_lower for word in ['status', 'state', 'success', 'error']):
                return 1
            elif any(word in key_lower for word in ['content', 'text', 'message', 'data']):
                return 2
            elif any(word in key_lower for word in ['id', 'timestamp', 'version', 'metadata']):
                return 4
            else:
                return 3
        
        return sorted(items, key=field_importance)
    
    def _format_field_dynamically(self, key: str, value: Any) -> str:
        """Format individual field without hardcoded mappings."""
        
        formatted_key = key.replace('_', ' ').title()
        
        if isinstance(value, bool):
            formatted_value = "Yes" if value else "No"
        elif isinstance(value, dict):
            if len(str(value)) > 200:
                formatted_value = f"{len(value)} fields"
            else:
                formatted_value = json.dumps(value, indent=2)
        elif isinstance(value, list):
            if len(value) == 0:
                formatted_value = "Empty list"
            elif len(str(value)) > 200:
                formatted_value = f"{len(value)} items"
            else:
                formatted_value = ", ".join(str(item) for item in value[:5])
                if len(value) > 5:
                    formatted_value += f" ... and {len(value) - 5} more"
        else:
            formatted_value = str(value)
        
        return f"{formatted_key}: {formatted_value}"
    
    def _format_list_response(self, data: list, user_message: str, tool_name: str = None) -> str:
        """Format list responses."""
        
        if not data:
            return f"The {tool_name or 'tool'} returned empty list."
        
        formatted_parts = []
        
        for i, item in enumerate(data, 1):
            if isinstance(item, dict):
                formatted_item = self._format_structured_response(item, user_message, tool_name)
                formatted_parts.append(f"Result {i}: {formatted_item}")
            elif isinstance(item, str):
                display_item = item[:200] + "..." if len(item) > 200 else item
                formatted_parts.append(f"Result {i}: {display_item}")
            else:
                formatted_parts.append(f"Result {i}: {str(item)}")
        
        return "\n".join(formatted_parts)
    
    def _generate_tool_usage_guidance(self, tool: Dict[str, Any]) -> str:
        """Generate usage guidance dynamically based on tool schema."""
        
        description = tool.get("description", "").strip()
        input_schema = tool.get("input_schema", {})
        
        guidance_parts = []
        
        if description:
            clean_description = description.rstrip('.')
            guidance_parts.append(f"Use when: {clean_description}")
        
        properties = input_schema.get("properties", {})
        if properties:
            param_hints = []
            for param_name, param_info in properties.items():
                param_desc = param_info.get("description", "")
                if param_desc:
                    param_hints.append(f"{param_name}: {param_desc}")
            
            if param_hints:
                guidance_parts.append(f"Parameters: {'; '.join(param_hints[:3])}")
        
        if not guidance_parts:
            tool_name = tool.get("name", "")
            guidance_parts.append(f"Use the {tool_name} tool when appropriate")
        
        return " | ".join(guidance_parts)
    
    # Memory management methods
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
        """Clear the intent detection cache."""
        self._intent_cache.clear()
    
    async def format_tool_output_with_llm(self, tool_output: Any, user_query: str, tool_name: str = None) -> str:
        """
        Use LLM to format tool output into user-friendly markdown/HTML.
        
        Args:
            tool_output: Raw output from the tool
            user_query: Original user query
            tool_name: Name of the tool that produced the output
            
        Returns:
            Formatted response as markdown/HTML
        """
        llm_client = self._get_llm_client()
        if not llm_client:
            raise RuntimeError("LLM client not available for formatting tool output")
        
        # Convert tool output to string for LLM processing
        if isinstance(tool_output, dict):
            tool_output_str = json.dumps(tool_output, indent=2)
        elif isinstance(tool_output, list):
            tool_output_str = json.dumps(tool_output, indent=2)
        else:
            tool_output_str = str(tool_output)
        
        # Create system prompt for formatting
        system_prompt = f"""You are a helpful assistant that formats tool outputs into user-friendly responses.

Your task is to take raw tool output and format it into clean, readable markdown that answers the user's query.

Guidelines:
1. Parse and structure the data intelligently
2. Use proper markdown formatting (headings, lists, links, etc.)
3. Make the content easy to read and understand
4. Include relevant links and references
5. Focus on answering the user's specific question
6. If the data contains search results, format them as a structured list
7. Clean up any escaped characters or formatting issues
8. Keep the response concise but comprehensive

Tool used: {tool_name or 'Unknown tool'}
User query: {user_query}

Format the following tool output into a clean, user-friendly response:"""

        user_prompt = f"""Please format this tool output to answer the user's query: "{user_query}"

Tool Output:
{tool_output_str}

Provide a well-formatted markdown response that directly answers the user's question."""

        # Get formatted response from LLM
        result = llm_client.generate_text(
            prompt=user_prompt,
            max_tokens=1500,
            temperature=0.3,
            system_message=system_prompt
        )
        
        if result.get("success") and result.get("text"):
            return result["text"]
        else:
            raise RuntimeError(f"LLM formatting failed: {result.get('error', 'Unknown error')}")


# Global instance
_agent_service_instance = None

def get_agent_service():
    """Get the agent service instance."""
    global _agent_service_instance
    if _agent_service_instance is None:
        _agent_service_instance = AgentService()
    return _agent_service_instance

agent_service = get_agent_service()