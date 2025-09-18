# Multi-stage build for Python backend with MCP functionality
FROM python:3.12-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for cryptography
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# Development stage
FROM python:3.12-slim as development

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install runtime dependencies and dev tools
RUN apt-get update && apt-get install -y \
    curl \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Create app directory
WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Create necessary directories
RUN mkdir -p logs uploads && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${FASTAPI_PORT:-9000}/health || exit 1

# Expose port
EXPOSE 9000

# Default command with reload for development
CMD ["sh", "-c", "python -m uvicorn app.main:app --host 0.0.0.0 --port 9000"]

# Production stage
FROM python:3.12-slim as production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Create app directory
WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Copy application code (excluding .env files)
COPY . .
RUN rm -f .env.local .env

# Create necessary directories
RUN mkdir -p logs uploads && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${FASTAPI_PORT:-9000}/health || exit 1

# Expose port
EXPOSE 9000

# Default command - use app starter for both backend and internal MCP
# Set APP_STARTER_MODE=true as fallback if not set in environment
CMD ["sh", "-c", "export APP_STARTER_MODE=${APP_STARTER_MODE:-true} && python -m app.app_starter"]
