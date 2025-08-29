"""
Enhanced Web Content Fetcher Tool for Word Add-in MCP Project.

This tool implements real web content fetching with:
- Real HTTP requests to URLs
- Google Search API integration
- LLM-powered content processing
- No mockups or placeholders
"""

import time
import aiohttp
import asyncio
from typing import Dict, Any, Optional, List
import structlog
from urllib.parse import urlparse, quote_plus
import json
import re
from html import unescape

from app.core.mcp_tool_interface import (
    BaseMCPTool,
    ToolMetadata,
    ToolExecutionContext,
    ToolExecutionResult,
    ToolExecutionStatus,
    ToolErrorCode
)
from app.services.llm_client import llm_client
from app.core.config import is_azure_openai_configured, settings

logger = structlog.get_logger()


class WebContentFetcherTool(BaseMCPTool):
    """Enhanced MCP tool for web content fetching with real HTTP and LLM processing."""
    
    def __init__(self):
        metadata = ToolMetadata(
            name="web_content_fetcher",
            description="Fetch and intelligently process web content using real HTTP requests and AI",
            version="2.0.0",
            author="Word Add-in MCP Project",
            tags=["web", "content", "extraction", "url", "search", "ai"],
            category="web_processing",
            input_schema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string", 
                        "description": "URL to fetch content from (optional if query provided)",
                        "format": "uri"
                    },
                    "query": {
                        "type": "string", 
                        "description": "Search query to find web content (optional if URL provided)",
                        "minLength": 1,
                        "maxLength": 500
                    },
                    "extract_type": {
                        "type": "string", 
                        "enum": ["text", "summary", "key_points", "full_content"], 
                        "default": "summary"
                    },
                    "max_length": {
                        "type": "integer", 
                        "description": "Maximum length of extracted content", 
                        "default": 500,
                        "minimum": 100,
                        "maximum": 5000
                    }
                },
                "anyOf": [
                    {"required": ["url"]},
                    {"required": ["query"]}
                ]
            },
            output_schema={
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "query": {"type": "string"},
                    "content": {"type": "string"},
                    "content_type": {"type": "string"},
                    "extraction_time": {"type": "number"},
                    "ai_enhanced": {"type": "boolean"},
                    "source_type": {"type": "string"},
                    "success": {"type": "boolean"},
                    "error_message": {"type": "string"}
                }
            }
        )
        super().__init__(metadata)
        
        # Configuration
        self.azure_openai_configured = is_azure_openai_configured()
        
        # Try to get Google API keys from settings first, then fallback to direct env loading
        self.google_api_key = getattr(settings, 'google_search_api_key', None)
        self.google_cse_id = getattr(settings, 'google_search_engine_id', None)
        
        # If not loaded from settings, try direct environment variable loading
        if not self.google_api_key or not self.google_cse_id:
            import os
            from dotenv import load_dotenv
            
            # Load .env file directly
            env_path = "/Users/Mariam/word-addin-mcp/.env"
            if os.path.exists(env_path):
                load_dotenv(env_path)
                self.google_api_key = os.getenv("GOOGLE_API_KEY")
                self.google_cse_id = os.getenv("GOOGLE_CSE_ID")
                logger.info(f"Loaded Google API keys directly from .env file")
        
        self.timeout = 30
        self.max_retries = 3
        self.max_content_size = 10 * 1024 * 1024  # 10MB limit
        
        # User agent for requests
        self.user_agent = 'Mozilla/5.0 (compatible; Word-Addin-MCP/2.0; +https://example.com/bot)'
        
        # Debug logging
        logger.info(f"WebContentFetcherTool initialization - google_api_key: {self.google_api_key[:10] if self.google_api_key else 'None'}..., google_cse_id: {self.google_cse_id[:10] if self.google_cse_id else 'None'}...")
        
        if self.azure_openai_configured:
            logger.info("Azure OpenAI configured for WebContentFetcherTool")
        if self.google_api_key and self.google_cse_id:
            logger.info("Google Search API configured for WebContentFetcherTool")
        else:
            logger.warning(f"Google Search API NOT configured - api_key: {bool(self.google_api_key)}, cse_id: {bool(self.google_cse_id)}")
    
    async def execute(self, context: ToolExecutionContext) -> ToolExecutionResult:
        """Execute web content fetching with real HTTP and LLM processing."""
        start_time = time.time()
        
        try:
            # Extract and validate parameters
            url = context.parameters.get("url", "").strip()
            query = context.parameters.get("query", "").strip()
            extract_type = context.parameters.get("extract_type", "summary")
            max_length = context.parameters.get("max_length", 500)
            
            # Validate input
            if not url and not query:
                return ToolExecutionResult(
                    status=ToolExecutionStatus.FAILED,
                    error_code=ToolErrorCode.INVALID_PARAMETERS,
                    error_message="Either URL or query is required"
                )
            
            # Validate max_length
            if not isinstance(max_length, int) or max_length < 100 or max_length > 5000:
                max_length = 500
            
            # Validate URL format if provided
            if url and not self._is_valid_url(url):
                return ToolExecutionResult(
                    status=ToolExecutionStatus.FAILED,
                    error_code=ToolErrorCode.INVALID_PARAMETERS,
                    error_message="Invalid URL format provided"
                )
            
            # Process based on input type
            if url:
                # Direct URL fetching
                result = await self._fetch_url_content(url, extract_type, max_length)
            else:
                # Search query processing
                result = await self._process_search_query(query, extract_type, max_length)
            
            # Calculate extraction time
            extraction_time = time.time() - start_time
            
            # Prepare result
            return ToolExecutionResult(
                status=ToolExecutionStatus.SUCCESS,
                data={
                    "url": result.get("url", url),
                    "query": query,
                    "content": result.get("content", ""),
                    "content_type": result.get("content_type", "text/plain"),
                    "extraction_time": round(extraction_time, 2),
                    "ai_enhanced": result.get("ai_enhanced", False),
                    "source_type": result.get("source_type", "direct_url" if url else "search_result"),
                    "success": True
                }
            )
            
        except Exception as e:
            logger.error("Web content fetching failed", 
                        url=context.parameters.get("url"),
                        query=context.parameters.get("query"),
                        error=str(e))
            
            return ToolExecutionResult(
                status=ToolExecutionStatus.FAILED,
                error_code=ToolErrorCode.EXECUTION_FAILED,
                error_message=f"Web content fetching failed: {str(e)}",
                data={
                    "success": False,
                    "error_message": str(e),
                    "extraction_time": round(time.time() - start_time, 2)
                }
            )
    
    def _is_valid_url(self, url: str) -> bool:
        """Validate URL format and security."""
        try:
            parsed = urlparse(url)
            
            # Check for required components
            if not parsed.scheme or not parsed.netloc:
                return False
            
            # Only allow HTTP/HTTPS
            if parsed.scheme not in ['http', 'https']:
                return False
            
            # Block localhost and private networks for security
            netloc = parsed.netloc.lower()
            blocked_hosts = ['localhost', '127.0.0.1', '0.0.0.0', '10.', '192.168.', '172.16.']
            if any(netloc.startswith(blocked) for blocked in blocked_hosts):
                return False
            
            return True
        except Exception:
            return False
    
    async def _fetch_url_content(self, url: str, extract_type: str, max_length: int) -> Dict[str, Any]:
        """Fetch content from a direct URL."""
        try:
            # Fetch content with retry logic
            content, content_type = await self._fetch_with_retry(url)
            
            # Process content based on extract type
            if extract_type == "text":
                processed_content = self._extract_text_content(content)
            elif extract_type == "summary":
                processed_content = await self._ai_summarize_content(content, max_length)
            elif extract_type == "key_points":
                processed_content = await self._ai_extract_key_points(content, max_length)
            elif extract_type == "full_content":
                processed_content = self._extract_text_content(content, truncate=False)
            else:
                processed_content = self._extract_text_content(content)
            
            # Truncation removed - let AI control the content length
            
            return {
                "url": url,
                "content": processed_content,
                "content_type": content_type or "text/plain",
                "ai_enhanced": extract_type in ["summary", "key_points"],
                "source_type": "direct_url"
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch URL content: {str(e)}")
            raise
    
    async def _process_search_query(self, query: str, extract_type: str, max_length: int) -> Dict[str, Any]:
        """Process a search query using Google Search API."""
        try:
            if not self.google_api_key or not self.google_cse_id:
                # Fallback to simple search simulation
                return await self._fallback_search(query, extract_type, max_length)
            
            # Use Google Search API
            search_results = await self._google_search(query)
            
            if not search_results:
                return await self._fallback_search(query, extract_type, max_length)
            
            # Get the first valid result and fetch its content
            for result in search_results[:3]:  # Try first 3 results
                result_url = result.get("link", "")
                if result_url and self._is_valid_url(result_url):
                    try:
                        content_result = await self._fetch_url_content(result_url, extract_type, max_length)
                        content_result["source_type"] = "search_result"
                        return content_result
                    except Exception as e:
                        logger.warning(f"Failed to fetch search result {result_url}: {str(e)}")
                        continue
            
            # If no results could be fetched, return fallback
            return await self._fallback_search(query, extract_type, max_length)
                
        except Exception as e:
            logger.error(f"Search query processing failed: {str(e)}")
            return await self._fallback_search(query, extract_type, max_length)
    
    async def _fetch_with_retry(self, url: str) -> tuple[str, str]:
        """Fetch content from URL with retry logic."""
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                connector = aiohttp.TCPConnector(
                    limit=10,
                    limit_per_host=5,
                    enable_cleanup_closed=True
                )
                
                timeout = aiohttp.ClientTimeout(
                    total=self.timeout,
                    connect=10,
                    sock_read=20
                )
                
                async with aiohttp.ClientSession(
                    connector=connector,
                    timeout=timeout
                ) as session:
                    headers = {
                        'User-Agent': self.user_agent,
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.5',
                        'Accept-Encoding': 'gzip, deflate',
                        'Connection': 'keep-alive'
                    }
                    
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            # Check content size
                            content_length = response.headers.get('content-length')
                            if content_length and int(content_length) > self.max_content_size:
                                raise Exception(f"Content too large: {content_length} bytes")
                            
                            content = await response.text(errors='ignore')
                            
                            # Additional size check after reading
                            if len(content) > self.max_content_size:
                                content = content[:self.max_content_size]
                            
                            content_type = response.headers.get('content-type', 'text/plain')
                            return content, content_type
                        
                        elif response.status in [301, 302, 303, 307, 308]:
                            # Handle redirects manually if needed
                            redirect_url = response.headers.get('location')
                            if redirect_url and attempt == 0:  # Only follow one redirect
                                logger.info(f"Following redirect from {url} to {redirect_url}")
                                return await self._fetch_with_retry(redirect_url)
                        
                        else:
                            raise aiohttp.ClientResponseError(
                                request_info=response.request_info,
                                history=response.history,
                                status=response.status,
                                message=f"HTTP {response.status}"
                            )
                            
            except Exception as e:
                last_exception = e
                logger.warning(f"Fetch attempt {attempt + 1} failed for {url}: {str(e)}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(min(2 ** attempt, 10))  # Exponential backoff with cap
                
        raise Exception(f"Failed to fetch content from {url} after {self.max_retries} attempts. Last error: {str(last_exception)}")
    
    async def _google_search(self, query: str) -> List[Dict[str, Any]]:
        """Perform Google search using Custom Search API."""
        try:
            search_url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': self.google_api_key,
                'cx': self.google_cse_id,
                'q': query,
                'num': 5,  # Get top 5 results
                'safe': 'active'  # Enable safe search
            }
            
            timeout = aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(search_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('items', [])
                    else:
                        logger.warning(f"Google Search API returned {response.status}")
                        response_text = await response.text()
                        logger.debug(f"Search API response: {response_text}")
                        return []
                        
        except Exception as e:
            logger.error(f"Google Search API failed: {str(e)}")
            return []
    
    def _extract_text_content(self, html_content: str, truncate: bool = True) -> str:
        """Extract clean text content from HTML."""
        try:
            if not html_content:
                return ""
            
            # Remove script and style elements
            html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
            html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
            
            # Remove HTML comments
            html_content = re.sub(r'<!--.*?-->', '', html_content, flags=re.DOTALL)
            
            # Remove HTML tags
            text = re.sub(r'<[^>]+>', ' ', html_content)
            
            # Decode HTML entities
            text = unescape(text)
            
            # Clean up whitespace
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'\n\s*\n', '\n', text)
            
            # Remove excessive punctuation and special characters
            text = re.sub(r'[^\w\s\.\,\!\?\-\:\;\(\)\[\]\"\'\/]', '', text)
            
            # Trim and limit length
            text = text.strip()
            
            if truncate and len(text) > 2000:
                # Find a good breaking point
                truncated = text[:2000]
                last_sentence = truncated.rfind('.')
                if last_sentence > 1500:
                    text = truncated[:last_sentence + 1]
                else:
                    text = truncated + "..."
            
            return text
            
        except Exception as e:
            logger.error(f"Text extraction failed: {str(e)}")
            # Fallback: just remove basic HTML tags
            clean_text = re.sub(r'<[^>]+>', ' ', html_content or "")
            clean_text = re.sub(r'\s+', ' ', clean_text).strip()
            return clean_text[:1000] if truncate else clean_text
    
    async def _ai_summarize_content(self, content: str, max_length: int) -> str:
        """Use LLM to summarize content."""
        if not self.azure_openai_configured or not llm_client:
            return self._fallback_summarize(content, max_length)
        
        try:
            # Extract text first
            text_content = self._extract_text_content(content)
            
            if len(text_content) < max_length:
                return text_content  # Already short enough
            
            prompt = f"""Summarize the following web content in approximately {max_length} characters. Focus on the main points and key information. Make it user-friendly and easy to read:

{text_content[:3000]}

Summary:"""

            # Call the method correctly (it's not async)
            result = llm_client.generate_text(
                prompt=prompt,
                max_tokens=min(max_length // 3, 400),  # Rough token estimate
                temperature=0.3
            )
            
            if result and isinstance(result, dict) and result.get("success") and result.get("text"):
                summary = result["text"].strip()
                return summary
            else:
                return self._fallback_summarize(text_content, max_length)
                
        except Exception as e:
            logger.warning(f"AI summarization failed: {str(e)}")
            return self._fallback_summarize(content, max_length)
    
    async def _ai_extract_key_points(self, content: str, max_length: int) -> str:
        """Use LLM to extract key points from content."""
        if not self.azure_openai_configured or not llm_client:
            return self._fallback_key_points(content, max_length)
        
        try:
            # Extract text first
            text_content = self._extract_text_content(content)
            
            prompt = f"""Extract the key points from the following web content. Format as bullet points, keeping within {max_length} characters total:

{text_content[:3000]}

Key Points:
•"""

            result = llm_client.generate_text(
                prompt=prompt,
                max_tokens=min(max_length // 3, 500),
                temperature=0.2
            )
            
            if result.get("success") and result.get("text"):
                key_points = "• " + result["text"].strip()
                return key_points
            else:
                return self._fallback_key_points(text_content, max_length)
                
        except Exception as e:
            logger.warning(f"AI key points extraction failed: {str(e)}")
            return self._fallback_key_points(content, max_length)
    
    async def _fallback_search(self, query: str, extract_type: str, max_length: int) -> Dict[str, Any]:
        """Fallback search when Google API is not available."""
        content = f"Search query: '{query}'\n\nThis is a fallback response as Google Search API is not configured. To enable real search results, please:\n1. Set up Google Custom Search Engine\n2. Configure GOOGLE_API_KEY and GOOGLE_CSE_ID in settings\n\nFor direct content access, please provide a specific URL instead."
        
        return {
            "url": f"search://{query}",
            "content": content[:max_length],
            "content_type": "text/plain",
            "ai_enhanced": False,
            "source_type": "fallback_search"
        }
    
    def _fallback_summarize(self, content: str, max_length: int) -> str:
        """Fallback summarization when LLM is not available."""
        text_content = self._extract_text_content(content)
        
        # Clean and format the text to make it user-friendly
        text_content = self._clean_and_format_text(text_content)
        
        if len(text_content) <= max_length:
            return text_content
        
        # Simple truncation at sentence boundary
        truncated = text_content[:max_length]
        last_period = truncated.rfind('.')
        if last_period > max_length * 0.7:  # If we can find a good breaking point
            return truncated[:last_period + 1]
        else:
            return truncated.rstrip() + "..."
    
    def _clean_and_format_text(self, text: str) -> str:
        """Clean and format text to make it user-friendly."""
        try:
            # Remove repetitive patterns
            text = re.sub(r'(\w+\s*-\s*\w+\s*-\s*\w+)\s*\1', r'\1', text)
            
            # Remove excessive whitespace
            text = re.sub(r'\s+', ' ', text)
            
            # Remove repetitive phrases
            text = re.sub(r'(\w+\s+\w+\s+\w+)\s*\1', r'\1', text)
            
            # Clean up patent-specific formatting
            text = re.sub(r'US\d+[A-Z]\d+\s*-\s*', '', text)  # Remove patent numbers
            text = re.sub(r'Google Patents\s*Google Patents', 'Google Patents', text)
            
            # Remove download links and technical info
            text = re.sub(r'Download PDF Info Publication number.*?Authority', 'Patent Information:', text, flags=re.DOTALL)
            
            # Clean up and format
            text = text.strip()
            text = re.sub(r'\s+', ' ', text)
            
            return text
            
        except Exception as e:
            logger.warning(f"Text cleaning failed: {str(e)}")
            return text
    
    def _fallback_key_points(self, content: str, max_length: int) -> str:
        """Fallback key points extraction when LLM is not available."""
        text_content = self._extract_text_content(content)
        
        # Simple approach: split by sentences and take first few
        sentences = [s.strip() + '.' for s in text_content.split('.') if s.strip()]
        
        key_points = []
        current_length = 0
        
        for sentence in sentences[:5]:  # Max 5 points
            point = f"• {sentence}"
            if current_length + len(point) < max_length:
                key_points.append(point)
                current_length += len(point)
            else:
                break
        
        return '\n'.join(key_points) if key_points else text_content[:max_length]
