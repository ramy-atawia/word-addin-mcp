"""
LLM Client Service

Handles communication with Azure OpenAI and other LLM providers.
Provides a unified interface for text generation, summarization, and analysis.
"""

import os
import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import openai
from openai import AzureOpenAI
import json

logger = logging.getLogger(__name__)


class LLMClient:
    """Client for interacting with Large Language Models."""
    
    def __init__(self, azure_openai_api_key: Optional[str] = None,
                 azure_openai_endpoint: Optional[str] = None,
                 azure_openai_deployment: Optional[str] = None,
                 azure_openai_api_version: Optional[str] = None,
                 model_name: str = "gpt-4"):
        """
        Initialize the LLM client.
        
        Args:
            azure_openai_api_key: Azure OpenAI API key
            azure_openai_endpoint: Azure OpenAI endpoint URL
            azure_openai_deployment: Azure OpenAI deployment name
            azure_openai_api_version: Azure OpenAI API version
            model_name: Model name to use
        """
        self.azure_openai_api_key = azure_openai_api_key
        self.azure_openai_endpoint = azure_openai_endpoint
        self.azure_openai_deployment = azure_openai_deployment
        self.azure_openai_api_version = azure_openai_api_version
        self.model_name = model_name
        
        # Initialize Azure OpenAI client
        if azure_openai_api_key and azure_openai_endpoint:
            try:
                self.client = AzureOpenAI(
                    api_key=azure_openai_api_key,
                    api_version=azure_openai_api_version or "2024-12-01-preview",
                    azure_endpoint=azure_openai_endpoint,
                    timeout=300.0
                )
                self.azure_openai_deployment = azure_openai_deployment or "gpt-5-nano"
                self.azure_deployment = azure_openai_deployment or "gpt-5-nano"
                self.llm_available = True
                logger.info(f"Azure OpenAI client initialized with deployment: {self.azure_deployment}")
            except Exception as e:
                logger.error(f"Failed to initialize Azure OpenAI client: {str(e)}")
                self.client = None
                self.llm_available = False
        else:
            self.client = None
            self.llm_available = False
            logger.warning("Azure OpenAI not configured - LLM features disabled")
    
    def generate_text_stream(self, prompt: str, max_tokens: int = 1000, 
                           system_message: Optional[str] = None, 
                           max_retries: int = 3):
        """
        Generate text using the LLM with streaming.
        
        Args:
            prompt: User prompt
            max_tokens: Maximum tokens to generate
            system_message: Optional system message
            
        Yields:
            Dictionary containing streaming text chunks and metadata
        """
        try:
            if not self.llm_available:
                yield self._create_error_result("LLM not available")
                return
            
            # Prepare messages
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})
            
            # Make streaming API call with retry logic
            last_error = None
            for attempt in range(max_retries):
                try:
                    # GPT-5-nano only supports default temperature
                    api_params = {
                        "model": self.azure_deployment,
                        "messages": messages,
                        "max_completion_tokens": max_tokens,
                        "stream": True
                    }
                    
                    response = self.client.chat.completions.create(**api_params)
                    break  # Success, exit retry loop
                except Exception as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        logger.warning(f"LLM streaming API call failed (attempt {attempt + 1}/{max_retries}): {str(e)}")
                        import time
                        time.sleep(2 ** attempt)  # Exponential backoff
                    else:
                        yield self._create_error_result(f"LLM streaming failed after {max_retries} attempts: {str(e)}")
                        return
            
            # Stream the response
            full_content = ""
            for chunk in response:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content:
                        full_content += delta.content
                        yield {
                            "success": True,
                            "text": delta.content,
                            "full_text": full_content,
                            "is_streaming": True,
                            "timestamp": datetime.now().isoformat()
                        }
            
            # Send final completion event
            yield {
                "success": True,
                "text": "",
                "full_text": full_content,
                "is_streaming": False,
                "is_complete": True,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"LLM streaming error: {str(e)}")
            yield self._create_error_result(f"LLM streaming error: {str(e)}")

    def generate_text(self, prompt: str, max_tokens: int = 1000, 
                     system_message: Optional[str] = None, 
                     max_retries: int = 3) -> Dict[str, Any]:
        """
        Generate text using the LLM.
        
        Args:
            prompt: User prompt
            max_tokens: Maximum tokens to generate
            system_message: Optional system message
            
        Returns:
            Dictionary containing generated text and metadata
        """
        try:
            if not self.llm_available:
                return self._create_error_result("LLM not available")
            
            # Prepare messages
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})
            
            # Make API call with retry logic
            last_error = None
            for attempt in range(max_retries):
                try:
                    # Standard configuration for text generation
                    api_params = {
                        "model": self.azure_openai_deployment,
                        "messages": messages,
                        "max_completion_tokens": max_tokens
                    }

                    # Log token limits for debugging
                    logger.debug(f"Model: {self.azure_openai_deployment}, Requested tokens: {max_tokens}")
                    if logger.isEnabledFor(logging.DEBUG):
                        logger.debug(f"API params: {api_params}")
                    
                    response = self.client.chat.completions.create(**api_params)
                    break  # Success, exit retry loop
                except Exception as e:
                    last_error = e
                    logger.error(f"API call failed (attempt {attempt + 1}/{max_retries}): {str(e)}")
                    if attempt < max_retries - 1:
                        logger.warning(f"LLM API call failed (attempt {attempt + 1}/{max_retries}): {str(e)}")
                        import time
                        time.sleep(2 ** attempt)  # Exponential backoff
                    else:
                        raise e
            
            # Debug logging
            logger.info(f"Azure OpenAI response type: {type(response)}")
            logger.info(f"Response choices: {response.choices}")
            logger.info(f"First choice message content type: {type(response.choices[0].message.content)}")
            logger.info(f"First choice message content: {response.choices[0].message.content}")
            
            # Extract response
            generated_text = response.choices[0].message.content
            usage = response.usage
            
            return {
                "success": True,
                "text": generated_text,
                "usage": {
                    "prompt_tokens": usage.prompt_tokens,
                    "completion_tokens": usage.completion_tokens,
                    "total_tokens": usage.total_tokens
                },
                "model": self.azure_openai_deployment,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating text: {str(e)}")
            return self._create_error_result(f"Text generation failed: {str(e)}")
    
    def summarize_text(self, text: str, summary_type: str = "concise", 
                      max_length: Optional[int] = None) -> Dict[str, Any]:
        """
        Summarize text using the LLM.
        
        Args:
            text: Text to summarize
            summary_type: Type of summary (concise, detailed, bullet_points)
            max_length: Maximum length of summary
            
        Returns:
            Dictionary containing summary and metadata
        """
        try:
            if not self.llm_available:
                return self._create_error_result("LLM not available")
            
            # Create appropriate prompt based on summary type
            if summary_type == "concise":
                prompt = f"Please provide a concise summary (2-3 sentences) of the following text:\n\n{text}"
            elif summary_type == "detailed":
                prompt = f"Please provide a detailed summary of the following text:\n\n{text}"
            elif summary_type == "bullet_points":
                prompt = f"Please provide a bullet-point summary of the key points from the following text:\n\n{text}"
            else:
                prompt = f"Please summarize the following text:\n\n{text}"
            
            # Add length constraint if specified
            if max_length:
                prompt += f"\n\nPlease keep the summary under {max_length} words."
            
            # Generate summary
            result = self.generate_text(
                prompt=prompt,
                max_tokens=500,
                system_message="You are an expert at summarizing text. Provide clear, accurate summaries."
            )
            
            if result.get("success"):
                return {
                    "success": True,
                    "summary": result["text"],
                    "summary_type": summary_type,
                    "original_length": len(text),
                    "summary_length": len(result["text"]),
                    "usage": result.get("usage", {}),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Error summarizing text: {str(e)}")
            return self._create_error_result(f"Summarization failed: {str(e)}")
    
    def extract_keywords(self, text: str, max_keywords: int = 10) -> Dict[str, Any]:
        """
        Extract keywords from text using the LLM.
        
        Args:
            text: Text to analyze
            max_keywords: Maximum number of keywords to extract
            
        Returns:
            Dictionary containing keywords and metadata
        """
        try:
            if not self.llm_available:
                return self._create_error_result("LLM not available")
            
            prompt = f"""
            Please extract the {max_keywords} most important keywords from the following text.
            Return only the keywords, separated by commas.
            
            Text: {text[:2000]}...
            
            Keywords:
            """
            
            result = self.generate_text(
                prompt=prompt,
                max_tokens=200,
                system_message="You are an expert at keyword extraction. Return only the keywords, separated by commas."
            )
            
            if result.get("success"):
                # Parse keywords
                keywords_text = result["text"].strip()
                keywords = [kw.strip() for kw in keywords_text.split(",") if kw.strip()]
                
                return {
                    "success": True,
                    "keywords": keywords,
                    "count": len(keywords),
                    "usage": result.get("usage", {}),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Error extracting keywords: {str(e)}")
            return self._create_error_result(f"Keyword extraction failed: {str(e)}")
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Analyze sentiment of text using the LLM.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary containing sentiment analysis
        """
        try:
            if not self.llm_available:
                return self._create_error_result("LLM not available")
            
            prompt = f"""
            Analyze the sentiment of the following text. Provide:
            1. Overall sentiment (Positive, Negative, Neutral, Mixed)
            2. Sentiment score (-1 to 1, where -1 is very negative, 1 is very positive)
            3. Key emotional indicators
            4. Confidence level (High, Medium, Low)
            
            Text: {text[:1500]}...
            
            Please format your response as:
            Sentiment: [overall sentiment]
            Score: [sentiment score]
            Indicators: [emotional indicators]
            Confidence: [confidence level]
            """
            
            result = self.generate_text(
                prompt=prompt,
                max_tokens=200,
                system_message="You are an expert at sentiment analysis. Provide structured, accurate analysis."
            )
            
            if result.get("success"):
                return {
                    "success": True,
                    "analysis": result["text"],
                    "usage": result.get("usage", {}),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {str(e)}")
            return self._create_error_result(f"Sentiment analysis failed: {str(e)}")
    
    def analyze_readability(self, text: str) -> Dict[str, Any]:
        """
        Analyze readability of text using the LLM.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary containing readability analysis
        """
        try:
            if not self.llm_available:
                return self._create_error_result("LLM not available")
            
            prompt = f"""
            Analyze the readability of the following text. Provide:
            1. Readability level (e.g., Elementary, High School, College, Graduate)
            2. Complexity score (1-10, where 1 is very simple, 10 is very complex)
            3. Target audience
            4. Suggestions for improvement
            
            Text: {text[:1500]}...
            
            Please format your response as:
            Level: [readability level]
            Complexity: [score]/10
            Audience: [target audience]
            Suggestions: [improvement suggestions]
            """
            
            result = self.generate_text(
                prompt=prompt,
                max_tokens=200,
                system_message="You are an expert at readability analysis. Provide structured, accurate analysis."
            )
            
            if result.get("success"):
                return {
                    "success": True,
                    "analysis": result["text"],
                    "usage": result.get("usage", {}),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Error analyzing readability: {str(e)}")
            return self._create_error_result(f"Readability analysis failed: {str(e)}")
    
    def compare_texts(self, text1: str, text2: str, comparison_type: str = "general") -> Dict[str, Any]:
        """
        Compare two texts using the LLM.
        
        Args:
            text1: First text
            text2: Second text
            comparison_type: Type of comparison (general, similarity, differences)
            
        Returns:
            Dictionary containing comparison analysis
        """
        try:
            if not self.llm_available:
                return self._create_error_result("LLM not available")
            
            # Create appropriate prompt based on comparison type
            if comparison_type == "similarity":
                prompt = f"""
                Analyze the similarity between these two texts. Provide:
                1. Similarity score (0-100%)
                2. Key similarities
                3. Key differences
                4. Overall assessment
                
                Text 1: {text1[:1000]}...
                Text 2: {text2[:1000]}...
                """
            elif comparison_type == "differences":
                prompt = f"""
                Analyze the differences between these two texts. Provide:
                1. Key differences
                2. Areas of disagreement
                3. Unique aspects of each text
                4. Overall assessment
                
                Text 1: {text1[:1000]}...
                Text 2: {text2[:1000]}...
                """
            else:  # general comparison
                prompt = f"""
                Compare these two texts. Provide:
                1. Key similarities
                2. Key differences
                3. Relative strengths and weaknesses
                4. Overall assessment
                
                Text 1: {text1[:1000]}...
                Text 2: {text2[:1000]}...
                """
            
            result = self.generate_text(
                prompt=prompt,
                max_tokens=400,
                system_message="You are an expert at text comparison. Provide structured, accurate analysis."
            )
            
            if result.get("success"):
                return {
                    "success": True,
                    "comparison": result["text"],
                    "comparison_type": comparison_type,
                    "usage": result.get("usage", {}),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Error comparing texts: {str(e)}")
            return self._create_error_result(f"Text comparison failed: {str(e)}")
    
    def translate_text(self, text: str, target_language: str, source_language: Optional[str] = None) -> Dict[str, Any]:
        """
        Translate text using the LLM.
        
        Args:
            text: Text to translate
            target_language: Target language
            source_language: Source language (optional, auto-detect if not specified)
            
        Returns:
            Dictionary containing translated text
        """
        try:
            if not self.llm_available:
                return self._create_error_result("LLM not available")
            
            if source_language:
                prompt = f"Translate the following text from {source_language} to {target_language}:\n\n{text}"
            else:
                prompt = f"Translate the following text to {target_language}:\n\n{text}"
            
            result = self.generate_text(
                prompt=prompt,
                max_tokens=len(text) * 2,  # Allow for longer translations
                system_message=f"You are an expert translator. Provide accurate translation to {target_language}."
            )
            
            if result.get("success"):
                return {
                    "success": True,
                    "translated_text": result["text"],
                    "source_language": source_language or "auto-detected",
                    "target_language": target_language,
                    "original_length": len(text),
                    "translated_length": len(result["text"]),
                    "usage": result.get("usage", {}),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"Error translating text: {str(e)}")
            return self._create_error_result(f"Translation failed: {str(e)}")
    
    def is_available(self) -> bool:
        """Check if LLM is available."""
        return self.llm_available
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        return {
            "available": self.llm_available,
            "provider": "Azure OpenAI" if self.llm_available else "None",
            "model": self.azure_openai_deployment if self.llm_available else "None",
            "endpoint": self.azure_openai_endpoint if self.llm_available else "None"
        }
    
    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """Create standardized error result."""
        return {
            "success": False,
            "error": error_message,
            "timestamp": datetime.now().isoformat()
        }


# Global instance for easy access
def create_llm_client():
    """Create LLM client with environment configuration."""
    try:
        from ..core.config import get_azure_openai_config, is_azure_openai_configured
    except ImportError:
        # Fallback to absolute import if relative fails
        try:
            from app.core.config import get_azure_openai_config, is_azure_openai_configured
        except ImportError:
            logger.error("Failed to import config functions")
            return LLMClient()
    
    if is_azure_openai_configured():
        config = get_azure_openai_config()
        return LLMClient(
            azure_openai_api_key=config['api_key'],
            azure_openai_endpoint=config['endpoint'],
            azure_openai_deployment=config['deployment'],
            azure_openai_api_version=config['api_version']
        )
    else:
        logger.warning("Azure OpenAI not configured - creating LLM client without credentials")
        return LLMClient()

# Lazy-loaded global instance to avoid import errors
_llm_client_instance = None

def get_llm_client():
    """Get the LLM client instance, creating it if necessary."""
    global _llm_client_instance
    if _llm_client_instance is None:
        _llm_client_instance = create_llm_client()
    return _llm_client_instance

# Don't create instance at module level - let it be created when needed
