"""
Intelligent Agent Service for Word Add-in MCP Project.

This service uses Azure OpenAI LLM for:
- Intent detection from user input
- Conversation context understanding
- Routing decisions to appropriate tools
- Dynamic response generation
"""

import structlog
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from enum import Enum

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
    UNKNOWN = "unknown"


class RoutingDecision(Enum):
    """Routing decisions for user intents."""
    CONVERSATIONAL_AI = "conversational_ai"
    TEXT_PROCESSOR = "text_processor"
    DOCUMENT_ANALYZER = "document_analyzer"
    WEB_CONTENT_FETCHER = "web_content_fetcher"
    FILE_READER = "file_reader"
    DATA_FORMATTER = "data_formatter"


class AgentService:
    """Intelligent agent service for intent detection and routing."""
    
    def __init__(self):
        """Initialize the agent service."""
        self.llm_client = None
        self._initialize_llm_client()
    
    def _initialize_llm_client(self):
        """Initialize the LLM client."""
        try:
            # Try different import paths based on environment
            try:
                from backend.app.services.llm_client import llm_client
                from backend.app.core.config import is_azure_openai_configured
                logger.info("Using backend.app.* import path")
            except ImportError:
                try:
                    from app.services.llm_client import llm_client
                    from app.core.config import is_azure_openai_configured
                    logger.info("Using app.* import path")
                except ImportError:
                    logger.error("Failed to import LLM client from any path")
                    self.llm_client = None
                    return
            
            if is_azure_openai_configured():
                self.llm_client = llm_client
                logger.info("Agent service initialized with Azure OpenAI LLM")
            else:
                logger.warning("Azure OpenAI not configured - agent will use fallback logic")
                self.llm_client = None
        except Exception as e:
            logger.error(f"Failed to initialize LLM client: {str(e)}")
            self.llm_client = None
    
    async def detect_intent_and_route(
        self,
        user_input: str,
        conversation_history: List[Dict[str, Any]],
        document_content: Optional[str] = None,
        available_tools: List[Dict[str, Any]] = None
    ) -> Tuple[IntentType, RoutingDecision, Dict[str, Any], str]:
        """
        Detect user intent and determine routing using LLM.
        
        Args:
            user_input: Current user message
            conversation_history: Previous conversation messages
            document_content: Current Word document content (if any)
            available_tools: List of available MCP tools
            
        Returns:
            Tuple of (intent_type, routing_decision, parameters, reasoning)
        """
        try:
            logger.info(f"Agent service: LLM client available: {self.llm_client is not None}")
            if not self.llm_client:
                logger.warning("Using fallback intent detection - no LLM client")
                return await self._fallback_intent_detection(user_input)
            
            # Prepare context for LLM
            context = self._prepare_context(user_input, conversation_history, document_content, available_tools)
            logger.info(f"Prepared context: {context[:200]}...")
            
            # Use LLM for intent detection and routing
            result = await self._llm_intent_detection(context)
            
            return result
            
        except Exception as e:
            logger.error(f"Intent detection failed: {str(e)}")
            return await self._fallback_intent_detection(user_input)
    
    def _prepare_context(
        self,
        user_input: str,
        conversation_history: List[Dict[str, Any]],
        document_content: Optional[str] = None,
        available_tools: List[Dict[str, Any]] = None
    ) -> str:
        """Prepare context information for LLM analysis."""
        context_parts = []
        
        # User input
        context_parts.append(f"User Input: {user_input}")
        
        # Conversation history (last 3 messages for context)
        if conversation_history:
            recent_history = conversation_history[-3:]
            history_text = "\n".join([
                f"{msg.get('role', 'user')}: {msg.get('content', '')[:100]}..."
                for msg in recent_history
            ])
            context_parts.append(f"Recent Conversation:\n{history_text}")
        
        # Document content (if available)
        if document_content:
            doc_preview = document_content[:500] + "..." if len(document_content) > 500 else document_content
            context_parts.append(f"Document Content Preview:\n{doc_preview}")
        
        # Available tools
        if available_tools:
            tools_text = "\n".join([
                f"- {tool.get('name', 'unknown')}: {tool.get('description', 'No description')}"
                for tool in available_tools
            ])
            context_parts.append(f"Available Tools:\n{tools_text}")
        
        return "\n\n".join(context_parts)
    
    async def _llm_intent_detection(self, context: str) -> Tuple[IntentType, RoutingDecision, Dict[str, Any], str]:
        """Use LLM to detect intent and determine routing."""
        
        logger.info("Starting LLM intent detection")
        
        system_prompt = """You are an intelligent routing agent for a document analysis and text processing system.

Your task is to:
1. Analyze the user's intent from their input
2. Consider conversation context and document content
3. Decide which tool or service should handle the request
4. Provide reasoning for your decision

Available routing options (use exact values):
- conversational_ai: For greetings, help, general questions, social interactions, casual inquiries, weather, time, jokes
- text_processor: For text analysis, summarization, keyword extraction, sentiment analysis, content enhancement
- document_analyzer: For document structure analysis, readability assessment, content insights
- web_content_fetcher: For search requests, online searches, "search for X", "find information about X", "search online for X", "who is X online", "what is X online", fetching web content, searching the internet
- file_reader: For reading and analyzing files
- data_formatter: For data formatting and transformation

Intent types (use exact values):
- greeting: Hello, hi, good morning, etc.
- help: Help requests, what can you do, tool explanations
- conversation: General chat, personal questions, weather, time, jokes, casual inquiries
- document_analysis: Analyze, examine, review documents
- text_processing: Process, summarize, extract, improve text
- web_content: For search requests, online searches, "search for X", "find information about X", "search online for X", "who is X online", "what is X online", fetching web content, searching the internet
- file_operations: Read, analyze, process files

Respond in this exact JSON format:
{
  "intent_type": "intent_name",
  "routing_decision": "routing_option",
  "parameters": {
    "tool_name": "specific_tool",
    "operation": "specific_operation",
    "additional_params": {}
  },
  "reasoning": "Explanation of why this routing decision was made",
  "confidence": 0.95
}

IMPORTANT EXAMPLES:
- "who is Ramy Atawia" → intent_type: "web_content", routing_decision: "web_content_fetcher"
- "search online for Ramy" → intent_type: "web_content", routing_decision: "web_content_fetcher"
- "find information about AI" → intent_type: "web_content", routing_decision: "web_content_fetcher"
- "what is the weather" → intent_type: "conversation", routing_decision: "conversational_ai"
- "fetch https://example.com" → intent_type: "web_content", routing_decision: "web_content_fetcher"
- "search for documents about AI" → intent_type: "web_content", routing_decision: "web_content_fetcher"
- "draft 2 claims" → intent_type: "text_processing", routing_decision: "text_processor", operation: "draft"
- "write a summary" → intent_type: "text_processing", routing_decision: "text_processor"
- "create content" → intent_type: "text_processing", routing_decision: "text_processor"
"""

        user_prompt = f"""Analyze this user request and determine the best routing:

{context}

Please provide your analysis in the specified JSON format."""

        try:
            logger.info("Calling LLM client for intent detection")
            result = self.llm_client.generate_text(
                prompt=user_prompt,
                max_tokens=400,
                temperature=0.3,
                system_message=system_prompt
            )
            logger.info(f"LLM response received: {result.get('success', False)}")
            
            if result.get("success"):
                # Parse LLM response
                response_text = result["text"]
                parsed_result = self._parse_llm_response(response_text)
                
                if parsed_result:
                    intent_type = IntentType(parsed_result.get("intent_type", "unknown"))
                    routing_decision = RoutingDecision(parsed_result.get("routing_decision", "conversational_ai"))
                    parameters = parsed_result.get("parameters", {})
                    reasoning = parsed_result.get("reasoning", "LLM analysis completed")
                    
                    logger.info(f"LLM intent detection successful", 
                              intent=intent_type.value,
                              routing=routing_decision.value,
                              reasoning=reasoning)
                    
                    return intent_type, routing_decision, parameters, reasoning
                else:
                    logger.warning("Failed to parse LLM response, using fallback")
                    return await self._fallback_intent_detection(context.split("User Input: ")[-1].split("\n")[0])
            else:
                logger.warning("LLM generation failed, using fallback")
                return await self._fallback_intent_detection(context.split("User Input: ")[-1].split("\n")[0])
                
        except Exception as e:
            logger.error(f"LLM intent detection failed: {str(e)}")
            return await self._fallback_intent_detection(context.split("User Input: ")[-1].split("\n")[0])
    
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
        """Extract intent and routing information from text when JSON parsing fails."""
        # Default to conversation when we can't parse the LLM response
        return {
            "intent_type": "conversation",
            "routing_decision": "conversational_ai",
            "parameters": {},
            "reasoning": "JSON parsing failed, defaulting to conversational AI",
            "confidence": 0.3
        }
    
    async def _fallback_intent_detection(self, user_input: str) -> Tuple[IntentType, RoutingDecision, Dict[str, Any], str]:
        """Fallback intent detection when LLM is not available."""
        # No pattern matching - default to conversation
        return IntentType.CONVERSATION, RoutingDecision.CONVERSATIONAL_AI, {}, "Fallback: LLM unavailable, defaulting to conversational AI"
    
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


# Global instance
agent_service = AgentService()
