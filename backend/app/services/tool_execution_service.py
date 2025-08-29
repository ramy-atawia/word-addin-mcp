"""
Tool Execution Service for Word Add-in MCP Project.

This service handles the execution of all MCP tools, providing a clean
separation between API layer and business logic.
"""

import time
from typing import Dict, Any, Optional
import structlog

from app.services.validation_service import validation_service
from app.services.llm_client import llm_client
from app.core.config import is_azure_openai_configured, settings
from app.core.mcp_tool_interface import ToolExecutionContext, ToolExecutionStatus

logger = structlog.get_logger()


class ToolExecutionService:
    """Service for executing MCP tools with proper validation and error handling."""
    
    def __init__(self):
        self.azure_openai_configured = is_azure_openai_configured()
        
    async def execute_file_reader(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute file reader tool."""
        try:
            # Validate parameters
            is_valid, error_message, sanitized_params = validation_service.validate_file_reader_params(parameters)
            if not is_valid:
                return {
                    "status": "error",
                    "error_message": error_message,
                    "error_type": "validation_error"
                }
            
            # Import LLM client for real AI processing
            from app.services.llm_client import llm_client
            from app.core.config import is_azure_openai_configured
            
            # Check if Azure OpenAI is available
            if not is_azure_openai_configured():
                return {
                    "status": "error",
                    "error_message": "Azure OpenAI not configured",
                    "error_type": "configuration_error"
                }
            
            # Get file path and parameters
            file_path = sanitized_params['path']
            encoding = sanitized_params.get('encoding', 'utf-8')
            max_size = sanitized_params.get('max_size', 1048576)
            
            logger.info(f"Executing file reader", 
                       file_path=file_path, 
                       encoding=encoding,
                       max_size=max_size)
            
            # TODO: Implement actual file reading logic
            # For now, return a placeholder
            return {
                "status": "success",
                "file_path": file_path,
                "content": f"File content from {file_path} (placeholder)",
                "encoding": encoding,
                "file_size": 0,
                "read_time": time.time()
            }
            
        except Exception as e:
            logger.error(f"File reader execution failed: {str(e)}")
            return {
                "status": "error",
                "error_message": f"File reading failed: {str(e)}",
                "error_type": "execution_error"
            }
    
    async def execute_text_processor(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute text processor tool with Azure OpenAI LLM."""
        try:
            # Validate parameters
            is_valid, error_message, sanitized_params = validation_service.validate_text_processor_params(parameters)
            if not is_valid:
                return {
                    "status": "error",
                    "error_message": error_message,
                    "error_type": "validation_error"
                }
            
            # Import LLM client for real AI processing
            from app.services.llm_client import llm_client
            from app.core.config import is_azure_openai_configured
            
            # Check if Azure OpenAI is available
            if not is_azure_openai_configured():
                return {
                    "status": "error",
                    "error_message": "Azure OpenAI not configured",
                    "error_type": "configuration_error"
                }
            
            # Get text and operation
            text = sanitized_params['text']
            operation = sanitized_params['operation']
            
            logger.info(f"Executing text processor with Azure OpenAI", 
                       operation=operation, 
                       text_length=len(text))
            
            # Execute real LLM processing based on operation
            if operation == "summarize":
                result = llm_client.summarize_text(
                    text=text,
                    summary_type="concise",
                    max_length=sanitized_params.get('max_length', 200)
                )
            elif operation == "extract_keywords":
                result = llm_client.extract_keywords(
                    text=text,
                    max_keywords=sanitized_params.get('max_keywords', 10)
                )
            elif operation == "sentiment_analysis":
                result = llm_client.analyze_sentiment(text)
            elif operation == "analyze":
                result = llm_client.analyze_readability(text)
            elif operation == "translate":
                target_lang = sanitized_params.get('target_language', 'en')
                result = llm_client.translate_text(text, target_lang)
            elif operation == "improve":
                style = sanitized_params.get('style', 'formal')
                # Create custom prompt for text improvement
                prompt = f"Please improve the following text to match the {style} writing style. Make it more professional, clear, and engaging while maintaining the original meaning.\n\nText: {text}\n\nImproved text:"
                result = llm_client.generate_text(
                    prompt=prompt,
                    max_tokens=len(text) * 2,
                    temperature=0.7
                )
            else:
                return {
                    "status": "error",
                    "error_message": f"Unsupported operation: {operation}",
                    "error_type": "validation_error"
                }
            
            # Check if LLM processing was successful
            if result.get("success"):
                # Extract the processed text based on operation
                if operation == "summarize":
                    processed_text = result["summary"]
                elif operation == "extract_keywords":
                    processed_text = f"Keywords: {', '.join(result['keywords'])}"
                elif operation == "sentiment_analysis":
                    processed_text = result["analysis"]
                elif operation == "analyze":
                    processed_text = result["analysis"]
                elif operation == "translate":
                    processed_text = result["translated_text"]
                elif operation == "improve":
                    processed_text = result["text"]
                else:
                    processed_text = str(result.get("text", result))
                
                logger.info(f"Text processor completed successfully", 
                           operation=operation, 
                           result_length=len(processed_text))
                
                return {
                    "status": "success",
                    "processed_text": processed_text,
                    "operation": operation,
                    "original_length": len(text),
                    "processed_length": len(processed_text),
                    "target_language": sanitized_params.get('target_language'),
                    "max_keywords": sanitized_params.get('max_keywords'),
                    "ai_model": llm_client.get_model_info()["model"],
                    "usage": result.get("usage", {}),
                    "confidence": result.get("confidence", 0.95)
                }
            else:
                return {
                    "status": "error",
                    "error_message": "LLM processing failed",
                    "error_type": "llm_error"
                }
                
        except Exception as e:
            logger.error(f"Text processor execution failed: {str(e)}")
            return {
                "status": "error",
                "error_message": f"Text processing failed: {str(e)}",
                "error_type": "execution_error"
            }
    
    async def execute_document_analyzer(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute document analyzer tool with Azure OpenAI LLM."""
        try:
            # Validate parameters
            is_valid, error_message, sanitized_params = validation_service.validate_document_analyzer_params(parameters)
            if not is_valid:
                return {
                    "status": "error",
                    "error_message": error_message,
                    "error_type": "validation_error"
                }
            
            # Import LLM client for real AI processing
            from app.services.llm_client import llm_client
            from app.core.config import is_azure_openai_configured
            
            # Check if Azure OpenAI is available
            if not is_azure_openai_configured():
                return {
                    "status": "error",
                    "error_message": "Azure OpenAI not configured",
                    "error_type": "configuration_error"
                }
            
            # Get content and analysis type
            content = sanitized_params['text']
            analysis_type = sanitized_params['analysis_type']
            
            logger.info(f"Executing document analyzer with Azure OpenAI", 
                       analysis_type=analysis_type, 
                       content_length=len(content))
            
            # Execute real LLM processing based on analysis type
            if analysis_type == "readability":
                result = llm_client.analyze_readability(content)
            elif analysis_type == "structure":
                result = llm_client.analyze_structure(content)
            elif analysis_type == "tone":
                result = llm_client.analyze_tone(content)
            elif analysis_type == "summary":
                result = llm_client.summarize_text(
                    text=content,
                    summary_type="comprehensive",
                    max_length=sanitized_params.get('max_length', 500)
                )
            elif analysis_type == "keyword_extraction":
                result = llm_client.extract_keywords(
                    text=content,
                    max_keywords=sanitized_params.get('max_keywords', 20)
                )
            else:
                return {
                    "status": "error",
                    "error_message": f"Unsupported analysis type: {analysis_type}",
                    "error_type": "validation_error"
                }
            
            # Check if LLM processing was successful
            if result.get("success"):
                # Extract the analysis result
                if analysis_type == "summary":
                    analysis_result = result["summary"]
                elif analysis_type == "keyword_extraction":
                    analysis_result = f"Keywords: {', '.join(result['keywords'])}"
                else:
                    analysis_result = result.get("analysis", str(result))
                
                logger.info(f"Document analyzer completed successfully", 
                           analysis_type=analysis_type, 
                           result_length=len(analysis_result))
                
                return {
                    "status": "success",
                    "analysis_result": analysis_result,
                    "analysis_type": analysis_type,
                    "content_length": len(content),
                    "result_length": len(analysis_result),
                    "ai_model": llm_client.get_model_info()["model"],
                    "usage": result.get("usage", {}),
                    "confidence": result.get("confidence", 0.95)
                }
            else:
                return {
                    "status": "error",
                    "error_message": "LLM processing failed",
                    "error_type": "llm_error"
                }
                
        except Exception as e:
            logger.error(f"Document analyzer execution failed: {str(e)}")
            return {
                "status": "error",
                "error_message": f"Document analysis failed: {str(e)}",
                "error_type": "execution_error"
            }
    
    async def execute_web_content_fetcher(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute web content fetcher tool using the enhanced tool directly."""
        try:
            # Validate parameters
            is_valid, error_message, sanitized_params = validation_service.validate_web_content_fetcher_params(parameters)
            if not is_valid:
                return {
                    "status": "error",
                    "error_message": error_message,
                    "error_type": "validation_error"
                }
            
            # Use the enhanced WebContentFetcherTool directly
            from app.tools.web_content_fetcher import WebContentFetcherTool
            
            # Create tool instance and execute
            tool = WebContentFetcherTool()
            context = ToolExecutionContext(
                parameters=sanitized_params,
                session_id=parameters.get('session_id', ''),
                request_id=parameters.get('request_id', ''),
                user_id=parameters.get('user_id', '')
            )
            
            result = await tool.execute(context)
            
            if result.status == ToolExecutionStatus.SUCCESS:
                return {
                    "status": "success",
                    "url": result.data.get("url", ""),
                    "query": result.data.get("query", ""),
                    "content": result.data.get("content", ""),
                    "content_type": result.data.get("content_type", "text/plain"),
                    "extraction_time": result.data.get("extraction_time", 0.0),
                    "ai_enhanced": result.data.get("ai_enhanced", False),
                    "source_type": result.data.get("source_type", "unknown")
                }
            else:
                return {
                    "status": "error",
                    "error_message": result.error_message or "Web content fetching failed",
                    "error_type": "execution_error"
                }
            
        except Exception as e:
            logger.error(f"Web content fetcher execution failed: {str(e)}")
            return {
                "status": "error",
                "error_message": f"Web content fetching failed: {str(e)}",
                "error_type": "execution_error"
            }
    
    async def execute_data_formatter(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute data formatter tool with real LLM processing."""
        try:
            # Validate parameters
            is_valid, error_message, sanitized_params = validation_service.validate_data_formatter_params(parameters)
            if not is_valid:
                return {
                    "status": "error",
                    "error_message": error_message,
                    "error_type": "validation_error"
                }
            
            # Simple LLM-based data formatting - direct implementation
            data = sanitized_params['data']
            output_format = sanitized_params['output_format']
            style = sanitized_params.get('style', 'simple')
            
            # Use LLM directly for intelligent formatting
            if is_azure_openai_configured() and llm_client:
                try:
                    prompt = f"""Format this data into {output_format.upper()} format.

Data to format:
{data}

Requirements:
- Convert to valid {output_format.upper()} format
- Style: {style} (keep it simple and clean)
- If the data appears structured (like a list or table), maintain that structure
- Output only the formatted data, no explanations

Format as {output_format}:"""

                    result = llm_client.generate_text(
                        prompt=prompt,
                        max_tokens=800,
                        temperature=0.2
                    )
                    
                    if result.get("success"):
                        formatted_data = result["text"].strip()
                        return {
                            "status": "success",
                            "output_format": output_format,
                            "formatted_data": formatted_data,
                            "input_length": len(str(data)),
                            "output_length": len(str(formatted_data)),
                            "content": formatted_data,
                            "ai_enhanced": True,
                            "style": style
                        }
                    else:
                        logger.warning("LLM formatting failed, using fallback")
                        return self._simple_fallback_formatting(data, output_format, style)
                        
                except Exception as e:
                    logger.warning(f"LLM formatting failed: {str(e)}, using fallback")
                    return self._simple_fallback_formatting(data, output_format, style)
            else:
                # LLM not available, use fallback
                return self._simple_fallback_formatting(data, output_format, style)
                
        except Exception as e:
            logger.error(f"Data formatter execution failed: {str(e)}")
            return {
                "status": "error",
                "error_message": f"Data formatting failed: {str(e)}",
                "error_type": "execution_error"
            }
    
    def _simple_fallback_formatting(self, data: str, output_format: str, style: str) -> Dict[str, Any]:
        """Simple fallback formatting when LLM is not available."""
        try:
            if output_format == "json":
                formatted_data = f'{{"content": "{data}", "format": "json"}}'
            elif output_format == "csv":
                formatted_data = f'"content","{data}"'
            elif output_format == "xml":
                formatted_data = f'<data><content>{data}</content></data>'
            elif output_format == "yaml":
                formatted_data = f'content: "{data}"\nformat: yaml'
            elif output_format == "table":
                formatted_data = f"| Content |\n|---------|\n| {data} |"
            elif output_format == "markdown":
                formatted_data = f"# Data Export\n\n{data}"
            else:
                formatted_data = str(data)
            
            return {
                "status": "success",
                "output_format": output_format,
                "formatted_data": formatted_data,
                "input_length": len(str(data)),
                "output_length": len(str(formatted_data)),
                "content": formatted_data,
                "ai_enhanced": False,
                "style": style
            }
            
        except Exception as e:
            logger.error(f"Fallback formatting failed: {str(e)}")
            return {
                "status": "error",
                "error_message": f"Fallback formatting failed: {str(e)}",
                "error_type": "execution_error"
            }


# Global instance for easy access
tool_execution_service = ToolExecutionService()
