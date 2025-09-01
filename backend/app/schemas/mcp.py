"""
MCP-related Pydantic schemas for API requests and responses.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel


class ExternalServerRequest(BaseModel):
    """Request model for adding external MCP servers."""
    name: str
    description: str
    server_url: str
    server_type: str
    authentication_type: str = "NONE"
    api_key: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    
    def to_backend_config(self) -> Dict[str, Any]:
        """Convert frontend payload to backend expected format."""
        return {
            "name": self.name,
            "url": self.server_url,
            "type": "external",  # Always external for this endpoint
            "description": self.description,
            "metadata": {
                "frontend_type": self.server_type,
                "authentication_type": self.authentication_type,
                "api_key": self.api_key,
                "username": self.username,
                "password": self.password
            }
        }
