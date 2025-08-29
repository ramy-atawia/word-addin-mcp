"""
Text Processor Tool for Word Add-in MCP Project.

This tool implements the MCP tool interface for text processing with:
- Text processing operations (summarize, translate, analyze, etc.)
- Azure OpenAI integration
- Operation parameter validation
- Result formatting
- Processing time tracking
- Error handling and retry logic
"""

import time
from typing import Dict, Any, List
import structlog

from app.core.mcp_tool_interface import (
    BaseMCPTool,
    ToolMetadata,
    ToolExecutionContext,
    ToolExecutionResult,
    ToolExecutionStatus,
    ToolErrorCode
)
from app.services.llm_client import llm_client
from app.core.config import get_azure_openai_config, is_azure_openai_configured

logger = structlog.get_logger()


class TextProcessorTool(BaseMCPTool):
    """MCP tool for text processing with Azure OpenAI integration."""
    
    def __init__(self):
        metadata = ToolMetadata(
            name="text_processor",
            description="Process text using various operations including summarization, translation, and analysis",
            version="1.0.0",
            author="Word Add-in MCP Project",
            tags=["text", "ai", "openai", "processing", "nlp"],
            category="text_processing",
            input_schema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to process",
                        "minLength": 1,
                        "maxLength": 10000
                    },
                    "operation": {
                        "type": "string",
                        "description": "Processing operation to perform",
                        "enum": ["summarize", "translate", "analyze", "improve", "extract_keywords", "sentiment_analysis", "draft"],
                        "default": "summarize"
                    },
                    "language": {
                        "type": "string",
                        "description": "Target language for translation (ISO 639-1 code)",
                        "pattern": "^[a-z]{2}$",
                        "default": "en"
                    },
                    "max_length": {
                        "type": "integer",
                        "description": "Maximum length of output (for summarization)",
                        "minimum": 10,
                        "maximum": 1000,
                        "default": 200
                    },
                    "style": {
                        "type": "string",
                        "description": "Writing style for improvement",
                        "enum": ["formal", "casual", "academic", "creative", "technical"],
                        "default": "formal"
                    }
                },
                "required": ["text", "operation"]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "processed_text": {"type": "string"},
                    "operation": {"type": "string"},
                    "original_length": {"type": "integer"},
                    "processed_length": {"type": "integer"},
                    "processing_time": {"type": "number"},
                    "confidence_score": {"type": "number"},
                    "metadata": {"type": "object"}
                }
            },
            examples=[
                {
                    "input": {"text": "Long text here...", "operation": "summarize", "max_length": 100},
                    "output": "Summarized text with metadata"
                }
            ],
            rate_limit=50,  # 50 requests per minute
            timeout=60.0,   # 60 seconds
            requires_auth=True
        )
        super().__init__(metadata)
        
        # Azure OpenAI configuration
        self.azure_openai_configured = is_azure_openai_configured()
        self.max_retries = 3
        self.retry_delay = 1.0
        
        if self.azure_openai_configured:
            logger.info("Azure OpenAI configured for TextProcessorTool")
        else:
            logger.warning("Azure OpenAI not configured - TextProcessorTool will use fallback methods")
    
    async def execute(self, context: ToolExecutionContext) -> ToolExecutionResult:
        """Execute the text processing operation."""
        start_time = time.time()
        
        try:
            # Extract parameters
            text = context.parameters.get("text", "")
            operation = context.parameters.get("operation", "summarize")
            language = context.parameters.get("language", "en")
            max_length = context.parameters.get("max_length", 200)
            style = context.parameters.get("style", "formal")
            
            # Validate input text
            if not text or len(text.strip()) == 0:
                return ToolExecutionResult(
                    status=ToolExecutionStatus.FAILED,
                    error_code=ToolErrorCode.INVALID_PARAMETERS,
                    error_message="Text input is required and cannot be empty",
                    error_details={"text_length": len(text) if text else 0}
                )
            
            # Process text based on operation
            if operation == "summarize":
                result = await self._summarize_text(text, max_length)
            elif operation == "translate":
                result = await self._translate_text(text, language)
            elif operation == "analyze":
                result = await self._analyze_text(text)
            elif operation == "improve":
                result = await self._improve_text(text, style)
            elif operation == "extract_keywords":
                result = await self._extract_keywords(text)
            elif operation == "sentiment_analysis":
                result = await self._analyze_sentiment(text)
            elif operation == "draft":
                result = await self._draft_content(text)
            else:
                return ToolExecutionResult(
                    status=ToolExecutionStatus.FAILED,
                    error_code=ToolErrorCode.INVALID_PARAMETERS,
                    error_message=f"Unknown operation: {operation}",
                    error_details={"supported_operations": ["summarize", "translate", "analyze", "improve", "extract_keywords", "sentiment_analysis", "draft"]}
                )
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Prepare result
            return ToolExecutionResult(
                status=ToolExecutionStatus.SUCCESS,
                data={
                    "processed_text": result["text"],
                    "operation": operation,
                    "original_length": len(text),
                    "processed_length": len(result["text"]),
                    "processing_time": processing_time,
                    "confidence_score": result.get("confidence", 0.8),
                    "metadata": result.get("metadata", {})
                }
            )
            
        except Exception as e:
            logger.error("Text processing failed", 
                        operation=context.parameters.get("operation"),
                        error=str(e))
            
            return ToolExecutionResult(
                status=ToolExecutionStatus.FAILED,
                error_code=ToolErrorCode.EXECUTION_FAILED,
                error_message=f"Text processing failed: {str(e)}",
                error_details={"operation": context.parameters.get("operation"), "error": str(e)}
            )
    
    async def _summarize_text(self, text: str, max_length: int) -> Dict[str, Any]:
        """Summarize text to specified length using Azure OpenAI."""
        logger.info(f"Starting summarization for text: {text[:50]}...")
        logger.info(f"Azure OpenAI configured: {is_azure_openai_configured()}")
        logger.info(f"LLM client available: {llm_client.is_available()}")
        
        try:
            # Check if Azure OpenAI is available
            if not is_azure_openai_configured():
                logger.warning("Azure OpenAI not configured, falling back to simple summarization")
                return await self._fallback_summarize_text(text, max_length)
            
            logger.info("Using Azure OpenAI for summarization")
            # Use real LLM client for summarization
            result = llm_client.summarize_text(
                text=text,
                summary_type="concise",
                max_length=max_length
            )
            
            logger.info(f"LLM result: {result}")
            
            if result.get("success"):
                return {
                    "text": result["summary"],
                    "confidence": 0.95,
                    "metadata": {
                        "method": "ai_powered",
                        "model": llm_client.get_model_info()["model"],
                        "usage": result.get("usage", {}),
                        "compression_ratio": len(result["summary"]) / len(text)
                    }
                }
            else:
                logger.error(f"LLM summarization failed: {result.get('error')}")
                return await self._fallback_summarize_text(text, max_length)
                
        except Exception as e:
            logger.error(f"Error in AI summarization: {str(e)}")
            return await self._fallback_summarize_text(text, max_length)
    
    async def _fallback_summarize_text(self, text: str, max_length: int) -> Dict[str, Any]:
        """Fallback summarization when AI is not available."""
        return {
            "text": f"AI summarization unavailable. Original text ({len(text)} chars): {text[:100]}{'...' if len(text) > 100 else ''}",
            "confidence": 0.0,
            "metadata": {
                "method": "fallback_disabled",
                "error": "AI service unavailable"
            }
        }
    
    async def _translate_text(self, text: str, target_language: str) -> Dict[str, Any]:
        """Translate text to target language using Azure OpenAI."""
        try:
            # Check if Azure OpenAI is available
            if not is_azure_openai_configured():
                logger.warning("Azure OpenAI not configured, falling back to placeholder translation")
                return await self._fallback_translate_text(text, target_language)
            
            # Use real LLM client for translation
            result = llm_client.translate_text(text, target_language)
            
            if result.get("success"):
                return {
                    "text": result["translated_text"],
                    "confidence": 0.95,
                    "metadata": {
                        "method": "ai_powered",
                        "model": llm_client.get_model_info()["model"],
                        "usage": result.get("usage", {}),
                        "source_language": result["source_language"],
                        "target_language": result["target_language"],
                        "translation_method": "ai_translation"
                    }
                }
            else:
                logger.error(f"LLM translation failed: {result.get('error')}")
                return await self._fallback_translate_text(text, target_language)
                
        except Exception as e:
            logger.error(f"Error in AI translation: {str(e)}")
            return await self._fallback_translate_text(text, target_language)
    
    async def _fallback_translate_text(self, text: str, target_language: str) -> Dict[str, Any]:
        """Fallback translation when AI is not available."""
        return {
            "text": f"AI translation to {target_language} unavailable. Original text: {text}",
            "confidence": 0.0,
            "metadata": {
                "method": "fallback_disabled",
                "error": "AI service unavailable"
            }
        }
    
    async def _analyze_text(self, text: str) -> Dict[str, Any]:
        """Analyze text for various metrics using Azure OpenAI."""
        try:
            # Check if Azure OpenAI is available
            if not is_azure_openai_configured():
                logger.warning("Azure OpenAI not configured, falling back to simple analysis")
                return await self._fallback_analyze_text(text)
            
            # Use real LLM client for text analysis
            result = llm_client.analyze_readability(text)
            
            if result.get("success"):
                return {
                    "text": result["analysis"],
                    "confidence": 0.95,
                    "metadata": {
                        "method": "ai_powered",
                        "model": llm_client.get_model_info()["model"],
                        "usage": result.get("usage", {}),
                        "analysis_type": "comprehensive"
                    }
                }
            else:
                logger.error(f"LLM analysis failed: {result.get('error')}")
                return await self._fallback_analyze_text(text)
                
        except Exception as e:
            logger.error(f"Error in AI analysis: {str(e)}")
            return await self._fallback_analyze_text(text)
    
    async def _fallback_analyze_text(self, text: str) -> Dict[str, Any]:
        """Fallback text analysis when AI is not available."""
        return {
            "text": f"AI text analysis unavailable. Basic stats: {len(text.split())} words, {len(text)} characters",
            "confidence": 0.0,
            "metadata": {
                "method": "fallback_disabled",
                "error": "AI service unavailable"
            }
        }
    
    async def _improve_text(self, text: str, style: str) -> Dict[str, Any]:
        """Improve text according to specified style using Azure OpenAI."""
        try:
            # Check if Azure OpenAI is available
            if not is_azure_openai_configured():
                logger.warning("Azure OpenAI not configured, falling back to placeholder improvement")
                return await self._fallback_improve_text(text, style)
            
            # Create prompt for text improvement
            prompt = f"""
            Please improve the following text to match the {style} writing style.
            Make it more professional, clear, and engaging while maintaining the original meaning.
            
            Text: {text}
            
            Improved text in {style} style:
            """
            
            # Use real LLM client for text improvement
            result = llm_client.generate_text(
                prompt=prompt,
                max_tokens=len(text) * 2,
                temperature=0.7,
                system_message=f"You are an expert at improving text to match the {style} writing style."
            )
            
            if result.get("success"):
                return {
                    "text": result["text"],
                    "confidence": 0.95,
                    "metadata": {
                        "method": "ai_powered",
                        "model": llm_client.get_model_info()["model"],
                        "usage": result.get("usage", {}),
                        "style_applied": style,
                        "improvement_type": "ai_enhanced_style_adaptation"
                    }
                }
            else:
                logger.error(f"LLM text improvement failed: {result.get('error')}")
                return await self._fallback_improve_text(text, style)
                
        except Exception as e:
            logger.error(f"Error in AI text improvement: {str(e)}")
            return await self._fallback_improve_text(text, style)
    
    async def _fallback_improve_text(self, text: str, style: str) -> Dict[str, Any]:
        """Fallback text improvement when AI is not available."""
        return {
            "text": f"AI text improvement to {style} style unavailable. Original text: {text}",
            "confidence": 0.0,
            "metadata": {
                "method": "fallback_disabled",
                "error": "AI service unavailable"
            }
        }
    
    async def _extract_keywords(self, text: str) -> Dict[str, Any]:
        """Extract keywords from text using Azure OpenAI."""
        try:
            # Check if Azure OpenAI is available
            if not is_azure_openai_configured():
                logger.warning("Azure OpenAI not configured, falling back to simple keyword extraction")
                return await self._fallback_extract_keywords(text)
            
            # Use real LLM client for keyword extraction
            result = llm_client.extract_keywords(text, max_keywords=10)
            
            if result.get("success"):
                return {
                    "text": f"Keywords: {', '.join(result['keywords'])}",
                    "confidence": 0.95,
                    "metadata": {
                        "method": "ai_powered",
                        "model": llm_client.get_model_info()["model"],
                        "usage": result.get("usage", {}),
                        "keyword_count": result["count"],
                        "extraction_method": "ai_analysis"
                    }
                }
            else:
                logger.error(f"LLM keyword extraction failed: {result.get('error')}")
                return await self._fallback_extract_keywords(text)
                
        except Exception as e:
            logger.error(f"Error in AI keyword extraction: {str(e)}")
            return await self._fallback_extract_keywords(text)
    
    async def _fallback_extract_keywords(self, text: str) -> Dict[str, Any]:
        """Fallback keyword extraction when AI is not available."""
        return {
            "text": f"AI keyword extraction unavailable. Text length: {len(text)} characters",
            "confidence": 0.0,
            "metadata": {
                "method": "fallback_disabled",
                "error": "AI service unavailable"
            }
        }
    
    async def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze text sentiment using Azure OpenAI."""
        try:
            # Check if Azure OpenAI is available
            if not is_azure_openai_configured():
                logger.warning("Azure OpenAI not configured, falling back to simple sentiment analysis")
                return await self._fallback_analyze_sentiment(text)
            
            # Use real LLM client for sentiment analysis
            result = llm_client.analyze_sentiment(text)
            
            if result.get("success"):
                return {
                    "text": result["analysis"],
                    "confidence": 0.95,
                    "metadata": {
                        "method": "ai_powered",
                        "model": llm_client.get_model_info()["model"],
                        "usage": result.get("usage", {}),
                        "analysis_method": "ai_analysis"
                    }
                }
            else:
                logger.error(f"LLM sentiment analysis failed: {result.get('error')}")
                return await self._fallback_analyze_sentiment(text)
                
        except Exception as e:
            logger.error(f"Error in AI sentiment analysis: {str(e)}")
            return await self._fallback_analyze_sentiment(text)
    
    async def _fallback_analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Fallback sentiment analysis when AI is not available."""
        return {
            "text": f"AI sentiment analysis unavailable. Text length: {len(text)} characters",
            "confidence": 0.0,
            "metadata": {
                "method": "fallback_disabled",
                "error": "AI service unavailable"
            }
        }
    
    def get_azure_openai_status(self) -> Dict[str, Any]:
        """Get Azure OpenAI integration status."""
        if self.azure_openai_configured:
            model_info = llm_client.get_model_info()
            return {
                "configured": True,
                "max_retries": self.max_retries,
                "retry_delay": self.retry_delay,
                "model": model_info.get("model"),
                "endpoint": model_info.get("endpoint"),
                "supported_operations": [
                    "summarize", "translate", "analyze", 
                    "improve", "extract_keywords", "sentiment_analysis", "draft"
                ]
            }
        else:
            return {
                "configured": False,
                "max_retries": self.max_retries,
                "retry_delay": self.retry_delay,
                "supported_operations": [
                    "summarize", "translate", "analyze", 
                    "improve", "extract_keywords", "sentiment_analysis", "draft"
                ]
            }
    
    async def _draft_content(self, text: str) -> Dict[str, Any]:
        """Draft content based on user input using Azure OpenAI."""
        logger.info(f"Starting content drafting for input: {text[:50]}...")
        
        try:
            # Check if Azure OpenAI is available
            if not is_azure_openai_configured():
                logger.warning("Azure OpenAI not configured, falling back to simple drafting")
                return await self._fallback_draft_content(text)
            
            logger.info("Using Azure OpenAI for content drafting")
            
            # Create a prompt for content drafting
            prompt = f"""Based on the following user request, draft appropriate content:

User Request: {text}

Please provide a well-structured, professional response that addresses the user's needs. If this is a request for patent claims, draft them in proper patent claim format. If it's for other content, provide appropriate formatting and structure.

Response:"""
            
            # Use real LLM client for content drafting
            result = llm_client.generate_text(
                prompt=prompt,
                max_tokens=1000,
                temperature=0.7
            )
            
            logger.info(f"LLM drafting result: {result}")
            
            if result.get("success"):
                return {
                    "text": result["text"],
                    "confidence": 0.95,
                    "metadata": {
                        "method": "ai_powered",
                        "model": llm_client.get_model_info()["model"],
                        "usage": result.get("usage", {}),
                        "drafting_type": "ai_generated"
                    }
                }
            else:
                logger.error(f"LLM content drafting failed: {result.get('error')}")
                return await self._fallback_draft_content(text)
                
        except Exception as e:
            logger.error(f"Error in AI content drafting: {str(e)}")
            return await self._fallback_draft_content(text)
    
    async def _fallback_draft_content(self, text: str) -> Dict[str, Any]:
        """Fallback content drafting when AI is not available."""
        return {
            "text": f"AI content drafting unavailable. User request: {text}\n\nPlease try again when AI services are available.",
            "confidence": 0.0,
            "metadata": {
                "method": "fallback_disabled",
                "error": "AI service unavailable"
            }
        }
