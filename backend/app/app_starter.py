"""
Application starter that runs both backend and internal MCP server.
"""

import asyncio
import logging
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
        
        # Start both servers concurrently, but don't fail if one fails
        try:
            await asyncio.gather(
                self.start_backend(),
                self.start_internal_mcp(),
                return_exceptions=True
            )
        except Exception as e:
            logger.error(f"Error starting applications: {e}")
            # If both fail, at least try to start the backend
            try:
                await self.start_backend()
            except Exception as backend_error:
                logger.error(f"Backend also failed to start: {backend_error}")
                raise
    
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
