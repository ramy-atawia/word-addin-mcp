"""
Logging configuration for Word Add-in MCP Project.
"""

import logging
import logging.handlers
import sys
import os
from pathlib import Path
from typing import Optional

import structlog
from structlog.stdlib import LoggerFactory

from app.core.config import settings


def setup_logging() -> None:
    """Setup structured logging configuration."""
    
    # Create logs directory if it doesn't exist
    log_dir = Path(settings.LOG_FILE).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL.upper())
    )
    
    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    if settings.LOG_FORMAT == "json":
        console_formatter = logging.Formatter('%(message)s')
    else:
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with rotation
    if settings.LOG_FILE:
        file_handler = logging.handlers.RotatingFileHandler(
            settings.LOG_FILE,
            maxBytes=settings.LOG_MAX_SIZE,
            backupCount=settings.LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
        
        if settings.LOG_FORMAT == "json":
            file_formatter = logging.Formatter('%(message)s')
        else:
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    # Set specific logger levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    
    # Log configuration
    logger = structlog.get_logger()
    logger.info(
        "Logging configured",
        level=settings.LOG_LEVEL,
        format=settings.LOG_FORMAT,
        file=settings.LOG_FILE if settings.LOG_FILE else "console only"
    )


def get_logger(name: Optional[str] = None) -> structlog.BoundLogger:
    """Get a structured logger instance.
    
    Args:
        name: Logger name (optional)
    
    Returns:
        Structured logger instance
    """
    return structlog.get_logger(name)


def log_request_info(request_id: str, method: str, path: str, status_code: int, 
                    execution_time: float, user_agent: Optional[str] = None,
                    ip_address: Optional[str] = None) -> None:
    """Log HTTP request information.
    
    Args:
        request_id: Unique request identifier
        method: HTTP method
        path: Request path
        status_code: HTTP status code
        execution_time: Request execution time in seconds
        user_agent: User agent string
        ip_address: Client IP address
    """
    logger = get_logger("http_request")
    
    log_data = {
        "request_id": request_id,
        "method": method,
        "path": path,
        "status_code": status_code,
        "execution_time": execution_time,
        "user_agent": user_agent,
        "ip_address": ip_address
    }
    
    if status_code >= 400:
        logger.warning("HTTP request completed with error", **log_data)
    else:
        logger.info("HTTP request completed successfully", **log_data)





def log_security_event(event_type: str, user_id: Optional[str] = None,
                      session_id: Optional[str] = None, ip_address: Optional[str] = None,
                      details: Optional[str] = None) -> None:
    """Log security-related events.
    
    Args:
        event_type: Type of security event
        user_id: User identifier (if applicable)
        session_id: Session identifier (if applicable)
        ip_address: IP address (if applicable)
        details: Additional event details
    """
    logger = get_logger("security")
    
    log_data = {
        "event_type": event_type,
        "user_id": user_id,
        "session_id": session_id,
        "ip_address": ip_address,
        "details": details
    }
    
    logger.warning("Security event detected", **log_data)





def log_error(error: Exception, context: Optional[dict] = None,
              request_id: Optional[str] = None, session_id: Optional[str] = None) -> None:
    """Log error information with context.
    
    Args:
        error: Exception that occurred
        context: Additional error context
        request_id: Request identifier (if applicable)
        session_id: Session identifier (if applicable)
    """
    logger = get_logger("error")
    
    log_data = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "request_id": request_id,
        "session_id": session_id,
        "context": context or {}
    }
    
    logger.error("Error occurred", **log_data, exc_info=True)






