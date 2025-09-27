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
from typing import Dict, Any, List, Optional, Tuple, Union, AsyncGenerator
from datetime import datetime
import json
import re

logger = structlog.get_logger()


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
    
    def get_recent_messages(self, count: int = None) -> List[Dict[str, Any]]:
        """Get recent conversation messages. If count is None, returns all messages."""
        if count is None:
            return self.messages
        return self.messages[-count:] if self.messages else []
    
    def clear(self):
        """Clear conversation memory."""
        self.messages.clear()
    


class AgentService:
    """Intelligent agent service for intent detection, routing, and tool execution."""
    
    def __init__(self):
        """Initialize the agent service."""
        self.llm_client = None
        self.conversation_memory = ConversationMemory()
        self.mcp_orchestrator = None
        self.unified_langgraph_agent = None  # Unified LangGraph integration
    
    def _get_llm_client(self):
        """Get LLM client with lazy initialization."""
        if self.llm_client is None:
            try:
                from .llm_client import get_llm_client
                from ..core.config import is_azure_openai_configured
                
                if is_azure_openai_configured():
                    self.llm_client = get_llm_client()
                    logger.debug("LLM client initialized")
                else:
                    logger.debug("Azure OpenAI not configured")
                    self.llm_client = None
            except ImportError as e:
                logger.error(f"Failed to import LLM client: {e}")
                self.llm_client = None
                
        return self.llm_client
    
    def _get_mcp_orchestrator(self):
        """Get MCP orchestrator with lazy initialization."""
        if self.mcp_orchestrator is None:
            try:
                from .mcp.orchestrator import get_initialized_mcp_orchestrator
                self.mcp_orchestrator = get_initialized_mcp_orchestrator()
                logger.debug("MCP orchestrator initialized")
            except RuntimeError as e:
                logger.error(f"MCP orchestrator initialization failed: {e}")
                raise RuntimeError("AgentService requires initialized MCP Orchestrator")
            except Exception as e:
                logger.error(f"Failed to initialize MCP orchestrator: {e}")
                raise RuntimeError(f"Failed to initialize MCP orchestrator: {str(e)}")
        return self.mcp_orchestrator
    
    def _get_unified_langgraph_agent(self):
        """Get unified LangGraph agent with lazy initialization."""
        if self.unified_langgraph_agent is None:
            try:
                from .langgraph_agent_unified import create_agent_graph, AgentGraphDependencies
                
                # Get dependencies with specific validation
                llm_client = self._get_llm_client()
                mcp_orchestrator = self._get_mcp_orchestrator()
                
                if not llm_client:
                    logger.error("LLM client initialization failed - Azure OpenAI may not be configured")
                    raise RuntimeError("LLM client not available for LangGraph agent")
                if not mcp_orchestrator:
                    logger.error("MCP orchestrator initialization failed")
                    raise RuntimeError("MCP orchestrator not available for LangGraph agent")
                
                # Create dependencies object
                dependencies = AgentGraphDependencies(llm_client, mcp_orchestrator)
                
                # Create agent graph with dependencies
                self.unified_langgraph_agent = create_agent_graph(dependencies)
                logger.debug("Unified LangGraph agent initialized with dependencies")
            except ImportError as e:
                logger.error(f"Failed to import unified LangGraph agent: {e}")
                self.unified_langgraph_agent = None
            except Exception as e:
                logger.error(f"Failed to initialize unified LangGraph agent: {e}")
                self.unified_langgraph_agent = None
        return self.unified_langgraph_agent
    
    
    async def process_user_message_unified_langgraph(
        self,
        user_message: str,
        document_content: Optional[str] = None,
        available_tools: List[Dict[str, Any]] = None,
        frontend_chat_history: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process user message using unified LangGraph workflow.
        
        This method handles both single-tool and multi-step workflows
        in one clean, unified architecture.
        """
        start_time = time.time()
        logger.debug(f"Unified LangGraph processing message: '{user_message[:50]}...'")
        
        try:
            # Get unified LangGraph agent
            langgraph_agent = self._get_unified_langgraph_agent()
            if not langgraph_agent:
                raise RuntimeError("Unified LangGraph agent not available")
            
            # Prepare initial state
            initial_state = {
                "user_input": user_message,
                "document_content": document_content or "",
                "conversation_history": frontend_chat_history or [],
                "available_tools": available_tools or [],
                "selected_tool": "",
                "tool_parameters": {},
                "tool_result": None,
                "final_response": "",
                "intent_type": "",
                "workflow_plan": None,
                "current_step": 0,
                "total_steps": 0,
                "step_results": {}
            }
            
            # Run unified LangGraph workflow (langgraph_agent is already a function with dependencies injected)
            result = await langgraph_agent(initial_state)
            
            # Convert to existing response format
            execution_time = time.time() - start_time
            
            # Extract tool name from workflow plan if available
            tool_name = None
            if result.get("workflow_plan"):
                first_step = result["workflow_plan"][0]
                tool_name = first_step.get("tool")
            elif result.get("selected_tool"):
                tool_name = result["selected_tool"]
            
            response_data = {
                "response": result["final_response"],
                "intent_type": result["intent_type"],
                "tool_name": tool_name,
                "execution_time": execution_time,
                "success": True,
                "error": None,
                "workflow_metadata": {
                    "total_steps": result.get("total_steps", 0),
                    "completed_steps": result.get("current_step", 0),
                    "workflow_type": "multi_step" if result.get("total_steps", 0) > 1 else "single_tool",
                    "workflow_plan": result.get("workflow_plan", [])
                }
            }
            
            logger.debug(f"Unified LangGraph completed - response length: {len(result['final_response'])}")
            return response_data
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_response = f"Unified LangGraph error: {str(e)}"
            logger.error(f"Unified LangGraph failed: {str(e)}")
            
            return {
                "response": error_response,
                "intent_type": "error",
                "tool_name": None,
                "execution_time": execution_time,
                "success": False,
                "error": str(e),
                "workflow_metadata": {
                    "total_steps": 0,
                    "completed_steps": 0,
                    "workflow_type": "error"
                }
            }
    
    
    async def process_user_message_streaming(
        self,
        user_message: str,
        document_content: Optional[str] = None,
        available_tools: List[Dict[str, Any]] = None,
        frontend_chat_history: List[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Process user message with LangGraph native streaming.
        
        Uses LangGraph's built-in .astream() method with proper chunk handling.
        """
        start_time = time.time()
        logger.debug(f"Streaming LangGraph processing message: '{user_message[:50]}...'")
        
        try:
            # Get unified LangGraph agent
            langgraph_agent = self._get_unified_langgraph_agent()
            if not langgraph_agent:
                raise RuntimeError("Unified LangGraph agent not available")
            
            # Prepare initial state (same as non-streaming version)
            initial_state = {
                "user_input": user_message,
                "document_content": document_content or "",
                "conversation_history": frontend_chat_history or [],
                "available_tools": available_tools or [],
                "selected_tool": "",
                "tool_parameters": {},
                "tool_result": None,
                "final_response": "",
                "intent_type": "",
                "workflow_plan": None,
                "current_step": 0,
                "total_steps": 0,
                "step_results": {}
            }
            
            # Track final result for completion event
            final_result = None
            
            # Use LangGraph's built-in streaming
            async for chunk in langgraph_agent.astream(
                initial_state, 
                stream_mode=["updates", "messages"]
            ):
                logger.debug(f"Received LangGraph chunk: {type(chunk)} - {chunk}")
                
                # Handle different chunk formats from LangGraph
                if isinstance(chunk, tuple) and len(chunk) == 2:
                    # Tuple format: ('updates', {node_name: node_data})
                    chunk_type, chunk_data = chunk
                    yield {
                        "event_type": "langgraph_chunk",
                        "data": {
                            "node": chunk_type,
                            "updates": {chunk_type: chunk_data} if chunk_data else {},
                            "messages": []
                        },
                        "timestamp": time.time()
                    }
                    
                    # Check if this chunk contains final response
                    if chunk_type == "updates" and isinstance(chunk_data, dict):
                        for node_name, node_data in chunk_data.items():
                            if isinstance(node_data, dict) and "final_response" in node_data:
                                final_result = node_data
                                logger.debug(f"Final result captured from {node_name}: {final_result.get('final_response', '')[:100]}...")
                elif isinstance(chunk, dict):
                    # Dictionary format: LangGraph's standard format
                    yield {
                        "event_type": "langgraph_chunk",
                        "data": chunk,
                        "timestamp": time.time()
                    }
                    
                    # Check if this is the final state with response
                    if "final_response" in chunk:
                        final_result = chunk
                        logger.debug(f"Final result captured: {final_result}")
                else:
                    # Other formats - wrap in generic structure
                    yield {
                        "event_type": "langgraph_chunk",
                        "data": {
                            "raw_chunk": chunk,
                            "updates": {},
                            "messages": []
                        },
                        "timestamp": time.time()
                    }
            
            # Send completion event after streaming finishes
            execution_time = time.time() - start_time
            logger.debug(f"LangGraph streaming completed in {execution_time:.2f}s")
            
            # If we have a final result, use it; otherwise generate a fallback response
            if final_result and final_result.get("final_response"):
                response_text = final_result["final_response"]
                logger.debug(f"Using final result response: {response_text[:100]}...")
            else:
                # Generate a fallback response using LLM
                logger.debug("No final result found, generating fallback response")
                try:
                    llm_client = self._get_llm_client()
                    if llm_client and llm_client.llm_available:
                        fallback_response = llm_client.generate_text(
                            prompt=f"User asked: {user_message}\n\nPlease provide a helpful response.",
                            max_tokens=500,
                            system_message="You are a helpful AI assistant. Provide a brief, helpful response to the user's request."
                        )
                        if fallback_response.get("success"):
                            generated_text = fallback_response.get("text", "")
                            # Validate response is not empty
                            if generated_text and len(generated_text.strip()) > 5:
                                response_text = generated_text
                            else:
                                logger.warning("LLM generated empty fallback response")
                                response_text = "I'm here to help! How can I assist you?"
                        else:
                            logger.error(f"LLM fallback response failed: {fallback_response.get('error')}")
                            response_text = "I'm here to help! How can I assist you?"
                    else:
                        response_text = "I'm here to help! How can I assist you?"
                except Exception as e:
                    logger.warning(f"Failed to generate fallback response: {e}")
                    response_text = "I'm here to help! How can I assist you?"
            
            # Send the final response as a streaming event
            yield {
                "event_type": "llm_response",
                "data": {
                    "content": response_text,
                    "is_streaming": False,
                    "is_complete": True
                },
                "timestamp": time.time()
            }
            
            yield {
                "event_type": "workflow_complete",
                "data": {
                    "message": "Workflow completed successfully",
                    "success": True,
                    "execution_time": execution_time,
                    "final_response": response_text
                },
                "timestamp": time.time()
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Streaming LangGraph failed: {str(e)}")
            
            yield {
                "event_type": "workflow_error",
                "data": {
                    "message": f"Workflow failed: {str(e)}",
                    "error": str(e),
                    "execution_time": execution_time
                },
                "timestamp": time.time()
            }
    
    
    async def process_user_message(
        self,
        user_message: str,
        document_content: Optional[str] = None,
        available_tools: List[Dict[str, Any]] = None,
        frontend_chat_history: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Main method to process user message end-to-end.
        """
        start_time = time.time()
        logger.debug(f"Agent processing message: '{user_message[:50]}...', tools: {len(available_tools) if available_tools else 0}")
        
        try:
            # Use frontend chat history if provided, otherwise use agent's own memory
            if frontend_chat_history:
                # Convert frontend format to agent format
                conversation_history = []
                for msg in frontend_chat_history:
                    # Handle both dict and string message formats
                    if isinstance(msg, dict):
                        conversation_history.append({
                            "role": msg.get("role", "user"),
                            "content": msg.get("content", ""),
                            "timestamp": msg.get("timestamp", time.time())
                        })
                    elif isinstance(msg, str):
                        conversation_history.append({
                            "role": "user",
                            "content": msg,
                            "timestamp": time.time()
                        })
                # Add current user message to the history
                conversation_history.append({
                    "role": "user",
                    "content": user_message,
                    "timestamp": time.time()
                })
                logger.debug(f"Using frontend chat history: {len(conversation_history)} messages (including current)")
            else:
                # Fallback to agent's own memory
                self.conversation_memory.add_message("user", user_message)
                conversation_history = self.conversation_memory.get_recent_messages()
                logger.debug(f"Using agent memory: {len(conversation_history)} messages")
            
            action_result = await self.detect_intent_and_route(
                user_input=user_message,
                conversation_history=conversation_history,
                document_content=document_content,
                available_tools=available_tools
            )

            intent_type, tool_name, parameters, reasoning = action_result
            logger.debug(f"Intent detected: {intent_type}, tool: {tool_name}")
            
            final_response = ""
            execution_result = {}
            tools_used = ["llm_chat"]

            if intent_type == "conversation":
                final_response = reasoning
            elif intent_type == "tool_execution":
                logger.info(f"Executing tool: {tool_name}")
                try:
                    orchestrator = self._get_mcp_orchestrator()
                    if not orchestrator:
                        raise RuntimeError("MCP Orchestrator not initialized.")

                    logger.debug(f"DEBUG: About to execute tool {tool_name} with parameters: {parameters}")
                    execution_result = await orchestrator.execute_tool(tool_name, parameters)
                    logger.debug(f"DEBUG: Tool execution result type: {type(execution_result)}")
                    logger.debug(f"DEBUG: Tool execution result keys: {execution_result.keys() if isinstance(execution_result, dict) else 'Not a dict'}")
                    if isinstance(execution_result, dict) and "result" in execution_result:
                        logger.debug(f"DEBUG: Nested result type: {type(execution_result['result'])}")
                        logger.debug(f"DEBUG: Nested result keys: {execution_result['result'].keys() if isinstance(execution_result['result'], dict) else 'Not a dict'}")
                        if isinstance(execution_result["result"], dict) and "report" in execution_result["result"]:
                            logger.debug(f"DEBUG: Report found in nested result, length: {len(execution_result['result']['report'])}")
                        else:
                            logger.debug(f"DEBUG: No report in nested result")
                    else:
                        logger.debug(f"DEBUG: No nested result field")
                    
                    # Extract the markdown content from all tools
                    if (isinstance(execution_result, dict) and 
                        "result" in execution_result and 
                        isinstance(execution_result["result"], str)):
                        
                        final_response = execution_result["result"]
                        logger.debug(f"DEBUG: EXTRACTION SUCCESS - length: {len(final_response)}")
                        
                        # For prior art search, verify it's the comprehensive report
                        if tool_name == "prior_art_search_tool":
                            if len(final_response) > 5000 and "Search Strategy Analysis" in final_response:
                                logger.debug(f"DEBUG: CONFIRMED - This is the comprehensive 7-section report")
                            else:
                                logger.error(f"DEBUG: WARNING - Report seems incomplete, length: {len(final_response)}")
                    else:
                        # Emergency fallback
                        logger.error(f"DEBUG: EXTRACTION FAILED - execution_result structure unexpected")
                        logger.error(f"DEBUG: execution_result keys: {execution_result.keys() if isinstance(execution_result, dict) else 'Not a dict'}")
                        final_response = f"Error: Unable to extract tool result. Tool executed but response structure was unexpected."
                    
                except Exception as e:
                    logger.error(f"DEBUG: Tool execution exception: {type(e).__name__}: {str(e)}")
                    final_response = f"Tool execution failed: {str(e)}"
            else:
                final_response = "I'm not sure how to help with that request."

            self.conversation_memory.add_message("assistant", final_response)
            execution_time = time.time() - start_time
            
            response_data = {
                "response": final_response,
                "intent_type": intent_type,
                "tool_name": tool_name,
                "execution_time": execution_time,
                "success": True,
                "error": None
            }
            
            logger.debug(f"DEBUG: Final response data - response length: {len(final_response) if final_response else 'None'}")
            logger.debug(f"DEBUG: Final response data - intent: {intent_type}, tool: {tool_name}, success: True")
            
            return response_data
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_response = f"Error processing request: {str(e)}"
            self.conversation_memory.add_message("assistant", error_response)
            
            return {
                "response": error_response,
                "intent_type": "unknown",
                "tool_name": None,
                "execution_time": execution_time,
                "success": False,
                "error": str(e)
            }
    
    async def detect_intent_and_route(
        self,
        user_input: str,
        conversation_history: List[Dict[str, Any]],
        document_content: Optional[str] = None,
        available_tools: List[Dict[str, Any]] = None
    ) -> Tuple[str, str, Dict[str, Any], str]:
        """
        Detect user intent and determine routing using LLM.
        """
        logger.debug(f"Detecting intent for: '{user_input[:30]}...', tools: {len(available_tools) if available_tools else 0}")
        
        try:
            llm_client = self._get_llm_client()
            if not llm_client:
                logger.debug("No LLM client, defaulting to conversation")
                return "conversation", None, {}, "I'm happy to chat with you!"

            context = self._prepare_context(user_input, conversation_history, document_content, available_tools)
            return await self._llm_intent_detection(context, llm_client)
            
        except Exception as e:
            logger.error(f"Intent detection failed: {type(e).__name__}: {str(e)}")
            return "conversation", None, {}, "I'm having trouble understanding your request, but I'm here to help!"

    def _prepare_context(self,
        user_input: str,
        conversation_history: List[Dict[str, Any]],
        document_content: Optional[str] = None,
        available_tools: List[Dict[str, Any]] = None
    ) -> str:
        """Prepare context information for LLM analysis."""
        try:
            context_parts = []
            context_parts.append(f"User Input: {user_input}")

            if conversation_history:
                # Truncate conversation history to prevent token limit issues
                # Keep only the last 5 messages to maintain context while staying within limits
                recent_history = conversation_history[-5:] if len(conversation_history) > 5 else conversation_history
                history_parts = []
                for msg in recent_history:
                    # Handle both dict and string message formats
                    if isinstance(msg, dict):
                        role = msg.get('role', 'user')
                        content = msg.get('content', '')
                    elif isinstance(msg, str):
                        role = 'user'
                        content = msg
                    else:
                        continue
                    history_parts.append(f"{role}: {content}")
                history_text = "\n".join(history_parts)
                context_parts.append(f"Conversation History (last {len(recent_history)} messages):\n{history_text}")

            if document_content:
                # Use full document content (up to 10000 chars from frontend)
                doc_preview = document_content[:10000] + "..." if len(document_content) > 10000 else document_content
                context_parts.append(f"Current Document Content:\n'''\n{doc_preview}\n'''")

            if available_tools:
                tool_descriptions = []
                for tool in available_tools:
                    tool_info = {
                        "name": tool.get("name"),
                        "description": tool.get("description"),
                        "parameters": tool.get("input_schema")
                    }
                    tool_descriptions.append(json.dumps(tool_info, indent=2))
                context_parts.append(f"Available Tools:\n'''\n{chr(10).join(tool_descriptions)}\n'''")

            return "\n\n".join(context_parts)
            
        except Exception as e:
            logger.error(f"Context preparation failed: {type(e).__name__}: {str(e)}")
            return f"User Input: {user_input}"

    async def _llm_intent_detection(self, context: str, llm_client) -> Tuple[str, str, Dict[str, Any], str]:
        """Use LLM to detect intent and return routing decision."""

        system_prompt = f'''
        Analyze user input and determine whether to call a tool or provide a conversational response.

        {context}

        IMPORTANT RULES:
        1. For web search requests like "web search [query]" or "search for [query]":
           - Extract the query after "web search" or "search for"
           - Use web_search_tool with {{"query": "extracted_query"}}
           - Example: "web search ramy Atawia" → {{"action": "tool_call", "tool_name": "web_search_tool", "parameters": {{"query": "ramy Atawia"}}}}
        
        2. For prior art search or patent search:
           - Use prior_art_search_tool with the invention/technology as query
           - Example: "prior art search 5G" → {{"action": "tool_call", "tool_name": "prior_art_search_tool", "parameters": {{"query": "5G"}}}}
        
        3. For claim drafting:
           - Use claim_drafting_tool with user query, conversation context, and document reference
           - ALWAYS include the document content in document_reference parameter
           - ALWAYS include conversation history in conversation_context parameter
           - Extract the relevant context from the document and conversation
           - Example: "draft claims for AI system" → {{"action": "tool_call", "tool_name": "claim_drafting_tool", "parameters": {{"user_query": "draft claims for AI system", "conversation_context": "extracted_conversation_context", "document_reference": "extracted_document_content"}}}}
        
        4. Always extract the actual content/query from user messages - don't leave parameters empty
        5. For claim drafting, ALWAYS use the document content and conversation context to create relevant, specific claims

        Respond with JSON in one of two formats:

        Tool Call (with extracted parameters):
        {{{{
            "action": "tool_call",
            "tool_name": "exact_tool_name_from_available_tools",
            "parameters": {{{{
                "query": "extracted_search_term_or_content"
            }}}}
        }}}}

        Conversational Response (if unclear):
        {{{{
            "action": "conversational_response",
            "response": "Your response text"
        }}}}

        Only output valid JSON.
        '''

        user_input = context.split('User Input: ')[1].split('\n\n')[0] if 'User Input: ' in context else "Unknown"
        user_prompt = f"""Analyze the request and provide appropriate JSON response.

User said: "{user_input}"

Choose the most appropriate tool or provide a conversational response."""

        try:
            raw_llm_response = llm_client.generate_text(
                prompt=user_prompt,
                max_tokens=2000,
                system_message=system_prompt
            )

            if not raw_llm_response.get("success"):
                logger.error(f"LLM tool selection failed: {raw_llm_response.get('error')}")
                raise RuntimeError(f"LLM tool selection failed: {raw_llm_response.get('error')}")

            llm_response_text = raw_llm_response.get("text", "")
            
            # Enhanced validation and logging
            logger.info(f"LLM tool selection response generated", 
                       response_length=len(llm_response_text),
                       response_preview=llm_response_text[:100] if llm_response_text else "EMPTY")
            
            # Validate response is not empty
            if not llm_response_text or len(llm_response_text.strip()) < 10:
                logger.error("LLM generated empty tool selection response", 
                            response=raw_llm_response,
                            generated_text=llm_response_text)
                raise RuntimeError("LLM generated empty tool selection response")

            # Extract JSON from response
            json_match = re.search(r'```json\s*\n(?P<json_content>.*?)\n\s*```', llm_response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group("json_content")
            else:
                json_str = llm_response_text

            try:
                parsed_response = json.loads(json_str)
            except json.JSONDecodeError:
                return "conversation", None, {}, f"I had trouble processing that request, but I'm here to help!"

            action = parsed_response.get("action")

            if action == "tool_call":
                tool_name = parsed_response.get("tool_name")
                parameters = parsed_response.get("parameters", {})
                if not tool_name or not isinstance(parameters, dict):
                    return "conversation", None, {}, "I'm not sure how to process that tool request."
                
                # For claim drafting tool, ensure context is properly passed
                if tool_name == "claim_drafting_tool":
                    # Extract context from the prepared context string
                    context_lines = context.split('\n')
                    conversation_context = ""
                    document_reference = ""
                    
                    for line in context_lines:
                        if line.startswith("Conversation History"):
                            conversation_context = line.split(":", 1)[1].strip() if ":" in line else ""
                        elif line.startswith("Current Document Content"):
                            # Find the document content between the triple quotes
                            doc_start = context.find("'''")
                            if doc_start != -1:
                                doc_end = context.find("'''", doc_start + 3)
                                if doc_end != -1:
                                    document_reference = context[doc_start + 3:doc_end].strip()
                    
                    # Update parameters with extracted context
                    if conversation_context:
                        parameters["conversation_context"] = conversation_context
                    if document_reference:
                        parameters["document_reference"] = document_reference
                
                reasoning = f"Tool call: {tool_name}"
                return "tool_execution", tool_name, parameters, reasoning

            elif action == "conversational_response":
                response_text = parsed_response.get("response")
                if not response_text:
                    return "conversation", None, {}, "I'm here to help! What would you like to know?"
                return "conversation", None, {}, response_text

            else:
                return "conversation", None, {}, "I'm not sure how to help with that, but I'm happy to try something else!"

        except Exception as e:
            logger.error(f"LLM intent detection failed: {type(e).__name__}: {str(e)}")
            return "conversation", None, {}, "I'm having some technical difficulties, but I'm still here to help!"
    
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
            # Fallback to simple string conversion
            if tool_output is None:
                return f"The {tool_name or 'tool'} executed but returned no results."
            return str(tool_output)
        
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

        try:
            # Get formatted response from LLM
            result = llm_client.generate_text(
                prompt=user_prompt,
                max_tokens=32000,  # Increased limit for comprehensive analysis
                system_message=system_prompt
            )
            
            if not result.get("success"):
                logger.error(f"LLM formatting failed: {result.get('error', 'Unknown error')}")
                return str(tool_output)
            
            generated_text = result.get("text", "")
            
            # Enhanced validation and logging
            logger.info(f"LLM formatting response generated", 
                       response_length=len(generated_text),
                       response_preview=generated_text[:100] if generated_text else "EMPTY")
            
            # Validate response is not empty
            if not generated_text or len(generated_text.strip()) < 10:
                logger.error("LLM generated empty formatting response", 
                            response=result,
                            generated_text=generated_text)
                return str(tool_output)
            
            return generated_text
                
        except Exception as e:
            logger.error(f"LLM formatting error: {str(e)}")
            return str(tool_output)


# Global instance
_agent_service_instance = None

def get_agent_service():
    """Get the agent service instance."""
    global _agent_service_instance
    if _agent_service_instance is None:
        _agent_service_instance = AgentService()
    return _agent_service_instance

agent_service = get_agent_service()