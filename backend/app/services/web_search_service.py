"""
Real Web Search Service

Integrates with actual web APIs for Google Search, arXiv, and academic databases.
Provides real search results instead of placeholder content.
"""

import asyncio
import aiohttp
import json
import re
from typing import List, Dict, Optional, Any
from urllib.parse import quote_plus, urlparse
import logging
import os

logger = logging.getLogger(__name__)


class WebSearchService:
    """Real web search service with multiple search engines."""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Mozilla/5.0 (X11; Linux x64) AppleWebKit/537.36"
        ]
        
        # Get API credentials from settings (loads from .env file)
        from app.core.config import settings
        self.google_api_key = settings.google_search_api_key
        self.google_engine_id = settings.google_search_engine_id
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={"User-Agent": self.user_agents[0]}
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def search_google(self, query: str, max_results: int = 10, 
                           include_abstracts: bool = False) -> List[Dict[str, Any]]:
        """Perform real Google search using Google Custom Search API."""
        try:
            if not self.google_api_key or not self.google_engine_id:
                logger.warning("Google Search API not configured")
                return []
            
            # Google Custom Search API endpoint
            api_url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "key": self.google_api_key,
                "cx": self.google_engine_id,
                "q": query,
                "num": min(max_results, 10)  # Google CSE max is 10
            }
            
            if not self.session:
                return []
            
            async with self.session.get(api_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    results = self._parse_google_results(data, include_abstracts)
                    logger.info(f"Google search completed for query: {query}, found {len(results)} results")
                    return results
                else:
                    logger.warning(f"Google API returned status {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Google search failed for query '{query}': {str(e)}")
            return []
    
    async def search_arxiv(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search arXiv for academic papers."""
        try:
            # arXiv API endpoint
            arxiv_url = "http://export.arxiv.org/api/query"
            params = {
                "search_query": query,
                "start": 0,
                "max_results": max_results,
                "sortBy": "relevance",
                "sortOrder": "descending"
            }
            
            if not self.session:
                return []
                
            async with self.session.get(arxiv_url, params=params) as response:
                if response.status == 200:
                    content = await response.text()
                    return self._parse_arxiv_results(content, max_results)
                else:
                    logger.warning(f"arXiv API returned status {response.status}")
                    return []
        except Exception as e:
            logger.error(f"arXiv search failed for query '{query}': {str(e)}")
            return []
    
    async def search_academic_databases(self, query: str, max_results: int = 10,
                                      databases: List[str] = None) -> List[Dict[str, Any]]:
        """Search multiple academic databases."""
        if databases is None:
            databases = ["arxiv", "ieee", "acm"]
        
        all_results = []
        
        for db in databases:
            try:
                if db == "arxiv":
                    results = await self.search_arxiv(query, max_results // len(databases))
                elif db == "ieee":
                    results = await self._search_ieee(query, max_results // len(databases))
                elif db == "acm":
                    results = await self._search_acm(query, max_results // len(databases))
                else:
                    continue
                    
                all_results.extend(results)
            except Exception as e:
                logger.error(f"Search in {db} failed: {str(e)}")
                continue
        
        # Sort by relevance and limit results
        return sorted(all_results, key=lambda x: x.get("relevance", 0), reverse=True)[:max_results]
    
    async def fetch_web_content(self, url: str, max_content_length: int = 50000) -> Dict[str, Any]:
        """Fetch actual web content from a URL."""
        try:
            if not self.session:
                return self._create_error_result("Session not initialized")
            
            headers = {
                "User-Agent": self.user_agents[0],
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
            }
            
            async with self.session.get(url, headers=headers, timeout=30) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    # Extract text content (basic HTML parsing)
                    text_content = self._extract_text_from_html(content)
                    
                    # Truncate if too long
                    if len(text_content) > max_content_length:
                        text_content = text_content[:max_content_length] + "..."
                    
                    return {
                        "url": url,
                        "content": text_content,
                        "content_type": "text/html",
                        "extraction_time": 0.0,
                        "status": "success",
                        "content_length": len(text_content)
                    }
                else:
                    return self._create_error_result(f"HTTP {response.status}")
                    
        except asyncio.TimeoutError:
            return self._create_error_result("Request timeout")
        except Exception as e:
            logger.error(f"Failed to fetch content from {url}: {str(e)}")
            return self._create_error_result(f"Fetch error: {str(e)}")
    
    def _parse_google_results(self, data: Dict[str, Any], include_abstracts: bool) -> List[Dict[str, Any]]:
        """Parse Google Custom Search API results."""
        try:
            results = []
            items = data.get("items", [])
            
            for item in items:
                result = {
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "source": "Google Search",
                    "type": "web_page",
                    "relevance": 0.8  # Default relevance score
                }
                
                # Add additional metadata if available
                if "pagemap" in item:
                    pagemap = item["pagemap"]
                    if "metatags" in pagemap:
                        metatags = pagemap["metatags"][0]
                        result["description"] = metatags.get("og:description", "")
                        result["image"] = metatags.get("og:image", "")
                    
                    if "cse_image" in pagemap:
                        result["thumbnail"] = pagemap["cse_image"][0].get("src", "")
                
                # Include abstract if requested and available
                if include_abstracts and result["snippet"]:
                    result["abstract"] = result["snippet"]
                
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to parse Google results: {str(e)}")
            return []
    
    def _parse_arxiv_results(self, xml_content: str, max_results: int) -> List[Dict[str, Any]]:
        """Parse arXiv XML results."""
        try:
            results = []
            # Simple XML parsing using regex (in production, use proper XML parser)
            entries = re.findall(r'<entry>(.*?)</entry>', xml_content, re.DOTALL)
            
            for entry in entries[:max_results]:
                title_match = re.search(r'<title>(.*?)</title>', entry)
                id_match = re.search(r'<id>(.*?)</id>', entry)
                summary_match = re.search(r'<summary>(.*?)</summary>', entry)
                published_match = re.search(r'<published>(.*?)</published>', entry)
                
                if title_match and id_match:
                    result = {
                        "title": title_match.group(1).strip(),
                        "link": id_match.group(1).strip(),
                        "snippet": summary_match.group(1).strip() if summary_match else "",
                        "source": "arXiv",
                        "type": "academic_paper",
                        "published_date": published_match.group(1).strip() if published_match else "",
                        "relevance": 0.9  # Academic papers get high relevance
                    }
                    results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to parse arXiv results: {str(e)}")
            return []
    
    async def _search_ieee(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Search IEEE Xplore (placeholder for future implementation)."""
        logger.info(f"IEEE search not yet implemented for query: {query}")
        return []
    
    async def _search_acm(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Search ACM Digital Library (placeholder for future implementation)."""
        logger.info(f"ACM search not yet implemented for query: {query}")
        return []
    
    def _extract_text_from_html(self, html: str) -> str:
        """Extract clean text content from HTML."""
        try:
            # Remove HTML tags
            text = re.sub(r'<[^>]+>', ' ', html)
            # Remove extra whitespace
            text = re.sub(r'\s+', ' ', text)
            # Decode HTML entities
            text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
            return text.strip()
        except Exception as e:
            logger.error(f"Failed to extract text from HTML: {str(e)}")
            return html[:1000] + "..."  # Fallback to truncated HTML
    
    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """Create standardized error result."""
        return {
            "url": "",
            "content": "",
            "content_type": "error",
            "extraction_time": 0.0,
            "status": "error",
            "error_message": error_message
        }
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get service status and configuration."""
        return {
            "service": "WebSearchService",
            "google_api_configured": bool(self.google_api_key and self.google_engine_id),
            "google_api_key_length": len(self.google_api_key) if self.google_api_key else 0,
            "google_engine_id_length": len(self.google_engine_id) if self.google_engine_id else 0,
            "session_active": self.session is not None,
            "status": "active"
        }


# Global instance for easy access
web_search_service = WebSearchService()
