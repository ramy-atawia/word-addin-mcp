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
    azure_openai_deployment: Optional[str] = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME") or os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
    azure_openai_api_version: Optional[str] = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    
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
    
    
    # Security Configuration
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    refresh_token_expire_days: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    password_min_length: int = int(os.getenv("PASSWORD_MIN_LENGTH", "8"))
    password_require_special: bool = os.getenv("PASSWORD_REQUIRE_SPECIAL", "true").lower() == "true"
    password_require_numbers: bool = os.getenv("PASSWORD_REQUIRE_NUMBERS", "true").lower() == "true"
    max_login_attempts: int = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
    lockout_duration_minutes: int = int(os.getenv("LOCKOUT_DURATION_MINUTES", "15"))
    
    # Database Configuration
    database_url: Optional[str] = os.getenv("DATABASE_URL")
    
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
    auth0_client_id: str = os.getenv("AUTH0_CLIENT_ID", "")
    auth0_client_secret: str = os.getenv("AUTH0_CLIENT_SECRET", "")
    auth0_audience: str = os.getenv("AUTH0_AUDIENCE", "https://word-addin-backend.azurewebsites.net")
    
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


