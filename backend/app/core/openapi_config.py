"""
OpenAPI configuration for FastAPI with Bearer token authentication.
"""
from fastapi.openapi.utils import get_openapi
from fastapi import FastAPI
from fastapi.security import HTTPBearer


def custom_openapi(app: FastAPI):
    """
    Custom OpenAPI schema that includes Bearer token authentication.
    """
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Word Add-in MCP Backend",
        version="1.0.0",
        description="Backend service for Word Add-in MCP integration",
        routes=app.routes,
    )
    
    # Add Bearer token security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter your JWT Bearer token"
        }
    }
    
    # Apply security to all endpoints
    openapi_schema["security"] = [{"BearerAuth": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema
