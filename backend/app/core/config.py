"""
Configuration settings for the Word Add-in MCP project.
"""

import os
import json
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import field_validator
from dotenv import load_dotenv
import pathlib

# Load .env file explicitly
env_file = pathlib.Path(__file__).parent.parent.parent / ".env"
if env_file.exists():
    load_dotenv(env_file)
else:
    # Try alternative location
    alt_env = pathlib.Path(__file__).parent.parent.parent.parent / ".env"
    if alt_env.exists():
        load_dotenv(alt_env)


class Settings(BaseSettings):
    """Application settings."""
    
    # Azure OpenAI Configuration
    azure_openai_api_key: Optional[str] = os.getenv("AZURE_OPENAI_API_KEY")
    azure_openai_endpoint: Optional[str] = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_openai_deployment: Optional[str] = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME") or os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-5-nano")
    azure_openai_api_version: Optional[str] = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
    
    # Google Search API Configuration
    google_search_api_key: Optional[str] = os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_SEARCH_API_KEY")
    google_search_engine_id: Optional[str] = os.getenv("GOOGLE_CSE_ID") or os.getenv("GOOGLE_SEARCH_ENGINE_ID")
    
    # arXiv API Configuration
    arxiv_user_agent: str = os.getenv("ARXIV_USER_AGENT", "WordAddinMCP/1.0")
    
    # File Processing Limits
    max_file_size: int = int(os.getenv("MAX_FILE_SIZE", "104857600"))  # 100MB
    max_pages: int = int(os.getenv("MAX_PAGES", "500"))
    
    # API Rate Limiting
    max_requests_per_minute: int = int(os.getenv("MAX_REQUESTS_PER_MINUTE", "60"))
    max_requests_per_hour: int = int(os.getenv("MAX_REQUESTS_PER_HOUR", "1000"))
    
    # LangGraph Configuration - Phase 1
    use_langgraph: bool = os.getenv("USE_LANGGRAPH", "false").lower() == "true"
    
    # Rate limit aliases for middleware
    @property
    def RATE_LIMIT_PER_MINUTE(self) -> int:
        return self.max_requests_per_minute
    
    @property
    def RATE_LIMIT_PER_HOUR(self) -> int:
        return self.max_requests_per_hour
    
    # Logging Configuration
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_file: str = os.getenv("LOG_FILE", "logs/app.log")
    log_format: str = os.getenv("LOG_FORMAT", "text")
    log_max_size: int = int(os.getenv("LOG_MAX_SIZE", "10485760"))  # 10MB
    log_backup_count: int = int(os.getenv("LOG_BACKUP_COUNT", "5"))
    
    
    
    # CORS Configuration
    allowed_origins: List[str] = ["*"]  # Allow all origins for development
    allowed_methods: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allowed_headers: List[str] = ["*"]
    
    @field_validator('allowed_origins', 'allowed_methods', 'allowed_headers', mode='before')
    @classmethod
    def parse_list_fields(cls, v):
        """Parse JSON string environment variables to lists."""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                # If it's not JSON, split by comma
                return [item.strip() for item in v.split(',')]
        return v
    
    # Langfuse Configuration (optional)
    langfuse_secret_key: Optional[str] = os.getenv("LANGFUSE_SECRET_KEY")
    langfuse_public_key: Optional[str] = os.getenv("LANGFUSE_PUBLIC_KEY")
    langfuse_host: Optional[str] = os.getenv("LANGFUSE_HOST")
    
    # PatentsView API Configuration (optional)
    patentsview_api_key: Optional[str] = os.getenv("PATENTSVIEW_API_KEY")
    
    # FastAPI Configuration
    enable_swagger: bool = os.getenv("ENABLE_SWAGGER", "true").lower() == "true"
    fastapi_host: str = os.getenv("FASTAPI_HOST", "0.0.0.0")
    fastapi_port: int = int(os.getenv("FASTAPI_PORT", "9000"))
    fastapi_reload: bool = os.getenv("FASTAPI_RELOAD", "true").lower() == "true"
    fastapi_log_level: str = os.getenv("FASTAPI_LOG_LEVEL", "INFO")
    
    
    # MCP Configuration
    mcp_server_url: str = os.getenv("MCP_SERVER_URL", "https://localhost:9000")
    
    # Internal MCP Server Configuration
    internal_mcp_host: str = os.getenv("INTERNAL_MCP_HOST", "localhost")
    internal_mcp_port: int = int(os.getenv("INTERNAL_MCP_PORT", "8001"))
    internal_mcp_path: str = os.getenv("INTERNAL_MCP_PATH", "/mcp")
    expose_mcp_publicly: bool = os.getenv("EXPOSE_MCP_PUBLICLY", "false").lower() == "true"
    mcp_public_url: str = os.getenv("MCP_PUBLIC_URL", "https://mcp-tools.yourdomain.com/mcp")
    
    @property
    def internal_mcp_url(self) -> str:
        """Get internal MCP server URL based on environment."""
        if self.expose_mcp_publicly:
            return self.mcp_public_url
        elif self.environment == "docker":
            return f"http://internal-mcp:{self.internal_mcp_port}{self.internal_mcp_path}"
        else:
            return f"http://{self.internal_mcp_host}:{self.internal_mcp_port}{self.internal_mcp_path}"
    
    # Application Configuration
    app_version: str = os.getenv("APP_VERSION", "1.0.0")
    environment: str = os.getenv("ENVIRONMENT", "development")
    
    # Debug Configuration
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # Host Configuration
    allowed_hosts: list = ["localhost", "127.0.0.1", "0.0.0.0", "*.azurewebsites.net"]
    
    # Frontend Configuration
    frontend_url: str = os.getenv("FRONTEND_URL", "https://localhost:3000")
    frontend_base_url: str = os.getenv("FRONTEND_BASE_URL", "https://localhost:3000")
    
    # Auth0 Configuration
    auth0_domain: str = os.getenv("AUTH0_DOMAIN", "dev-bktskx5kbc655wcl.us.auth0.com")
    auth0_audience: str = os.getenv("AUTH0_AUDIENCE", "INws849yDXaC6MZVXnLhMJi6CZC4nx6U")
    auth0_enabled: bool = os.getenv("AUTH0_ENABLED", "true").lower() == "true"
    
    # Auth0 Excluded Paths (paths that don't require authentication)
    auth0_excluded_paths: List[str] = [
        "/health",
        "/",
        "/docs",
        "/redoc", 
        "/openapi.json",
        "/api/v1/health",
        "/api/v1/health/live",
        "/api/v1/health/ready",
        "/api/v1/health/detailed",
        "/api/v1/health/debug/config",
        "/api/v1/health/metrics",
        "/api/v1/mcp/agent/chat/stream",  # Temporarily allow streaming without auth for testing
        "/api/v1/async/chat/submit",      # Allow async chat submission
        "/api/v1/async/chat/status",      # Allow async chat status checks
        "/api/v1/async/chat/result",      # Allow async chat result retrieval
        "/api/v1/async/chat/cancel",      # Allow async chat cancellation
        "/api/v1/async/chat/jobs",        # Allow async chat job listing
        "/api/v1/async/chat/stats",       # Allow async chat statistics
        "/api/v1/mcp/tools"               # Temporarily allow MCP tools without auth for testing
    ]

# API Configuration
api_base_url: str = os.getenv("API_BASE_URL", "http://localhost:9000")
api_docs_url: str = os.getenv("API_DOCS_URL", "http://localhost:9000/docs")

class Config:
    env_file = [".env", "../.env", "/Users/Mariam/word-addin-mcp/.env"]
    case_sensitive = False
    extra = "allow"  # Allow extra fields from .env


# Global settings instance
settings = Settings()


def is_azure_openai_configured() -> bool:
    """Check if Azure OpenAI is properly configured."""
    return (
        settings.azure_openai_api_key is not None and
        settings.azure_openai_endpoint is not None and
        settings.azure_openai_deployment is not None
    )


def get_azure_openai_config() -> dict:
    """Get Azure OpenAI configuration."""
    return {
        'api_key': settings.azure_openai_api_key,
        'endpoint': settings.azure_openai_endpoint,
        'deployment': settings.azure_openai_deployment,
        'api_version': settings.azure_openai_api_version
    }


