"""
Simplified Web Content Fetcher Service

Basic web search and content extraction using Google Search API and BeautifulSoup.
Removed Selenium integration and complex features for simplicity.
"""

import os
import json
import logging
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime
from urllib.parse import urlparse, quote_plus
import time

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class WebContentFetcherService:
    """Simplified web content fetcher with Google Search API and basic scraping."""
    
    def __init__(self, google_api_key: Optional[str] = None, 
                 google_engine_id: Optional[str] = None):
        """
        Initialize the web content fetcher service.
        
        Args:
            google_api_key: Google Custom Search API key
            google_engine_id: Google Custom Search Engine ID
        """
        self.google_api_key = google_api_key
        self.google_engine_id = google_engine_id
        
        # API endpoints
        self.google_search_url = "https://www.googleapis.com/customsearch/v1"
        
        # Rate limiting (basic)
        self.last_google_request = None
        self.min_request_interval = 1.0  # seconds between requests
    
    def search_web(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """
        Search the web using Google Custom Search API.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            Dictionary with search results
        """
        try:
            if not self.google_api_key or not self.google_engine_id:
                return {
                    "success": False,
                    "error": "Google Search API not configured",
                    "results": []
                }
            
            # Rate limiting
            if self.last_google_request:
                time_since_last = time.time() - self.last_google_request
                if time_since_last < self.min_request_interval:
                    time.sleep(self.min_request_interval - time_since_last)
            
            # Prepare search parameters
            params = {
                "key": self.google_api_key,
                "cx": self.google_engine_id,
                "q": query,
                "num": min(max_results, 10)  # Google CSE max is 10
            }
            
            # Make request
            response = requests.get(self.google_search_url, params=params, timeout=30)
            self.last_google_request = time.time()
            
            if response.status_code == 200:
                data = response.json()
                results = self._parse_google_results(data)
                
                return {
                    "success": True,
                    "query": query,
                    "results": results,
                    "total_results": len(results),
                    "search_time": datetime.utcnow().isoformat()
                }
            else:
                return {
                    "success": False,
                    "error": f"Google API returned status {response.status_code}",
                    "results": []
                }
                
        except Exception as e:
            logger.error(f"Web search failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "results": []
            }
    
    def fetch_url_content(self, url: str, max_length: int = 5000) -> Dict[str, Any]:
        """
        Fetch and extract content from a URL.
        
        Args:
            url: URL to fetch
            max_length: Maximum content length
            
        Returns:
            Dictionary with extracted content
        """
        try:
            # Validate URL
            if not self._is_valid_url(url):
                return {
                    "success": False,
                    "error": "Invalid URL",
                    "url": url
                }
            
            # Fetch content
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "url": url
                }
            
            # Extract text content
            content_type = response.headers.get("content-type", "")
            
            if "text/html" in content_type:
                content = self._extract_html_content(response.text, max_length)
            elif "text/plain" in content_type:
                content = response.text[:max_length]
            else:
                return {
                    "success": False,
                    "error": f"Unsupported content type: {content_type}",
                    "url": url
                }
            
            return {
                "success": True,
                "url": url,
                "content": content,
                "content_type": content_type,
                "content_length": len(content),
                "fetch_time": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch URL {url}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "url": url
            }
    
    def _parse_google_results(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse Google Custom Search API results."""
        try:
            results = []
            items = data.get("items", [])
            
            for item in items:
                result = {
                    "title": item.get("title", ""),
                    "link": item.get("link", ""),
                    "snippet": item.get("snippet", ""),
                    "display_link": item.get("displayLink", ""),
                    "image": item.get("pagemap", {}).get("cse_image", [{}])[0].get("src", ""),
                    "type": "web_search"
                }
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to parse Google results: {str(e)}")
            return []
    
    def _extract_html_content(self, html: str, max_length: int) -> str:
        """Extract text content from HTML."""
        try:
            soup = BeautifulSoup(html, "html.parser")
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Extract text
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = " ".join(chunk for chunk in chunks if chunk)
            
            # Truncate if too long
            if len(text) > max_length:
                text = text[:max_length] + "..."
            
            return text
            
        except Exception as e:
            logger.error(f"Failed to extract HTML content: {str(e)}")
            return "Content extraction failed"
    
    def _is_valid_url(self, url: str) -> bool:
        """Basic URL validation."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get service status and configuration."""
        return {
            "service": "WebContentFetcherService",
            "google_api_configured": bool(self.google_api_key and self.google_engine_id),
            "google_api_key_length": len(self.google_api_key) if self.google_api_key else 0,
            "google_engine_id_length": len(self.google_engine_id) if self.google_engine_id else 0,
            "last_request_time": self.last_google_request,
            "status": "active"
        }
