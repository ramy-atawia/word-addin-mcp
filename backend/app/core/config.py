"""
Configuration settings for the Word Add-in MCP project.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Azure OpenAI Configuration
    azure_openai_api_key: Optional[str] = os.getenv("AZURE_OPENAI_API_KEY")
    azure_openai_endpoint: Optional[str] = os.getenv("AZURE_OPENAI_ENDPOINT")
    azure_openai_deployment: Optional[str] = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME") or os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
    azure_openai_deployment_name: Optional[str] = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME") or os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
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
    
    # Logging Configuration
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")  # Alias for compatibility
    log_file: str = os.getenv("LOG_FILE", "logs/app.log")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/app.log")  # Alias for compatibility
    log_format: str = os.getenv("LOG_FORMAT", "text")
    LOG_FORMAT: str = os.getenv("LOG_FORMAT", "text")  # Alias for compatibility
    log_max_size: int = int(os.getenv("LOG_MAX_SIZE", "10485760"))  # 10MB
    LOG_MAX_SIZE: int = int(os.getenv("LOG_MAX_SIZE", "10485760"))  # Alias for compatibility
    log_backup_count: int = int(os.getenv("LOG_BACKUP_COUNT", "5"))
    LOG_BACKUP_COUNT: int = int(os.getenv("LOG_BACKUP_COUNT", "5"))  # Alias for compatibility
    
    # Security Configuration
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")  # Alias for compatibility
    algorithm: str = "HS256"
    JWT_ALGORITHM: str = "HS256"  # Alias for compatibility
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))  # Alias for compatibility
    refresh_token_expire_days: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))  # Alias for compatibility
    password_min_length: int = int(os.getenv("PASSWORD_MIN_LENGTH", "8"))
    PASSWORD_MIN_LENGTH: int = int(os.getenv("PASSWORD_MIN_LENGTH", "8"))  # Alias for compatibility
    password_require_special: bool = os.getenv("PASSWORD_REQUIRE_SPECIAL", "true").lower() == "true"
    PASSWORD_REQUIRE_SPECIAL: bool = os.getenv("PASSWORD_REQUIRE_SPECIAL", "true").lower() == "true"  # Alias for compatibility
    password_require_numbers: bool = os.getenv("PASSWORD_REQUIRE_NUMBERS", "true").lower() == "true"
    PASSWORD_REQUIRE_NUMBERS: bool = os.getenv("PASSWORD_REQUIRE_NUMBERS", "true").lower() == "true"  # Alias for compatibility
    max_login_attempts: int = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
    MAX_LOGIN_ATTEMPTS: int = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))  # Alias for compatibility
    lockout_duration_minutes: int = int(os.getenv("LOCKOUT_DURATION_MINUTES", "15"))
    LOCKOUT_DURATION_MINUTES: int = int(os.getenv("LOCKOUT_DURATION_MINUTES", "15"))  # Alias for compatibility
    
    # Database Configuration
    database_url: Optional[str] = os.getenv("DATABASE_URL")
    
    # CORS Configuration
    allowed_origins: list = ["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "https://localhost:3000", "https://localhost:3001", "https://localhost:3002"]
    allowed_methods: list = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allowed_headers: list = ["*"]
    
    # Langfuse Configuration (optional)
    langfuse_secret_key: Optional[str] = os.getenv("LANGFUSE_SECRET_KEY")
    langfuse_public_key: Optional[str] = os.getenv("LANGFUSE_PUBLIC_KEY")
    langfuse_host: Optional[str] = os.getenv("LANGFUSE_HOST")
    
    # PatentsView API Configuration (optional)
    patentsview_api_key: Optional[str] = os.getenv("PATENTSVIEW_API_KEY")
    
    # FastAPI Configuration
    enable_swagger: bool = os.getenv("ENABLE_SWAGGER", "true").lower() == "true"
    ENABLE_SWAGGER: bool = os.getenv("ENABLE_SWAGGER", "true").lower() == "true"  # Alias for compatibility
    fastapi_host: str = os.getenv("FASTAPI_HOST", "0.0.0.0")
    FASTAPI_HOST: str = os.getenv("FASTAPI_HOST", "0.0.0.0")  # Alias for compatibility
    fastapi_port: int = int(os.getenv("FASTAPI_PORT", "9000"))
    FASTAPI_PORT: int = int(os.getenv("FASTAPI_PORT", "9000"))  # Alias for compatibility
    fastapi_reload: bool = os.getenv("FASTAPI_RELOAD", "true").lower() == "true"
    FASTAPI_RELOAD: bool = os.getenv("FASTAPI_RELOAD", "true").lower() == "true"  # Alias for compatibility
    fastapi_log_level: str = os.getenv("FASTAPI_LOG_LEVEL", "INFO")
    FASTAPI_LOG_LEVEL: str = os.getenv("FASTAPI_LOG_LEVEL", "INFO")  # Alias for compatibility
    
    # MCP Configuration
    mcp_server_url: str = os.getenv("MCP_SERVER_URL", "http://localhost:9000")
    MCP_SERVER_URL: str = os.getenv("MCP_SERVER_URL", "http://localhost:9000")  # Alias for compatibility
    
    # Application Configuration
    app_version: str = os.getenv("APP_VERSION", "1.0.0")
    APP_VERSION: str = os.getenv("APP_VERSION", "1.0.0")  # Alias for compatibility
    environment: str = os.getenv("ENVIRONMENT", "development")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")  # Alias for compatibility
    
    class Config:
        env_file = "/Users/Mariam/word-addin-mcp/.env"
        case_sensitive = False
        extra = "allow"  # Allow extra fields from .env


# Global settings instance
settings = Settings()


def get_azure_openai_config() -> dict:
    """Get Azure OpenAI configuration."""
    return {
        "api_key": settings.azure_openai_api_key,
        "endpoint": settings.azure_openai_endpoint,
        "deployment": settings.azure_openai_deployment
    }


def get_google_search_config() -> dict:
    """Get Google Search API configuration."""
    return {
        "api_key": settings.google_search_api_key,
        "engine_id": settings.google_search_engine_id
    }


def is_azure_openai_configured() -> bool:
    """Check if Azure OpenAI is properly configured."""
    return bool(
        settings.azure_openai_api_key and 
        settings.azure_openai_endpoint
    )


def is_google_search_configured() -> bool:
    """Check if Google Search API is properly configured."""
    return bool(
        settings.google_search_api_key and 
        settings.google_search_engine_id
    )
