"""
Application starter that runs both backend and internal MCP server.
"""

import asyncio
import logging
import os
import signal
import sys
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from .main import app as backend_app
from .internal_mcp_app import app as internal_mcp_app

logger = logging.getLogger(__name__)

class AppStarter:
    """Starter class for running both applications."""
    
    def __init__(self):
        self.backend_server = None
        self.internal_mcp_server = None
        self.shutdown_event = asyncio.Event()
    
    async def start_backend(self):
        """Start the backend application."""
        config = uvicorn.Config(
            backend_app,
            host="0.0.0.0",
            port=9000,
            log_level="info"
        )
        self.backend_server = uvicorn.Server(config)
        await self.backend_server.serve()
    
    async def start_internal_mcp(self):
        """Start the internal MCP server."""
        # Check if we're in Azure App Service (production)
        if os.getenv("ENVIRONMENT") == "production":
            # In Azure App Service, we can't use a separate port
            # Instead, we'll mount the internal MCP app on the backend app
            logger.info("Production mode: Mounting internal MCP server on backend app")
            return
        else:
            # In development/docker, use separate port
            config = uvicorn.Config(
                internal_mcp_app,
                host="0.0.0.0",
                port=8001,
                log_level="info"
            )
            self.internal_mcp_server = uvicorn.Server(config)
            await self.internal_mcp_server.serve()
    
    async def start_both(self):
        """Start both applications concurrently."""
        logger.info("Starting both applications...")
        
        # Debug environment variables
        app_starter_mode = os.getenv("APP_STARTER_MODE", "false")
        environment = os.getenv("ENVIRONMENT", "development")
        internal_mcp_fail_open = os.getenv("INTERNAL_MCP_FAIL_OPEN", "false")
        
        logger.info(f"Environment variables - APP_STARTER_MODE: {app_starter_mode}, ENVIRONMENT: {environment}, INTERNAL_MCP_FAIL_OPEN: {internal_mcp_fail_open}")
        
        # Check if we're in production and should fail-open
        if environment == "production" and internal_mcp_fail_open.lower() == "true":
            logger.warning("Production mode: Starting backend only (internal MCP fail-open)")
            await self.start_backend()
        elif app_starter_mode.lower() == "true":
            # APP_STARTER_MODE: Start both servers concurrently
            logger.info("APP_STARTER_MODE enabled: Starting both backend and internal MCP server")
            await asyncio.gather(
                self.start_backend(),
                self.start_internal_mcp()
            )
        else:
            # Default: Start both servers concurrently
            logger.info("Default mode: Starting both backend and internal MCP server")
            await asyncio.gather(
                self.start_backend(),
                self.start_internal_mcp()
            )
    
    async def shutdown(self):
        """Shutdown both applications."""
        logger.info("Shutting down applications...")
        
        if self.backend_server:
            self.backend_server.should_exit = True
        if self.internal_mcp_server:
            self.internal_mcp_server.should_exit = True
        
        self.shutdown_event.set()

def setup_signal_handlers(starter: AppStarter):
    """Setup signal handlers for graceful shutdown."""
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}, initiating shutdown...")
        asyncio.create_task(starter.shutdown())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

async def main():
    """Main entry point."""
    starter = AppStarter()
    setup_signal_handlers(starter)
    
    try:
        await starter.start_both()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)
    finally:
        await starter.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
